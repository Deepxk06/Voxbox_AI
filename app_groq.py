"""VoxBox AI — production-grade ChatGPT-style coding assistant.

Flask application wiring the voxbox backend package (providers, router,
context, classifier, search, security) to the HTTP API and the frontend.

Routes:
    GET  /                    -> frontend
    GET  /api/models          -> providers/models/defaults
    GET  /api/health          -> health + provider states
    POST /api/chat            -> non-streaming chat
    POST /api/chat/stream     -> SSE streaming chat
    POST /api/title           -> conversation title
    GET  /api/memory          -> list memories
    DELETE /api/memory/<id>   -> delete a memory
    POST /api/memory/clear    -> clear all memories
"""
import json
import os
import time

from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
from flask_cors import CORS

from voxbox import config
from voxbox.classifier import classify, needs_web_search
from voxbox.context import build_context, memory_store, extract_memories, summarize
from voxbox.logging import log_event, log_error
from voxbox.providers import router
from voxbox.search import search, format_results
from voxbox.security import (
    validate_chat_payload,
    rate_limit_ok,
    safe_error_message,
    looks_like_injection,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

_cors_origins = [o for o in config.CORS_ORIGIN_LIST if o != "*"]
if config.CORS_ORIGIN_LIST and "*" in config.CORS_ORIGIN_LIST:
    CORS(app, resources={r"/api/*": {"origins": "*"}})
elif _cors_origins:
    CORS(app, resources={r"/api/*": {"origins": _cors_origins}})
else:
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5000"}})


def check_auth():
    if not config.VOXBOX_API_TOKEN:
        return None
    if request.headers.get("X-VoxBox-Token", "") != config.VOXBOX_API_TOKEN:
        return jsonify({"error": "Unauthorized. Set the X-VoxBox-Token header."}), 401
    return None


def _client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()


# ---------------------------------------------------------------- frontend
def _frontend_html() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend.html")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return "<!DOCTYPE html><html><body><h1>VoxBox</h1><p>frontend.html missing.</p></body></html>"


_FRONTEND_CACHE = None


@app.route("/")
def index():
    global _FRONTEND_CACHE
    if _FRONTEND_CACHE is None:
        _FRONTEND_CACHE = _frontend_html()
    return Response(_FRONTEND_CACHE, mimetype="text/html")


# ---------------------------------------------------------------- models
@app.route("/api/models", methods=["GET"])
def models_endpoint():
    auth_error = check_auth()
    if auth_error:
        return auth_error
    selected = router.default_provider_id()
    return jsonify({
        "providers": router.enabled_providers(),
        "default_provider": selected,
        "default_model": router.default_model_for(selected) if selected else None,
        "auth_required": bool(config.VOXBOX_API_TOKEN),
        "memory_enabled": memory_store.enabled(),
        "web_search_enabled": config.ENABLE_WEB_SEARCH,
    })


# ---------------------------------------------------------------- health
@app.route("/api/health", methods=["GET"])
def health():
    states = router.provider_states()
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "providers": {pid: s["status"] for pid, s in states.items()},
    })


# ---------------------------------------------------------------- chat
@app.route("/api/chat", methods=["POST"])
def chat():
    auth_error = check_auth()
    if auth_error:
        return auth_error
    if not rate_limit_ok(_client_ip()):
        return jsonify({"error": "Rate limit exceeded. Try again shortly."}), 429

    try:
        data = request.json or {}
        payload, err = validate_chat_payload(data, router)
        if err:
            return err
        request_id = _client_ip()[:8] + "-" + str(int(time.time() * 1000))[-6:]
        contents = payload["contents"]
        last_text = contents[-1]["content"]

        for mem in extract_memories(last_text):
            memory_store.add(mem)

        start = time.time()
        category = classify(last_text)
        search_text = ""
        if needs_web_search(category, last_text) and config.ENABLE_WEB_SEARCH:
            results = search(last_text)
            search_text = format_results(results)

        summary, trimmed = summarize(contents, router, request_id=request_id)
        messages = build_context(trimmed, memory_store, search_text)
        if summary:
            from voxbox import prompt
            messages[0]["content"] += "\n\n" + prompt.CONVERSATION_SUMMARY_BLOCK.format(summary=summary)

        if looks_like_injection(last_text):
            log_event("injection_attempt", request_id=request_id)

        result = router.chat(
            messages,
            temperature=payload["temperature"],
            max_tokens=payload["max_tokens"],
            requested=payload["provider"],
            request_id=request_id,
        )

        if "error" in result:
            log_error("chat_all_failed", Exception(result["detail"]), request_id=request_id)
            return jsonify({"text": "All AI providers are temporarily unavailable. Please try again shortly."}), 503

        elapsed = time.time() - start
        return jsonify({
            "text": result["text"],
            "meta": {
                "tokens": max(1, len(result["text"]) // 4),
                "time": round(elapsed, 2),
                "provider": result["provider"],
                "model": result["model"],
                "category": category,
                "searched": bool(search_text),
            },
        })
    except Exception as e:
        log_error("chat_route_error", e)
        return jsonify({"text": "Something went wrong. Please try again."}), 500


# ---------------------------------------------------------------- stream
@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    auth_error = check_auth()
    if auth_error:
        return auth_error
    if not rate_limit_ok(_client_ip()):
        return jsonify({"error": "Rate limit exceeded. Try again shortly."}), 429

    try:
        data = request.json or {}
        payload, err = validate_chat_payload(data, router)
        if err:
            return err
    except Exception as e:
        log_error("stream_route_validate_error", e)
        return jsonify({"error": "Invalid request."}), 400

    request_id = _client_ip()[:8] + "-" + str(int(time.time() * 1000))[-6:]
    contents = payload["contents"]
    last_text = contents[-1]["content"]
    category = classify(last_text)

    def generate():
        try:
            search_text = ""
            if needs_web_search(category, last_text) and config.ENABLE_WEB_SEARCH:
                yield f"data: {json.dumps({'status': 'Searching trusted sources...'})}\n\n"
                search_text = format_results(search(last_text))

            for mem in extract_memories(last_text):
                memory_store.add(mem)

            summary, trimmed = summarize(contents, router, request_id=request_id)
            messages = build_context(trimmed, memory_store, search_text)
            if summary:
                from voxbox import prompt
                messages[0]["content"] += "\n\n" + prompt.CONVERSATION_SUMMARY_BLOCK.format(summary=summary)

            if looks_like_injection(last_text):
                log_event("injection_attempt", request_id=request_id)

            saw_switch = False
            for event in router.stream(
                messages,
                temperature=payload["temperature"],
                max_tokens=payload["max_tokens"],
                requested=payload["provider"],
                request_id=request_id,
            ):
                if event["type"] == "provider_switch":
                    saw_switch = True
                    yield f"data: {json.dumps({'status': 'VoxBox is switching to another AI provider...'})}\n\n"
                elif event["type"] == "token":
                    yield f"data: {json.dumps({'token': event['text']})}\n\n"
                elif event["type"] == "meta":
                    event["category"] = category
                    event["searched"] = bool(search_text)
                    yield f"data: {json.dumps({'meta': {k: v for k, v in event.items() if k != 'type'}})}\n\n"
                elif event["type"] == "error":
                    raise Exception(event.get("detail") or "unknown error")
            yield "data: [DONE]\n\n"
        except Exception as e:
            log_error("stream_route_error", e, request_id=request_id)
            yield f"data: {json.dumps({'error': 'Something went wrong. Please try again.'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------- title
@app.route("/api/title", methods=["POST"])
def generate_title():
    auth_error = check_auth()
    if auth_error:
        return auth_error

    try:
        data = request.json or {}
        message = (data.get("message") or "").strip()
        if not message or len(message) > config.MAX_MESSAGE_CHARS:
            return jsonify({"title": "New Chat"})

        payload, err = validate_chat_payload(
            {"contents": [{"role": "user", "parts": [{"text": message}]}], "provider": data.get("provider")}, router
        )
        if err:
            return jsonify({"title": "New Chat"})

        result = router.chat(
            [
                {"role": "system", "content": "Generate a short 3-6 word title for a conversation that starts with the following message. Return ONLY the title, nothing else."},
                {"role": "user", "content": message},
            ],
            temperature=0.5,
            max_tokens=40,
            requested=payload["provider"],
        )
        title = (result.get("text") or "").strip().strip('"\'') or "New Chat"
        return jsonify({"title": title[:80]})
    except Exception:
        return jsonify({"title": "New Chat"})


# ---------------------------------------------------------------- memory
@app.route("/api/memory", methods=["GET"])
def list_memory():
    auth_error = check_auth()
    if auth_error:
        return auth_error
    return jsonify({"memory": memory_store.all(), "enabled": memory_store.enabled()})


@app.route("/api/memory/<memory_id>", methods=["DELETE"])
def delete_memory(memory_id):
    auth_error = check_auth()
    if auth_error:
        return auth_error
    if memory_store.delete(memory_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Memory not found."}), 404


@app.route("/api/memory/clear", methods=["POST"])
def clear_memory():
    auth_error = check_auth()
    if auth_error:
        return auth_error
    count = memory_store.clear()
    return jsonify({"ok": True, "cleared": count})


if __name__ == "__main__":
    log_event("server_start", port=config.PORT)
    app.run(host="0.0.0.0", port=config.PORT, debug=config.FLASK_DEBUG)
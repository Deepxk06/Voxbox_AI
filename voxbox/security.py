"""Request validation, rate limiting, and safety helpers."""
import re
import threading
import time
import uuid

from flask import jsonify

from . import config

_request_id_lock = threading.Lock()
_rate = {}  # ip -> list of timestamps


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def make_request_id():
    with _request_id_lock:
        return new_request_id()


def rate_limit_ok(ip: str) -> bool:
    """Simple in-memory sliding-window rate limiter. Disabled when 0."""
    if not config.RATE_LIMIT_PER_MIN:
        return True
    now = time.time()
    with _request_id_lock:
        window = _rate.get(ip, [])
        window = [t for t in window if now - t < 60]
        if len(window) >= config.RATE_LIMIT_PER_MIN:
            _rate[ip] = window
            return False
        window.append(now)
        _rate[ip] = window
    return True


def validate_chat_payload(data: dict, router) -> dict:
    """Validate a chat request payload. Returns (payload, error_response)."""
    if data is None or not isinstance(data, dict):
        return None, (jsonify({"error": "Invalid JSON body."}), 400)

    contents = data.get("contents") or []
    if not isinstance(contents, list) or not contents:
        return None, (jsonify({"error": "No content provided."}), 400)
    if len(contents) > config.MAX_MESSAGES:
        return None, (jsonify({"error": "Too many messages."}), 400)

    cleaned = []
    for msg in contents[: config.MAX_MESSAGES]:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "user")
        text = ""
        if isinstance(msg.get("content"), str):
            text = msg.get("content", "")
        elif isinstance(msg.get("parts"), list):
            text = " ".join(
                p.get("text", "") for p in msg["parts"]
                if isinstance(p, dict) and isinstance(p.get("text"), str)
            )
        text = text.strip()
        if not text:
            continue
        if len(text) > config.MAX_MESSAGE_CHARS:
            return None, (jsonify({"error": "Message too long."}), 400)
        cleaned.append({"role": role, "content": text})
    if not cleaned:
        return None, (jsonify({"error": "No content provided."}), 400)

    provider = data.get("provider", "auto")
    if provider == "auto" or provider is None:
        provider = "auto"
    elif not router.is_valid_provider(provider):
        return None, (jsonify({"error": f"Unknown provider: {provider}"}), 400)

    try:
        temperature = float(data.get("temperature", config.TEMPERATURE))
    except (TypeError, ValueError):
        temperature = config.TEMPERATURE
    temperature = max(0.0, min(2.0, temperature))

    try:
        max_tokens = int(data.get("max_tokens", config.MAX_TOKENS))
    except (TypeError, ValueError):
        max_tokens = config.MAX_TOKENS
    max_tokens = max(1, min(config.MAX_TOKENS_HARD, max_tokens))

    return {
        "contents": cleaned,
        "provider": provider,
        "model": data.get("model"),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }, None


# Prompt-injection defense: delimit untrusted text that travels through
# the conversation (external data is already wrapped server-side in
# prompt.py). This helper flags suspicious instructions in user messages
# for logging only.
_INJECTION_PATTERNS = [
    r"ignore (all |your |previous )?(instructions|prompts|rules)",
    r"system prompt", r"developer message", r"reveal your", r"override your",
    r"disregard the (above|previous)",
]


def looks_like_injection(text: str) -> bool:
    if not text:
        return False
    low = text.lower()
    return any(re.search(p, low) for p in _INJECTION_PATTERNS)


def safe_error_message(exc: Exception) -> str:
    """User-facing message; never leaks internals or keys."""
    text = str(exc)
    if any(k in text.lower() for k in ("api key", "authorization", "token")):
        return "The provider rejected the request. Check your API key configuration."
    return "Something went wrong. Please try again."
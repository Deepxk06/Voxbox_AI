"""Groq provider (OpenAI-compatible REST API)."""
import json
import time
import urllib.error
import urllib.request

from .base import AIProvider, ProviderError
from .. import config

_GROQ_API = "https://api.groq.com/openai/v1"


class GroqProvider(AIProvider):
    id = "groq"
    label = "Groq"
    priority = 2

    def __init__(self):
        super().__init__()
        self.api_key = config.GROQ_API_KEY
        self._default = config.GROQ_MODEL
        self.models = [
            {"id": "groq/compound", "label": "Compound"},
            {"id": "groq/compound-mini", "label": "Compound · Mini"},
            {"id": "allam-2-7b", "label": "Allam 2 · 7B"},
        ]

    def enabled(self) -> bool:
        return bool(self.api_key)

    def _request(self, path: str, payload: dict = None, timeout: float = 90.0) -> dict:
        url = f"{_GROQ_API}{path}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            url, data=data, method="POST" if payload is not None else "GET",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "VoxBox/2.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode()[:300]
            except Exception:
                pass
            status = e.code
            message = f"groq HTTP {status}: {detail}"
            if status in (429, 500, 502, 503, 504):
                raise ProviderError(message, kind="retryable")
            if status in (400, 401, 403):
                raise ProviderError(message, kind="permanent")
            if status == 404:
                raise ProviderError(message, kind="permanent")
            raise ProviderError(message, kind="retryable")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"groq network error: {e}", kind="retryable")

    def discover_models(self) -> list:
        if not self.enabled():
            return []
        try:
            data = self._request("/models", timeout=15.0)
            found = []
            skip = {"whisper", "tts", "speech", "image", "audio", "guard", "embedding", "stt", "rerank"}
            for m in data.get("data", []):
                mid = m.get("id", "")
                if any(s in mid.lower() for s in skip):
                    continue
                found.append({"id": mid, "label": mid})
            if found:
                self.models = found
        except Exception:
            pass
        return self.models

    def default_model(self) -> str:
        if self._default and self._default in {m["id"] for m in self.models}:
            return self._default
        return self.models[0]["id"] if self.models else self._default

    def health(self) -> bool:
        if not self.enabled():
            return False
        try:
            self._request("/models", timeout=10.0)
            return True
        except Exception:
            return False

    def chat(self, messages: list, temperature: float, max_tokens: int) -> str:
        if not self.enabled():
            raise ProviderError("groq not configured", kind="permanent")
        payload = {
            "model": self.default_model(),
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        start = time.time()
        data = self._request("/chat/completions", payload)
        self.state.mark_success(time.time() - start)
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or msg.get("reasoning") or ""
        return self.clean_response(text)

    def stream(self, messages: list, temperature: float, max_tokens: int):
        if not self.enabled():
            raise ProviderError("groq not configured", kind="permanent")
        payload = {
            "model": self.default_model(),
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        url = f"{_GROQ_API}/chat/completions"
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "User-Agent": "VoxBox/2.0"},
        )
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120.0) as resp:
                buffer = ""
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choice = (obj.get("choices") or [{}])[0]
                        delta = choice.get("delta") or {}
                        text = delta.get("content") or delta.get("reasoning") or ""
                        if text:
                            yield text
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode()[:300]
            except Exception:
                pass
            message = f"groq HTTP {e.code}: {detail}"
            raise ProviderError(message, kind="retryable" if e.code in (429, 500, 502, 503, 504) else "permanent")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"groq network error: {e}", kind="retryable")
        self.state.mark_success(time.time() - start)
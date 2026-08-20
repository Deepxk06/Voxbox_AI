"""OpenRouter provider (OpenAI-compatible REST API)."""
import json
import time
import urllib.error
import urllib.request

from .base import AIProvider, ProviderError
from .. import config

_OR_API = "https://openrouter.ai/api/v1"
_HEADERS = {"User-Agent": "VoxBox/2.0"}


class OpenRouterProvider(AIProvider):
    id = "openrouter"
    label = "OpenRouter"
    priority = 3

    def __init__(self):
        super().__init__()
        self.api_key = config.OPENROUTER_API_KEY
        self._default = config.OPENROUTER_MODEL
        self.models = [
            {"id": "deepseek/deepseek-chat-v3-0324:free", "label": "DeepSeek Chat V3 (free)"},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "label": "Llama 3.3 70B (free)"},
            {"id": "qwen/qwen-2.5-72b-instruct:free", "label": "Qwen 2.5 72B (free)"},
        ]

    def enabled(self) -> bool:
        return bool(self.api_key)

    def _request(self, path: str, payload: dict = None, timeout: float = 90.0) -> dict:
        url = f"{_OR_API}{path}"
        data = json.dumps(payload).encode() if payload is not None else None
        headers = dict(_HEADERS)
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method="POST" if payload is not None else "GET", headers=headers)
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
            message = f"openrouter HTTP {e.code}: {detail}"
            if e.code in (429, 500, 502, 503, 504):
                raise ProviderError(message, kind="retryable")
            if e.code in (400, 401, 403):
                raise ProviderError(message, kind="permanent")
            raise ProviderError(message, kind="permanent" if e.code == 404 else "retryable")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"openrouter network error: {e}", kind="retryable")

    def discover_models(self) -> list:
        if not self.enabled():
            return []
        try:
            data = self._request("/models", timeout=15.0)
            found = []
            for m in data.get("data", []) or []:
                mid = m.get("id", "")
                pricing = m.get("pricing") or {}
                prompt_price = float(pricing.get("prompt", 0) or 0)
                completion_price = float(pricing.get("completion", 0) or 0)
                if prompt_price == 0 and completion_price == 0:
                    found.append({"id": mid, "label": m.get("name") or mid})
                if len(found) >= 30:
                    break
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

    def _chat_payload(self, messages: list, temperature: float, max_tokens: int, stream: bool) -> dict:
        return {
            "model": self.default_model(),
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    def chat(self, messages: list, temperature: float, max_tokens: int) -> str:
        if not self.enabled():
            raise ProviderError("openrouter not configured", kind="permanent")
        start = time.time()
        data = self._request("/chat/completions", self._chat_payload(messages, temperature, max_tokens, False))
        self.state.mark_success(time.time() - start)
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or msg.get("reasoning_content") or ""
        return self.clean_response(text)

    def stream(self, messages: list, temperature: float, max_tokens: int):
        if not self.enabled():
            raise ProviderError("openrouter not configured", kind="permanent")
        payload = self._chat_payload(messages, temperature, max_tokens, True)
        headers = dict(_HEADERS)
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            f"{_OR_API}/chat/completions", data=json.dumps(payload).encode(), method="POST", headers=headers
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
                        text = delta.get("content") or delta.get("reasoning_content") or ""
                        if text:
                            yield text
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode()[:300]
            except Exception:
                pass
            message = f"openrouter HTTP {e.code}: {detail}"
            raise ProviderError(message, kind="retryable" if e.code in (429, 500, 502, 503, 504) else "permanent")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"openrouter network error: {e}", kind="retryable")
        self.state.mark_success(time.time() - start)
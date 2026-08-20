"""Local Ollama provider (OpenAI-compatible REST API on localhost)."""
import json
import time
import urllib.error
import urllib.request

from .base import AIProvider, ProviderError
from .. import config

_HEADERS = {"Content-Type": "application/json", "User-Agent": "VoxBox/2.0"}


class OllamaProvider(AIProvider):
    id = "ollama"
    label = "Local (Ollama)"
    priority = 4

    def __init__(self):
        super().__init__()
        self.host = config.OLLAMA_HOST.rstrip("/")
        self._default = config.OLLAMA_MODEL
        self.models = [{"id": config.OLLAMA_MODEL, "label": config.OLLAMA_MODEL}]
        self._reachable = None

    def enabled(self) -> bool:
        return config.ENABLE_LOCAL_FALLBACK

    def _request(self, path: str, payload: dict = None, timeout: float = 30.0) -> dict:
        url = f"{self.host}{path}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, method="POST" if payload is not None else "GET", headers=_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            raise ProviderError(f"ollama HTTP {e.code}", kind="retryable" if e.code in (429, 500, 502, 503, 504) else "permanent")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"ollama unreachable: {e}", kind="retryable")

    def discover_models(self) -> list:
        if not self.enabled():
            return []
        try:
            data = self._request("/api/tags", timeout=5.0)
            found = [{"id": m["name"], "label": m["name"]} for m in data.get("models", [])]
            if found:
                self.models = found
                self._reachable = True
        except Exception:
            self._reachable = False
        return self.models

    def default_model(self) -> str:
        if self._default and self._default in {m["id"] for m in self.models}:
            return self._default
        return self.models[0]["id"] if self.models else self._default

    def health(self) -> bool:
        if not self.enabled():
            return False
        try:
            self._request("/api/tags", timeout=5.0)
            self._reachable = True
            return True
        except Exception:
            self._reachable = False
            return False

    def chat(self, messages: list, temperature: float, max_tokens: int) -> str:
        if not self.enabled():
            raise ProviderError("ollama disabled", kind="permanent")
        payload = {
            "model": self.default_model(),
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "stream": False,
        }
        start = time.time()
        data = self._request("/api/chat", payload)
        self.state.mark_success(time.time() - start)
        return self.clean_response(data.get("message", {}).get("content", ""))

    def stream(self, messages: list, temperature: float, max_tokens: int):
        if not self.enabled():
            raise ProviderError("ollama disabled", kind="permanent")
        payload = {
            "model": self.default_model(),
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "stream": True,
        }
        req = urllib.request.Request(f"{self.host}/api/chat", data=json.dumps(payload).encode(), method="POST", headers=_HEADERS)
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
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if obj.get("done"):
                            break
                        delta = (obj.get("message") or {}).get("content", "")
                        if delta:
                            yield delta
        except urllib.error.HTTPError as e:
            raise ProviderError(f"ollama HTTP {e.code}", kind="retryable" if e.code in (429, 500, 502, 503, 504) else "permanent")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"ollama unreachable: {e}", kind="retryable")
        self.state.mark_success(time.time() - start)
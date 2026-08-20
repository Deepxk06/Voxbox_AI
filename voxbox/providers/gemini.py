"""Google Gemini provider (google-genai SDK)."""
import time

from google import genai
from google.genai import types

from .base import AIProvider, ProviderError
from .. import config


class GeminiProvider(AIProvider):
    id = "gemini"
    label = "Google Gemini"
    priority = 1

    def __init__(self):
        super().__init__()
        self.client = None
        if config.GEMINI_API_KEY:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self._default = config.GEMINI_MODEL
        self.models = [
            {"id": "gemini-3.6-flash", "label": "Gemini 3.6 Flash"},
            {"id": "gemini-3.5-flash", "label": "Gemini 3.5 Flash"},
            {"id": "gemini-3.5-flash-lite", "label": "Gemini 3.5 Flash Lite"},
        ]

    def enabled(self) -> bool:
        return self.client is not None

    def discover_models(self) -> list:
        if not self.enabled():
            return []
        try:
            skip = ("tts", "image", "robotics", "computer-use", "lyria", "deep-research",
                    "antigravity", "nano-banana", "clip", "er-", "omni", "embedding", "imagen")
            found = []
            for m in self.client.models.list():
                mid = m.name.split("/")[-1]
                if any(s in mid.lower() for s in skip):
                    continue
                if "generateContent" in (getattr(m, "supported_actions", None) or []):
                    found.append({"id": mid, "label": m.display_name or mid})
            if found:
                self.models = found
        except Exception as e:
            from ..logging import log_error
            log_error("gemini model discovery failed", e)
        return self.models

    def default_model(self) -> str:
        if self._default and self._default in {m["id"] for m in self.models}:
            return self._default
        return self.models[0]["id"] if self.models else self._default

    def health(self) -> bool:
        if not self.enabled():
            return False
        try:
            self.client.models.get(model=self.default_model())
            return True
        except Exception:
            return False

    def _contents(self, messages: list):
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                continue
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        return contents

    def _system_instruction(self, messages: list) -> str:
        parts = [m["content"] for m in messages if m["role"] == "system"]
        return "\n\n".join(parts) if parts else None

    def chat(self, messages: list, temperature: float, max_tokens: int) -> str:
        if not self.enabled():
            raise ProviderError("gemini not configured", kind="permanent")
        model = self.default_model()
        config_obj = types.GenerateContentConfig(
            system_instruction=self._system_instruction(messages),
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        start = time.time()
        try:
            response = self.client.models.generate_content(
                model=model, contents=self._contents(messages), config=config_obj
            )
        except Exception as e:
            text = str(e)
            if "429" in text or "RESOURCE_EXHAUSTED" in text or "quota" in text.lower():
                raise ProviderError("gemini quota exceeded", kind="retryable") from e
            if "404" in text and ("model" in text.lower() or "not found" in text.lower()):
                raise ProviderError(f"model {model} not found", kind="permanent") from e
            raise ProviderError(f"gemini failed: {text[:200]}", kind="retryable") from e
        self.state.mark_success(time.time() - start)
        return self.clean_response(response.text or "")

    def stream(self, messages: list, temperature: float, max_tokens: int):
        if not self.enabled():
            raise ProviderError("gemini not configured", kind="permanent")
        model = self.default_model()
        config_obj = types.GenerateContentConfig(
            system_instruction=self._system_instruction(messages),
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        start = time.time()
        try:
            stream = self.client.models.generate_content_stream(
                model=model, contents=self._contents(messages), config=config_obj
            )
            for chunk in stream:
                delta = chunk.text
                if delta:
                    yield delta
        except Exception as e:
            text = str(e)
            if "429" in text or "RESOURCE_EXHAUSTED" in text or "quota" in text.lower():
                raise ProviderError("gemini quota exceeded", kind="retryable") from e
            if "404" in text and "model" in text.lower():
                raise ProviderError(f"model {model} not found", kind="permanent") from e
            raise ProviderError(f"gemini failed: {text[:200]}", kind="retryable") from e
        self.state.mark_success(time.time() - start)
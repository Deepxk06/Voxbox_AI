"""AI provider abstraction.

Canonical message format used across VoxBox:
    [{"role": "system"|"user"|"assistant", "content": str}, ...]

Each provider adapts this to its own SDK format.
"""
import re
import time
from abc import ABC, abstractmethod


class ProviderState:
    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    TEMP_UNAVAILABLE = "temporarily_unavailable"
    INVALID = "invalid"
    DISABLED = "disabled"

    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.status = ProviderState.AVAILABLE
        self.failures = 0
        self.cooldown_until = 0.0
        self.last_error = ""
        self.latency = 0.0

    def mark_failure(self, error: str, backoff_base: float = 2.0) -> None:
        self.failures += 1
        self.last_error = error
        if "429" in error or "rate limit" in error.lower() or "resource_exhausted" in error.lower():
            self.status = ProviderState.RATE_LIMITED
        elif any(s in error for s in ("401", "403", "invalid api key", "api key")):
            self.status = ProviderState.INVALID
        else:
            self.status = ProviderState.TEMP_UNAVAILABLE
        delay = min(backoff_base * (2 ** (self.failures - 1)), 60.0)
        self.cooldown_until = time.time() + delay

    def mark_success(self, latency: float) -> None:
        self.failures = 0
        self.cooldown_until = 0.0
        self.status = ProviderState.AVAILABLE
        self.last_error = ""
        self.latency = latency

    def available(self) -> bool:
        return (
            self.status == ProviderState.AVAILABLE
            and time.time() >= self.cooldown_until
        )

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "failures": self.failures,
            "latency": round(self.latency, 2),
        }


class ProviderError(Exception):
    """Raised when a provider call fails in a retryable/permanent way.

    kind: retryable | permanent
    """

    def __init__(self, message: str, kind: str = "retryable"):
        super().__init__(message)
        self.kind = kind


class AIProvider(ABC):
    id = "base"
    label = "Provider"
    priority = 100

    def __init__(self):
        self.state = ProviderState(self.id)
        self.models = []  # list of {"id", "label"}
        self.disabled_models = {}  # model id -> reason

    # --- discovery ---
    @abstractmethod
    def discover_models(self) -> list:
        """Return available model ids. Best effort; fall back to defaults."""

    @abstractmethod
    def default_model(self) -> str:
        """Configured default model id."""

    # --- health ---
    @abstractmethod
    def health(self) -> bool:
        """Quick check that the provider is usable."""

    # --- chat ---
    @abstractmethod
    def chat(self, messages: list, temperature: float, max_tokens: int) -> str:
        """Return the cleaned assistant text for the canonical messages."""

    @abstractmethod
    def stream(self, messages: list, temperature: float, max_tokens: int):
        """Yield cleaned text deltas (str) for the canonical messages."""

    # --- response pipeline ---
    _DUMP_BLOCKS = re.compile(
        r"<(tool|output|search|scratchpad|function|thinking)\b[^>]*>.*?</\1\s*>",
        re.DOTALL | re.IGNORECASE,
    )
    _WRAPPER_TAGS = re.compile(r"</?(answer|final|result)\b[^>]*>", re.IGNORECASE)
    _IDENTITY_FILTERS = [
        (re.compile(r"\bGroq\b", re.IGNORECASE), "VoxBox"),
        (re.compile(r"\bLlama\b", re.IGNORECASE), "VoxBox"),
        (re.compile(r"\bOpenAI\b", re.IGNORECASE), "VoxBox"),
        (re.compile(r"\bGPT\b", re.IGNORECASE), "VoxBox"),
        (re.compile(r"\bLLM\b", re.IGNORECASE), "assistant"),
        (re.compile(r"language model", re.IGNORECASE), "assistant"),
        (re.compile(r"as an AI", re.IGNORECASE), "as VoxBox"),
    ]

    def clean_response(self, text: str) -> str:
        """Full response pipeline: strip dumps, wrappers, identity fixes."""
        if not text:
            return ""
        text = self._DUMP_BLOCKS.sub("", text)
        text = self._WRAPPER_TAGS.sub("", text)
        for pattern, replacement in self._IDENTITY_FILTERS:
            text = pattern.sub(replacement, text)
        return text.strip()

    def models_dict(self) -> list:
        return [{"id": m["id"], "label": m.get("label", m["id"])} for m in self.models]

    def config_dict(self) -> dict:
        return {
            "label": self.label,
            "default_model": self.default_model(),
            "models": self.models_dict(),
        }

    def _check_model(self, model: str):
        ids = {m["id"] for m in self.models}
        if model not in ids:
            raise ProviderError(f"model not available: {model}", kind="permanent")

    def _call_guard(self, fn, model: str):
        """Run fn; on permanent model errors mark the model disabled."""
        try:
            return fn()
        except ProviderError as e:
            if e.kind == "permanent" and "model" in str(e).lower():
                self.disabled_models[model] = str(e)[:200]
            raise
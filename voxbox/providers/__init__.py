"""Provider registry and AI router with automatic fallback."""
import time

from .base import AIProvider, ProviderError
from .gemini import GeminiProvider
from .groq import GroqProvider
from .openrouter import OpenRouterProvider
from .ollama import OllamaProvider
from .. import config
from ..logging import log_event, log_error

PROVIDER_CLASSES = [GeminiProvider, GroqProvider, OpenRouterProvider, OllamaProvider]


class AIRouter:
    """Routes requests across providers with automatic fallback."""

    def __init__(self):
        self.providers = {}
        for cls in PROVIDER_CLASSES:
            instance = cls()
            if instance.enabled():
                instance.discover_models()
                if isinstance(instance, OllamaProvider) and instance._reachable is False:
                    continue
                self.providers[instance.id] = instance
        self.priority_order = [p.id for p in sorted(self.providers.values(), key=lambda p: p.priority)]

    # --- public state ---
    def default_provider_id(self):
        if not self.priority_order:
            return None
        for pid in self.priority_order:
            if self.providers[pid].state.available():
                return pid
        return self.priority_order[0]

    def enabled_providers(self):
        return {pid: p.config_dict() for pid, p in self.providers.items()}

    def provider_states(self):
        return {pid: p.state.as_dict() for pid, p in self.providers.items()}

    def is_valid_provider(self, provider_id):
        return provider_id in self.providers

    def models_for(self, provider_id):
        p = self.providers.get(provider_id)
        return p.models_dict() if p else []

    def default_model_for(self, provider_id):
        p = self.providers.get(provider_id)
        return p.default_model() if p else None

    # --- fallback planning ---
    def _provider_chain(self, requested):
        chain = []
        if requested and requested != "auto" and self.is_valid_provider(requested):
            chain.append(requested)
        for pid in self.priority_order:
            if pid not in chain:
                chain.append(pid)
        return chain

    def _usable(self, provider_id):
        p = self.providers.get(provider_id)
        return p is not None and p.state.available()

    # --- chat ---
    def chat(self, messages, temperature=0.7, max_tokens=2048, requested="auto", request_id=""):
        chain = self._provider_chain(requested)
        fallbacks = 0
        last_error = ""
        for pid in chain:
            if not self._usable(pid):
                continue
            provider = self.providers[pid]
            model = provider.default_model()
            start = time.time()
            try:
                text = provider.chat(messages, temperature, max_tokens)
                if not text:
                    raise ProviderError("empty response", kind="retryable")
                provider.state.mark_success(time.time() - start)
                log_event("chat_ok", request_id=request_id, provider=pid, model=model,
                          latency=round(time.time() - start, 2), fallbacks=fallbacks)
                return {"text": text, "provider": pid, "model": model, "fallbacks": fallbacks}
            except ProviderError as e:
                provider.state.mark_failure(str(e), config.FALLBACK_BACKOFF)
                fallbacks += 1
                last_error = str(e)
                log_error("chat_fallback", e, request_id=request_id, provider=pid,
                          model=model, fallbacks=fallbacks)
                if e.kind == "permanent" and fallbacks >= 1:
                    continue
            except Exception as e:
                provider.state.mark_failure(str(e), config.FALLBACK_BACKOFF)
                fallbacks += 1
                last_error = str(e)
                log_error("chat_fallback", e, request_id=request_id, provider=pid)
        return {"error": "all providers failed", "detail": last_error, "fallbacks": fallbacks}

    # --- streaming ---
    def stream(self, messages, temperature=0.7, max_tokens=2048, requested="auto", request_id=""):
        """Yield event dicts: {type: token|provider_switch|meta|error, ...}"""
        chain = self._provider_chain(requested)
        fallbacks = 0
        last_error = ""
        used_provider = None
        used_model = None
        token_count = 0
        start_time = time.time()

        for pid in chain:
            if not self._usable(pid):
                continue
            provider = self.providers[pid]
            model = provider.default_model()
            if used_provider is not None:
                fallbacks += 1
                yield {"type": "provider_switch", "provider": pid, "model": model}
                log_event("provider_switch", request_id=request_id, from_provider=used_provider, to_provider=pid)
            used_provider = pid
            used_model = model

            buffer = ""
            emitted = ""
            yielded_any = False
            call_started = time.time()
            try:
                for delta in provider.stream(messages, temperature, max_tokens):
                    if delta:
                        buffer += delta
                        token_count += max(1, len(delta) // 4)
                        clean = provider.clean_response(buffer)
                        if len(clean) > len(emitted):
                            new = clean[len(emitted):]
                            emitted = clean
                            yielded_any = True
                            yield {"type": "token", "text": new}
                if not yielded_any:
                    raise ProviderError("empty response", kind="retryable")
                provider.state.mark_success(time.time() - call_started)
                log_event("stream_ok", request_id=request_id, provider=pid, model=model,
                          latency=round(time.time() - call_started, 2), fallbacks=fallbacks)
                yield {
                    "type": "meta",
                    "tokens": token_count,
                    "time": round(time.time() - start_time, 2),
                    "provider": pid,
                    "model": model,
                    "fallbacks": fallbacks,
                }
                return
            except ProviderError as e:
                provider.state.mark_failure(str(e), config.FALLBACK_BACKOFF)
                last_error = str(e)
                log_error("stream_fallback", e, request_id=request_id, provider=pid,
                          model=model, fallbacks=fallbacks)
                continue
            except Exception as e:
                provider.state.mark_failure(str(e), config.FALLBACK_BACKOFF)
                last_error = str(e)
                log_error("stream_fallback", e, request_id=request_id, provider=pid)
                continue

        yield {"type": "error", "message": "all providers failed", "detail": last_error, "fallbacks": fallbacks}


router = AIRouter()
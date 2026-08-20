"""Conversation context engine: summarization, trimming, and durable memory."""
import json
import os
import re
import threading
import time
import uuid

from . import config, prompt
from .logging import log_event, log_error

_SUMMARY_INSTRUCTION = (
    "Summarize the following conversation into a compact bullet list "
    "(max 120 words). Keep key facts, decisions, user preferences, and "
    "open questions. Do not include greetings or small talk."
)


class MemoryStore:
    """Durable user memory persisted to a JSON file (data/memory.json)."""

    def __init__(self, path=None):
        self.path = path or os.path.join(config.DATA_DIR, "memory.json")
        self._lock = threading.Lock()
        self._entries = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._entries = data
        except Exception as e:
            log_error("memory load failed", e)

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def all(self):
        with self._lock:
            return list(self._entries)

    def enabled(self) -> bool:
        return config.ENABLE_MEMORY

    def add(self, text: str, source: str = "conversation"):
        text = text.strip()
        if not text or not self.enabled():
            return None
        with self._lock:
            for existing in self._entries:
                if existing["text"] == text:
                    return existing["id"]
            entry = {
                "id": uuid.uuid4().hex[:12],
                "text": text[:500],
                "source": source,
                "created": time.time(),
            }
            self._entries.append(entry)
            if len(self._entries) > 200:
                self._entries = self._entries[-200:]
            self._save()
            return entry["id"]

    def delete(self, memory_id: str) -> bool:
        with self._lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e["id"] != memory_id]
            if len(self._entries) != before:
                self._save()
                return True
            return False

    def clear(self) -> int:
        with self._lock:
            count = len(self._entries)
            self._entries = []
            self._save()
            return count


_MEMORY_KEYWORDS = [
    r"\bI prefer\b", r"\bI use\b", r"\bI like\b", r"\bI dislike\b", r"\bmy project\b",
    r"\bI work(ing)? on\b", r"\bremember\b", r"\balways\b", r"\bI want you to\b",
    r"\bI am (a|an|using)\b", r"\bI have a\b", r"\bmy (favorite|favourite)\b",
    r"\bI code in\b", r"\bI develop\b", r"\bI build\b",
]


def extract_memories(text: str) -> list:
    """Return short memory-worthy snippets from a user message (best effort)."""
    if not text or not config.ENABLE_MEMORY:
        return []
    if not re.search(r"|".join(_MEMORY_KEYWORDS), text, re.IGNORECASE):
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    memories = []
    for s in sentences:
        s = s.strip()
        if re.search(r"|".join(_MEMORY_KEYWORDS), s, re.IGNORECASE) and 10 <= len(s) <= 300:
            memories.append(s)
    return memories[:3]


def build_context(messages, memory_store=None, search_text=""):
    """Assemble the canonical message list for providers.

    - system prompt + memory block (+ summary block handled by caller)
    - search results injected as a user-role context message (external data)
    - the conversation itself
    """
    system = prompt.BASE_SYSTEM_PROMPT
    blocks = []

    if memory_store and memory_store.enabled():
        memories = memory_store.all()
        if memories:
            lines = "\n".join(f"- {m['text']}" for m in memories[-15:])
            blocks.append(prompt.CONVERSATION_MEMORY_BLOCK.format(memory=lines))

    if blocks:
        system += "\n\n" + "\n\n".join(blocks)

    system += "\n\n" + prompt.KNOWLEDGE_LIMIT_RULE

    result = [{"role": "system", "content": system}]

    if search_text:
        result.append({
            "role": "user",
            "content": prompt.SEARCH_CONTEXT_BLOCK.format(results=search_text),
        })

    for msg in messages:
        if msg.get("role") == "system":
            continue
        role = "assistant" if msg.get("role") in ("assistant", "model") else "user"
        text = msg.get("content", "")
        if not isinstance(text, str):
            parts = msg.get("parts") or []
            text = " ".join(p.get("text", "") for p in parts if isinstance(p, dict))
        if text:
            result.append({"role": role, "content": text})
    return result


def needs_summarization(messages) -> bool:
    if len(messages) <= config.SUMMARY_THRESHOLD_MESSAGES:
        return False
    total = sum(len(str(m.get("content", ""))) for m in messages)
    return total > config.SUMMARY_THRESHOLD_CHARS


def summarize(messages, router, request_id=""):
    """Summarize the older portion of a long conversation.

    Returns (summary_text, trimmed_messages).
    """
    if not needs_summarization(messages):
        return "", messages
    keep = config.KEEP_RECENT_MESSAGES
    old = messages[:-keep]
    recent = messages[-keep:]
    old_text = "\n\n".join(
        f"{m['role']}: {m.get('content', '')}" for m in old if m.get("content")
    )
    if not old_text:
        return "", recent
    try:
        result = router.chat(
            [{"role": "system", "content": _SUMMARY_INSTRUCTION},
             {"role": "user", "content": old_text[:24000]}],
            temperature=0.2,
            max_tokens=300,
            requested="auto",
            request_id=request_id,
        )
        summary = (result.get("text") or "").strip()
        if not summary:
            return "", recent
        log_event("context_summarized", request_id=request_id, old_messages=len(old), summary_len=len(summary))
        return summary, recent
    except Exception as e:
        log_error("summarization failed", e, request_id=request_id)
        return "", recent


memory_store = MemoryStore()
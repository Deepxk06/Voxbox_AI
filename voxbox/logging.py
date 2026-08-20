"""Structured logging for VoxBox.

Never log API keys, tokens, passwords or private user content.
"""
import json
import logging
import time

_LOG = logging.getLogger("voxbox")
if not _LOG.handlers:
    _LOG.setLevel(logging.INFO)
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _LOG.addHandler(_handler)


def _safe_fields(fields: dict) -> dict:
    """Drop any field that could contain secrets."""
    blocked = {"api_key", "authorization", "token", "password", "secret", "contents", "message", "content"}
    return {k: v for k, v in fields.items() if k.lower() not in blocked}


def log_event(event: str, **fields) -> None:
    safe = _safe_fields(fields)
    safe["event"] = event
    safe["ts"] = time.time()
    _LOG.info(json.dumps(safe, default=str))


def log_error(event: str, error: Exception, **fields) -> None:
    safe = _safe_fields(fields)
    safe["event"] = event
    safe["error_type"] = type(error).__name__
    safe["error"] = str(error)[:500]
    safe["ts"] = time.time()
    _LOG.error(json.dumps(safe, default=str))
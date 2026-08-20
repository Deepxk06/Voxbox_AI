"""Environment configuration for VoxBox.

All settings are read once at import time. Backward compatible with the
legacy variable names (GOOGLE_API_KEY / GROQ_API_KEY / GROQ_MODEL /
GEMINI_MODEL) while accepting the new names from the specification.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --- API keys (aliases for backward compatibility) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or ""

# --- Auth ---
VOXBOX_API_TOKEN = os.getenv("VOXBOX_API_TOKEN", "")

# --- Server ---
PORT = _int("PORT", 5000)
FLASK_DEBUG = _bool("FLASK_DEBUG", False)

# --- Models ---
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.6-flash"
GROQ_MODEL = os.getenv("GROQ_MODEL") or "groq/compound"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL") or "deepseek/deepseek-chat-v3-0324:free"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or "llama3.2"
OLLAMA_HOST = os.getenv("OLLAMA_HOST") or "http://localhost:11434"

# --- Generation defaults ---
TEMPERATURE = _float("TEMPERATURE", 0.7)
MAX_TOKENS = _int("MAX_TOKENS", 2048)
MAX_TOKENS_HARD = 8192

# --- Features ---
ENABLE_WEB_SEARCH = _bool("ENABLE_WEB_SEARCH", True)
ENABLE_MEMORY = _bool("ENABLE_MEMORY", True)
ENABLE_LOCAL_FALLBACK = _bool("ENABLE_LOCAL_FALLBACK", True)

# --- Fallback / retry ---
MAX_FALLBACKS = _int("MAX_FALLBACKS", 3)
FALLBACK_BACKOFF = _float("FALLBACK_BACKOFF", 2.0)  # seconds, doubles per failure

# --- Request validation ---
MAX_CONTENT_LENGTH = _int("MAX_CONTENT_LENGTH", 1_048_576)  # 1 MB
MAX_MESSAGE_CHARS = _int("MAX_MESSAGE_CHARS", 50_000)
MAX_MESSAGES = _int("MAX_MESSAGES", 200)
RATE_LIMIT_PER_MIN = _int("RATE_LIMIT_PER_MIN", 0)  # 0 = disabled

# --- CORS ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000")
CORS_ORIGIN_LIST = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

# --- Storage ---
DATA_DIR = os.getenv("VOXBOX_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))

# --- Search ---
SEARCH_RESULTS = _int("SEARCH_RESULTS", 5)
SEARCH_TIMEOUT = _float("SEARCH_TIMEOUT", 8.0)

# --- Context engine ---
SUMMARY_THRESHOLD_MESSAGES = _int("SUMMARY_THRESHOLD_MESSAGES", 14)
SUMMARY_THRESHOLD_CHARS = _int("SUMMARY_THRESHOLD_CHARS", 12_000)
KEEP_RECENT_MESSAGES = _int("KEEP_RECENT_MESSAGES", 8)
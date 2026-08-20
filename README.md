# VoxBox AI — Your intelligent coding companion

A production-grade, ChatGPT-style AI coding assistant built on **free-first** AI
providers. Reliable answers through multiple providers, automatic fallback,
current-information retrieval, durable memory, and a polished responsive UI.

## Features

- **Multi-provider with automatic fallback** — Gemini → Groq → OpenRouter → local Ollama
- **Provider abstraction** (`voxbox/providers/`) with health tracking, backoff, and model discovery
- **Dynamic model discovery** — retired/404 models are disabled automatically, never break the app
- **Streaming (SSE)** and non-streaming chat
- **Current-information handling** — lightweight classifier triggers web search only when needed; results are injected as untrusted data with source citations
- **Conversation memory** — durable facts stored server-side (`data/memory.json`), viewable/deletable in Settings
- **Context engine** — long conversations are summarized and trimmed to avoid context overflow
- **Response quality pipeline** — dump/tool-markup stripping, empty-response protection, retry + fallback
- **Security** — keys stay server-side, request validation, rate limiting, prompt-injection isolation, safe client-side code runner (Pyodide / iframe / AsyncFunction), restricted CORS
- **Professional UI** — light/dark themes, sidebar history (Today/Yesterday/7 days/Older), welcome screen, premium code blocks (copy/run/download), voice input + TTS, command palette (Ctrl+K), search, import/export (JSON/MD/TXT/HTML), settings, mobile responsive

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  |  source .venv/bin/activate  (macOS/Linux)
pip install -r requirements.txt
copy .env.example .env        # Windows  |  cp .env.example .env  (macOS/Linux)
python app_groq.py
```

Open `http://localhost:5000`. At least one API key is required:

| Provider  | Key (free)                    | Default model                    |
|-----------|-------------------------------|----------------------------------|
| Gemini    | `GEMINI_API_KEY` (Google AI Studio) | `gemini-3.6-flash`          |
| Groq      | `GROQ_API_KEY` (console.groq.com)   | `groq/compound`              |
| OpenRouter| `OPENROUTER_API_KEY`          | `deepseek/deepseek-chat-v3-0324:free` |
| Ollama    | local install                 | `llama3.2` (auto-disabled if unreachable) |

## API

All endpoints accept an optional `provider` and `model`; CORS is enabled for
configured origins, and if `VOXBOX_API_TOKEN` is set every request needs the
header `X-VoxBox-Token: <token>`.

### GET `/api/models`
```json
{
  "providers": { "gemini": {"label":"Google Gemini","default_model":"gemini-3.6-flash","models":[...]}, "groq": {...} },
  "default_provider": "gemini",
  "default_model": "gemini-3.6-flash",
  "auth_required": false,
  "memory_enabled": true,
  "web_search_enabled": true
}
```

### GET `/api/health`
```json
{ "status": "ok", "version": "2.0.0", "providers": { "gemini": "available", "groq": "available" } }
```

### POST `/api/chat` (non-streaming)
```json
{ "provider": "auto", "model": null, "contents": [{"role":"user","parts":[{"text":"..."}]}], "temperature": 0.7, "max_tokens": 2048 }
```
Response: `{"text":"...", "meta":{"tokens":…,"time":…,"provider":"gemini","model":"…","category":"CODING","searched":false}}`

### POST `/api/chat/stream` (SSE)
Same payload. Frames: `{"token":"…"}`, `{"status":"Searching trusted sources..."}`,
`{"status":"VoxBox is switching to another AI provider..."}`, `{"meta":{…}}`, then `[DONE]`.

### POST `/api/title`
`{"message":"…"}` → `{"title":"Debugging"}`

### Memory
- `GET /api/memory` — list stored memories
- `DELETE /api/memory/<id>` — delete one
- `POST /api/memory/clear` — clear all

## Project layout

```
app_groq.py          Flask application + routes (reads frontend.html)
frontend.html        Full UI (design system, chat, composer, settings, palette)
voxbox/
  config.py          environment configuration
  logging.py         structured logging (never logs secrets)
  prompt.py          system prompts + external-data isolation
  classifier.py      lightweight question classification
  search.py          DuckDuckGo retrieval + source extraction
  context.py         conversation summarization + durable memory
  security.py        request validation, rate limiting
  providers/
    base.py          AIProvider ABC + response pipeline
    gemini.py groq.py openrouter.py ollama.py
    __init__.py      registry + AI router with automatic fallback
client.py            Python API client (demo: python client.py interactive)
data/memory.json     durable memory (auto-created, gitignored)
```

## Configuration

See `.env.example` for the full list (temperature, max tokens, search/memory/fallback
toggles, payload limits, rate limiting, CORS origins). Settings can also be changed
in the UI (Settings → AI / Appearance / Voice / Memory / Data).

## Architecture notes

- **Routing** — the router tries providers in priority order (Gemini first), tracks
  per-provider state (available / rate_limited / temporarily_unavailable / invalid),
  applies exponential backoff (2s→4s→8s…), and switches providers on 429/5xx/timeout/
  empty/malformed responses. Users see a friendly "switching provider" status, never
  raw errors.
- **Context** — conversations over the threshold are summarized by the default provider
  and trimmed; durable facts are extracted from messages and stored in memory.
- **Search** — only `CURRENT_INFORMATION` questions trigger retrieval. Results are
  wrapped in `<external_data>` and treated as untrusted data to resist prompt injection.
- **Code execution** — runs entirely client-side (WebAssembly Pyodide for Python, sandboxed
  iframes for HTML, AsyncFunction for JS). The server never `exec`s user code.

## Testing

```bash
python -m py_compile app_groq.py voxbox/*.py voxbox/providers/*.py
python client.py basic       # models + both providers
python client.py interactive # interactive chat
```

## License

MIT — free to use and modify. Free-tier providers mean no credit card required.
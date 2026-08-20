# VoxBox AI — Setup Guide

VoxBox is a production-grade free AI coding assistant with **automatic provider
fallback** across Gemini, Groq, OpenRouter and local Ollama. One key is enough;
providers without a key are simply hidden.

## What's Included

- Multi-provider routing (Gemini → Groq → OpenRouter → Ollama) with health tracking + backoff
- Dynamic model discovery (retired models are auto-disabled)
- Streaming (SSE) + non-streaming chat, title generation, model listing, health endpoint
- Current-information retrieval with source citations (DuckDuckGo, no key required)
- Durable conversation memory (`data/memory.json`), long-conversation summarization
- Browser code execution (JavaScript / Python via Pyodide / HTML in sandboxed iframes)
- Voice input/output, conversation history, search, import/export, token tracking
- Professional responsive UI (light/dark, command palette, settings, mobile)
- Request validation, rate limiting, prompt-injection isolation, optional token auth, restricted CORS

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`
```bash
copy .env.example .env   # Windows (cmd)
# Copy-Item .env.example .env   # PowerShell
```
```env
GEMINI_API_KEY="your_free_google_key"   # or GOOGLE_API_KEY (alias)
GROQ_API_KEY="your_free_groq_key"
```
Optional (OpenRouter / local):
```env
OPENROUTER_API_KEY="your_key"
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="llama3.2"
```

Get free keys (no credit card): https://aistudio.google.com/app/apikey and https://console.groq.com

### 3. Run
```bash
python app_groq.py
```
Open `http://localhost:5000`.

## Example Requests

### Chat (auto provider, streaming)
```bash
curl -N -X POST http://localhost:5000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Explain recursion"}]}]}'
```
Frames: `{"token":"…"}` … `{"meta":{…}}` … `[DONE]`. On provider failure you may
see `{"status":"VoxBox is switching to another AI provider..."}` before tokens resume.

### Non-streaming
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

### With auth token
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-VoxBox-Token: your_secret" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

### Health / models
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/models
```

## Model Customization

Default models come from `.env` (`GEMINI_MODEL`, `GROQ_MODEL`, `OPENROUTER_MODEL`,
`OLLAMA_MODEL`). At startup each provider discovers its available models; the configured
default is used if present, otherwise the first available model wins. Disabled/404 models
are skipped automatically — never edit code to retire a model.

## API Summary

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Web UI |
| `/api/models` | GET | List enabled providers, models, defaults |
| `/api/health` | GET | Server + provider health |
| `/api/chat` | POST | Non-streaming chat |
| `/api/chat/stream` | POST | SSE streaming chat |
| `/api/title` | POST | Conversation title |
| `/api/memory` | GET | List memories |
| `/api/memory/<id>` | DELETE | Delete one memory |
| `/api/memory/clear` | POST | Clear all memories |

Request body: `{provider: "auto"|"gemini"|"groq"|"openrouter"|"ollama", model, contents: [{role, parts: [{text}]}], temperature, max_tokens}`.

If `VOXBOX_API_TOKEN` is set, every request needs `X-VoxBox-Token: <token>`.

## Architecture

```
Browser (frontend.html)
  └─ /api/chat(stream) ─┐
                        ▼
              AIRouter (voxbox/providers)
              Gemini → Groq → OpenRouter → Ollama
                        │
                        ├─ classifier  (CURRENT_INFORMATION? → web search)
                        ├─ context     (summarize long chats, memory)
                        └─ security    (validate, rate limit, sanitize)
```

- Provider state is tracked (available / rate_limited / temporarily_unavailable / invalid)
  with exponential backoff; retries stop after the configured fallback budget.
- Search results are injected as `<external_data>` (untrusted) so instructions in web
  content cannot override the system prompt.
- The UI stores conversations in `localStorage`; durable memory is server-side in
  `data/memory.json` (gitignored).

## Troubleshooting

| Problem | Fix |
|---|---|
| "No AI provider is available" | Add at least one key to `.env`, restart server |
| 401 Unauthorized | Provide `X-VoxBox-Token` or set it in Settings |
| Import errors | `pip install -r requirements.txt --upgrade` |
| Slow Python run in UI | First run downloads Pyodide (~10 MB), then it's cached |
| Gemini unavailable in health | Free-tier quota may be exhausted; the router auto-falls back to Groq |
| Local Ollama missing | Install Ollama or set `ENABLE_LOCAL_FALLBACK=false` |
# VoxBox AI — Setup Guide

VoxBox is a free voice coding assistant with two free AI providers: **Groq** and **Google Gemini**. One key is enough; providers without a key are simply hidden.

## What's Included

- Groq + Gemini providers with in-UI model switching
- Streaming (SSE) and non-streaming chat, title generation, model listing
- Browser code execution (JavaScript / Python / HTML)
- Voice input/output, conversation history, import/export, token usage per chat
- Optional API token auth and CORS support

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
GROQ_API_KEY="your_free_groq_key"
GOOGLE_API_KEY="your_free_google_key"
```

Optional:
```env
GROQ_MODEL="llama-3.1-8b-instant"      # default Groq model
GEMINI_MODEL="gemini-2.0-flash"        # default Gemini model
VOXBOX_API_TOKEN="secret"              # protect the API
PORT=5000
```

Get free keys (no credit card): https://console.groq.com/ and https://aistudio.google.com/app/apikey

### 3. Run
```bash
python app_groq.py
```
Open `http://localhost:5000`.

## Example Requests

### Groq (streaming)
```bash
curl -X POST http://localhost:5000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"provider":"groq","model":"llama-3.1-8b-instant","contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

### Gemini (non-streaming)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"provider":"gemini","model":"gemini-2.0-flash","contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

### With auth token
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-VoxBox-Token: your_secret" \
  -d '{"provider":"groq","contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

### List available providers/models
```bash
curl http://localhost:5000/api/models
```

## Model Customization

Available models are defined in `PROVIDERS` inside `app_groq.py`. To add a model,
append `{"id": "model-id", "label": "Display Label"}` to the provider's `models`
list. To change the default, set `GROQ_MODEL` / `GEMINI_MODEL` in `.env`.

## API Summary

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/models` | GET | List enabled providers + models |
| `/api/chat` | POST | Non-streaming chat |
| `/api/chat/stream` | POST | SSE streaming chat |
| `/api/title` | POST | Conversation title |
| `/` | GET | Web UI |

Request body: `{provider, model, contents: [{role, parts: [{text}]}], temperature, max_tokens}`.

If `VOXBOX_API_TOKEN` is set, every request needs `X-VoxBox-Token: <token>`.

## Architecture

```
Browser (app_groq.py embedded UI)
  └─ /api/chat(stream) ─ Groq SDK ──► Groq API (llama-3.1-8b-instant, ...)
                       └ google-genai SDK ─► Google Gemini API (gemini-2.0-flash, ...)
```
- Streaming uses Server-Sent Events; each `data:` frame carries a token chunk.
- The final frame carries `meta` with token count, elapsed time, provider, and model.
- Token counts come from provider usage metadata when available, otherwise estimated.
- The UI stores conversations in `localStorage` (title, history, tokens).

## Troubleshooting

| Problem | Fix |
|---|---|
| "No provider available" | Add a key to `.env`, restart server |
| 401 Unauthorized | Provide `X-VoxBox-Token` or set it in Settings |
| Import errors | `pip install -r requirements.txt --upgrade` |
| Slow Python run in UI | First run downloads Pyodide (~10 MB), then it's cached |
| Gemini model not listed | Check `GOOGLE_API_KEY`, restart server |

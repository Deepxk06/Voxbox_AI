# VoxBox AI — Free Tier Voice Coding Assistant

VoxBox is a fast, intelligent coding voice assistant powered by **free** AI providers:

- **Groq** — `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` (free, no credit card)
- **Google Gemini** — `gemini-2.0-flash`, `gemini-2.5-flash` (free, no credit card)

Switch providers/models from a dropdown in the header — no restart needed.

## Features

- Multi-provider (Groq + Gemini) with in-UI **model selector**
- Streaming (SSE) and non-streaming chat endpoints
- **Run code blocks in the browser** (JavaScript / Python / HTML)
- Voice input (Web Speech API) and voice output (TTS)
- Conversation history, search, **import/export** (JSON/MD/TXT/HTML)
- Per-conversation **token usage** tracking
- Dark/light theme, command palette, keyboard shortcuts
- Markdown rendering with syntax highlighting and Mermaid diagrams
- Optional **API token auth** for remote deployments
- **CORS enabled** for cross-origin API clients

## Installation

### Prerequisites
- Python 3.9+

### Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd Voxbox_AI
```

2. **Create and activate a virtual environment**
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API keys (free)**
```bash
copy .env.example .env
# Windows (PowerShell):
# Copy-Item .env.example .env
```
Edit `.env`:
```env
GROQ_API_KEY="your_free_groq_api_key"
GOOGLE_API_KEY="your_free_google_api_key"
```

> One provider key is enough — VoxBox only shows providers you have keys for.

### Getting FREE API Keys

- **Groq**: https://console.groq.com/ — no credit card needed
- **Google Gemini**: https://aistudio.google.com/app/apikey — no credit card needed

## Usage

### Run the Application
```bash
python app_groq.py
```
Open `http://localhost:5000` (port configurable via `PORT` env var).

### API Endpoints

All endpoints accept an optional `provider` and `model`. CORS is enabled, and if
`VOXBOX_API_TOKEN` is set, all requests must include the header
`X-VoxBox-Token: <token>`.

#### 1. List Providers/Models
**GET** `/api/models`
```json
{
  "providers": {
    "groq": {"label": "Groq (FREE)", "default_model": "llama-3.1-8b-instant", "models": [...]},
    "gemini": {"label": "Google Gemini (FREE)", "default_model": "gemini-2.0-flash", "models": [...]}
  },
  "default_provider": "groq",
  "default_model": "llama-3.1-8b-instant",
  "auth_required": false
}
```

#### 2. Chat Endpoint (Streaming)
**POST** `/api/chat/stream`
```json
{
  "provider": "groq",
  "model": "llama-3.1-8b-instant",
  "contents": [{"role": "user", "parts": [{"text": "How do I write a Python function?"}]}],
  "temperature": 0.7,
  "max_tokens": 2048
}
```
Response: Server-Sent Events stream with token chunks, final `meta` (tokens/time/provider/model), then `[DONE]`.

#### 3. Chat Endpoint (Non-Streaming)
**POST** `/api/chat`
```json
{
  "provider": "gemini",
  "model": "gemini-2.0-flash",
  "contents": [{"role": "user", "parts": [{"text": "Explain async/await in JavaScript"}]}],
  "temperature": 0.7,
  "max_tokens": 2048
}
```
Response:
```json
{
  "text": "...",
  "meta": {"tokens": 150, "time": 2.45, "provider": "gemini", "model": "gemini-2.0-flash"}
}
```

#### 4. Title Generation
**POST** `/api/title`
```json
{"provider": "groq", "message": "How do I optimize my React components?"}
```
Response: `{"title": "React Performance Optimization"}`

## Client

`client.py` is a ready-to-use API client:
```bash
python client.py basic        # Test Groq + Gemini
python client.py stream       # Streaming demo
python client.py title        # Title generation demo
python client.py temp         # Temperature comparison
python client.py interactive  # Interactive chat (/provider, /model, /stream, /quit)
```

```python
from client import VoxBoxClient

client = VoxBoxClient(token="your-token-if-set")
result = client.chat("Write a factorial function", provider="groq")
print(result["text"])
```

## Configuration

### `.env` variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Enables the Groq provider |
| `GOOGLE_API_KEY` | — | Enables the Gemini provider |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Default Groq model |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Default Gemini model |
| `VOXBOX_API_TOKEN` | — | If set, requires `X-VoxBox-Token` on all API calls |
| `PORT` | `5000` | Flask port |

### Temperature (0.0–2.0)
- **0.0** deterministic (best for code) · **0.7** balanced (default) · **1.5+** creative

### Max Tokens
Default: 2048. Adjustable in Settings or per request.

## Troubleshooting

### "No provider available"
- Ensure at least one API key is set in `.env`
- Restart the server after editing `.env`

### 401 Unauthorized
- The server has `VOXBOX_API_TOKEN` set — add the token in Settings, or send the `X-VoxBox-Token` header.

### Import errors
```bash
pip install -r requirements.txt --upgrade
```

### No response
- Try the other provider from the model dropdown
- Check the server console for the real error message

## Requirements

See `requirements.txt`: Flask, Flask-Cors, python-dotenv, groq, google-genai.

## License

MIT License — feel free to use and modify.

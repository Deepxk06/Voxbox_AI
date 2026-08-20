# VoxBox AI — Quick Reference

## Quick Start (30 seconds)

```bash
pip install -r requirements.txt
copy .env.example .env          # Windows (cmd)
# Copy-Item .env.example .env   # PowerShell
# edit .env → add GEMINI_API_KEY and/or GROQ_API_KEY
python app_groq.py
# open http://localhost:5000
```

Free keys (no credit card): https://aistudio.google.com/app/apikey · https://console.groq.com

## Providers (priority order, auto-fallback)

| Provider | Default model | Notes |
|---|---|---|
| gemini | gemini-3.6-flash | Fast, free via AI Studio |
| groq | groq/compound | Fast, free via console.groq.com |
| openrouter | deepseek/deepseek-chat-v3-0324:free | Optional, free models |
| ollama | llama3.2 | Local, auto-disabled if unreachable |

The router tries the requested provider (or `auto`) first, then falls back down
the priority list on 429 / 5xx / timeout / empty / malformed responses.

## API Endpoints

| Endpoint | Method | Notes |
|---|---|---|
| `/` | GET | Web UI |
| `/api/models` | GET | Providers, models, defaults, auth state |
| `/api/health` | GET | Server + provider health |
| `/api/chat` | POST | Non-streaming response |
| `/api/chat/stream` | POST | SSE streaming response |
| `/api/title` | POST | Generate conversation title |
| `/api/memory` | GET | List stored memories |
| `/api/memory/<id>` | DELETE | Delete one memory |
| `/api/memory/clear` | POST | Clear all memories |

Request shape:
```json
{
  "provider": "auto",
  "model": null,
  "contents": [{"role": "user", "parts": [{"text": "Hello!"}]}],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Streaming frames: `{"token":"…"}` · optional `{"status":"…"}` (searching/switching)
· `{"meta":{tokens,time,provider,model,category,searched}}` · `[DONE]`

If `VOXBOX_API_TOKEN` is set in `.env`, add header `X-VoxBox-Token: <token>` to every request.

## Usage Examples

### Python
```python
from client import VoxBoxClient

client = VoxBoxClient()                     # token="..." if auth enabled
result = client.chat("Write a Python function")   # provider defaults to auto
print(result['text'])
```

### cURL
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

### JavaScript (CORS enabled for configured origins)
```javascript
const res = await fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    contents: [{ role: 'user', parts: [{ text: 'Hello!' }] }]
  })
});
console.log((await res.json()).text);
```

## Test Client

```bash
python client.py basic        # Test providers
python client.py stream       # Streaming demo
python client.py title        # Title generation
python client.py temp         # Temperature comparison
python client.py interactive  # Interactive chat
```

Interactive commands: `/provider <id>`, `/model <id>`, `/stream`, `/quit`

## UI Features

| Feature | How |
|---|---|
| New chat / history | Sidebar (Today/Yesterday/7 days/Older) |
| Switch model/provider | Header dropdowns or Settings |
| Run code | "Run" on JS/Python/HTML code blocks (sandboxed, client-side) |
| Copy / Download code | Code block header buttons |
| Voice input | Mic button (falls back gracefully if unsupported) |
| Voice output (TTS) | Toggle in composer / Settings (rate + voice select) |
| Command palette | Ctrl+K |
| Search chats | Ctrl+K → "Search chats", or header search |
| Import/Export | Settings → Data (JSON/MD/TXT/HTML) |
| Memory | Settings → Memory (view/delete/clear) |
| Theme | Header moon icon or Settings |

## Slash commands

`/debug` `/explain` `/refactor` `/optimize` `/test` `/document` `/review` `/convert` `/sql`

## Configuration (`.env`)

| Variable | Default |
|---|---|
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | — |
| `GROQ_API_KEY` | — |
| `OPENROUTER_API_KEY` | — |
| `GEMINI_MODEL` | gemini-3.6-flash |
| `GROQ_MODEL` | groq/compound |
| `TEMPERATURE` | 0.7 |
| `MAX_TOKENS` | 2048 |
| `ENABLE_WEB_SEARCH` | true |
| `ENABLE_MEMORY` | true |
| `ENABLE_LOCAL_FALLBACK` | true |
| `VOXBOX_API_TOKEN` | — (auth disabled) |
| `PORT` | 5000 |
| `RATE_LIMIT_PER_MIN` | 0 (disabled) |
| `CORS_ORIGINS` | localhost:5000 |

## Troubleshooting

- **No provider available** → add at least one key to `.env`, restart server
- **401** → server requires a token; set it in Settings
- **Import errors** → `pip install -r requirements.txt --upgrade`
- **No response / switching provider** → free-tier quota exhausted; the router falls
  back automatically and shows a status message
- **Models change after a provider retires a model** → restart; discovery re-enables the live list

## Files

```
Voxbox_AI/
├── app_groq.py            # Flask app + routes
├── frontend.html          # Full UI
├── voxbox/                # Backend package (providers, router, context, search, security)
├── client.py              # Python API client
├── requirements.txt       # Dependencies
├── .env.example           # Key template (copy to .env)
├── README.md              # Full docs
├── SETUP_GUIDE.md         # Detailed setup
└── QUICK_REFERENCE.md     # This file
```

**Cost: $0 | Credit card: Not required | Rate limits: fair use**
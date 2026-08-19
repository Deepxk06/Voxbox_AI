# VoxBox AI — Quick Reference

## Quick Start (30 seconds)

```bash
pip install -r requirements.txt
copy .env.example .env          # Windows (cmd)
# Copy-Item .env.example .env   # PowerShell
# edit .env → add GROQ_API_KEY and/or GOOGLE_API_KEY
python app_groq.py
# open http://localhost:5000
```

Free keys (no credit card): https://console.groq.com/ · https://aistudio.google.com/app/apikey

## Available FREE Providers

| Provider | Models | Speed | Free |
|---|---|---|---|
| groq | llama-3.1-8b-instant, llama-3.3-70b-versatile, mixtral-8x7b-32768 | ⚡⚡⚡ | ✅ No CC |
| gemini | gemini-2.0-flash, gemini-2.5-flash | ⚡⚡ | ✅ No CC |

Switch anytime from the model dropdown in the header.

## API Endpoints

| Endpoint | Method | Notes |
|---|---|---|
| `/api/models` | GET | List providers/models, defaults, auth_required |
| `/api/chat` | POST | Non-streaming response |
| `/api/chat/stream` | POST | SSE streaming response |
| `/api/title` | POST | Generate conversation title |

Request shape:
```json
{
  "provider": "groq",
  "model": "llama-3.1-8b-instant",
  "contents": [{"role": "user", "parts": [{"text": "Hello!"}]}],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Response meta: `{"tokens": 150, "time": 2.45, "provider": "groq", "model": "..."}`

If `VOXBOX_API_TOKEN` is set in `.env`, add header `X-VoxBox-Token: <token>` to every request.

## Usage Examples

### Python
```python
from client import VoxBoxClient

client = VoxBoxClient()                     # token="..." if auth enabled
result = client.chat("Write a Python function", provider="groq")
print(result['text'])
```

### cURL
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"provider":"gemini","contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

### JavaScript (CORS enabled)
```javascript
const res = await fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    provider: 'groq',
    contents: [{ role: 'user', parts: [{ text: 'Hello!' }] }]
  })
});
console.log((await res.json()).text);
```

## Test Client

```bash
python client.py basic        # Test Groq + Gemini
python client.py stream       # Streaming demo
python client.py title        # Title generation
python client.py temp         # Temperature comparison
python client.py interactive  # Interactive chat
```

Interactive commands: `/provider groq|gemini`, `/model <id>`, `/stream`, `/quit`

## UI Features

| Feature | How |
|---|---|
| Switch model/provider | Header dropdown |
| Run code | "Run" button on JS/Python/HTML code blocks |
| Voice input | Mic button (Ctrl+M) |
| Voice output | Auto-read toggle in Settings |
| Import/Export | Sidebar footer → Import/Export Data |
| Token usage | Header subtitle + sidebar per conversation |
| Theme | Ctrl+D |
| Command palette | Ctrl+K |

## Configuration (`.env`)

| Variable | Default |
|---|---|
| `GROQ_API_KEY` | — |
| `GOOGLE_API_KEY` | — |
| `GROQ_MODEL` | llama-3.1-8b-instant |
| `GEMINI_MODEL` | gemini-2.0-flash |
| `VOXBOX_API_TOKEN` | — (auth disabled) |
| `PORT` | 5000 |

## Troubleshooting

- **"No provider available"** → add a key to `.env`, restart server
- **401** → server requires a token; set it in Settings
- **Import errors** → `pip install -r requirements.txt --upgrade`
- **No response** → try the other provider, check server logs

## Files

```
Voxbox_AI/
├── app_groq.py            # Main Flask app + embedded UI
├── client.py              # Python API client
├── requirements.txt       # Dependencies
├── .env.example           # Key template (copy to .env)
├── README.md              # Full docs
├── SETUP_GUIDE.md         # Detailed setup
└── QUICK_REFERENCE.md     # This file
```

**Cost: $0 | Credit card: Not required | Rate limits: fair use**

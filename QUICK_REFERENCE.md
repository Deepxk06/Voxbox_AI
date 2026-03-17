# VoxBox AI - Quick Reference (FREE TIER)

## 🚀 Quick Start (30 seconds)

### 1. Install Packages
```bash
pip install -r requirements.txt
```

### 2. Add FREE API Keys to `.env`
```env
GROQ_API_KEY="your_free_groq_key"
GOOGLE_API_KEY="your_free_google_key"
```

**No credit card required!**

### 3. Run Server
```bash
python app_groq.py
```

### 4. Open Browser
```
http://localhost:5000
```

---

## 🤖 Available FREE Providers

| Provider | Model | Speed | Quality | Free |
|----------|-------|-------|---------|------|
| **groq** | llama-3.1-8b | ⚡⚡⚡ | ⭐⭐⭐ | ✅ No CC |
| **gemini** | gemini-pro | ⚡⚡ | ⭐⭐⭐⭐ | ✅ No CC |

---

## 📡 API Endpoints

### Chat (Non-Streaming)
```
POST /api/chat
```
**Request:**
```json
{
  "provider": "groq",
  "contents": [{"role": "user", "parts": [{"text": "Hello!"}]}],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

### Chat (Streaming)
```
POST /api/chat/stream
```
Returns Server-Sent Events stream

### Generate Title
```
POST /api/title
```
**Request:**
```json
{
  "provider": "gemini",
  "message": "Your message here"
}
```

---

## 💻 Usage Examples

### Python
```python
from client import VoxBoxClient

client = VoxBoxClient()
result = client.chat("Write a Python function", provider="groq")
print(result['text'])
```

### JavaScript/Fetch
```javascript
const response = await fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    provider: 'gemini',
    contents: [{ role: 'user', parts: [{ text: 'Hello!' }] }]
  })
});
const data = await response.json();
console.log(data.text);
```

### cURL
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"provider":"groq","contents":[{"role":"user","parts":[{"text":"Hi!"}]}]}'
```

---

## 🎮 Test Client

Interactive client with demo modes:

```bash
# Test all FREE providers
python client.py basic

# Streaming demo
python client.py stream

# Interactive chat
python client.py interactive
```

---

## 🔑 Get FREE API Keys

1. **Groq** (Free, No CC): https://console.groq.com/
2. **Google Gemini** (Free, No CC): https://makersuite.google.com/app/apikey

---

## 📚 Documentation

- **README.md** - Full documentation
- **SETUP_GUIDE.md** - Detailed setup instructions
- **client.py** - Python client examples

---

## ⚙️ Configuration

### Temperature (0.0 - 2.0)
- **0.0** - Deterministic (best for coding)
- **0.7** - Balanced (default)
- **1.5+** - Creative

### Max Tokens
- Default: 2048
- Min: 1
- Max: Model dependent

---

## 🐛 Troubleshooting

### Provider not found
← Check `.env` has valid API keys
← Get free keys: groq.com & makersuite.google.com

### Import error
```bash
pip install -r requirements.txt --upgrade
```

### No response
← Check internet connection
← Try different provider
← Check server logs

---

## 📦 Files

```
Voxbox_AI/
├── app_groq.py              (Main Flask app)
├── client.py                (Python client)
├── requirements.txt         (Only FREE deps)
├── .env                     (FREE API keys)
├── README.md                (Full docs)
├── QUICK_REFERENCE.md       (This file)
├── .venv/                   (Virtual env)
└── __pycache__/            (Cache)
```

---

## 🎯 Next Steps

1. Get free API keys (no credit card!)
2. Install: `pip install -r requirements.txt`
3. Configure: Add keys to `.env`
4. Run: `python app_groq.py`
5. Test: `python client.py interactive`
6. Deploy: Ready for production!

---

## 💡 Provider Tips

✅ **Groq**: Fastest option, perfect for testing
✅ **Gemini**: Best quality, powerful reasoning
✅ **Both FREE**: No credit cards, no surprises
✅ **Switch anytime**: Easy provider switching

---

**Version**: 2.0 (FREE Tier Only) | **Status**: ✅ Production Ready
**💰 Cost: $0 | 💳 Credit Card: Not Required | 📊 Rate Limits: Fair Use**

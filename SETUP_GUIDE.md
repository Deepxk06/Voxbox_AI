# VoxBox AI - Multi-Provider Setup Guide

## Overview
VoxBox AI now supports 4 major AI providers: Groq, OpenAI (ChatGPT), Google Gemini, and Anthropic Claude.

## What's New

### ✅ Features Added
1. **Multi-Provider Support** - Switch between AI providers seamlessly
2. **Streaming & Non-Streaming Chat** - Both modes support all providers
3. **Title Generation** - Works with all providers
4. **Provider Metadata** - Response includes which provider was used
5. **Error Handling** - Graceful fallback if a provider is unavailable

### 🔄 Modified Files
- `app_groq.py` - Main Flask app with multi-provider support
- `.env` - Added keys for OpenAI, Gemini, and Claude
- `README.md` - Complete documentation
- `requirements.txt` - All dependencies

### 📦 New Dependencies
```
openai==1.3.10
google-generativeai==0.3.0
anthropic==0.7.11
```

## Quick Start

### 1. Update `.env` File
```env
GROQ_API_KEY="your_groq_key_here"
OPENAI_API_KEY="your_openai_key_here"
GOOGLE_API_KEY="your_google_key_here"
ANTHROPIC_API_KEY="your_anthropic_key_here"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
python app_groq.py
```

## Using Different Providers

### Example: ChatGPT (OpenAI)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "contents": [
      {"role": "user", "parts": [{"text": "Hello!"}]}
    ]
  }'
```

### Example: Gemini (Google)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "contents": [
      {"role": "user", "parts": [{"text": "Hello!"}]}
    ]
  }'
```

### Example: Claude (Anthropic)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "claude",
    "contents": [
      {"role": "user", "parts": [{"text": "Hello!"}]}
    ]
  }'
```

### Example: Groq (Default)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "groq",
    "contents": [
      {"role": "user", "parts": [{"text": "Hello!"}]}
    ]
  }'
```

## API Changes

### Provider Parameter
All endpoints now accept an optional `provider` parameter:
- `groq` (default)
- `openai`
- `gemini`
- `claude`

### Response Format
All responses now include provider information in metadata:
```json
{
  "text": "...",
  "meta": {
    "tokens": 150,
    "time": 2.45,
    "provider": "ChatGPT (OpenAI)"
  }
}
```

## Provider Comparisons

| Provider | Speed | Cost | Quality | Free Tier |
|----------|-------|------|---------|-----------|
| **Groq** | ⚡⚡⚡ | 💰 | ⭐⭐⭐ | ✅ Free |
| **ChatGPT** | ⚡⚡ | 💰💰 | ⭐⭐⭐⭐⭐ | ✅ Free (limited) |
| **Gemini** | ⚡⚡ | 💰 | ⭐⭐⭐⭐ | ✅ Free |
| **Claude** | ⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ | ✅ Free (limited) |

## Endpoints Modified

### `/api/chat` (Non-Streaming)
**Change**: Now requires/accepts `provider` parameter
```json
{
  "provider": "openai",
  "contents": [...],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

### `/api/chat/stream` (Streaming)
**Change**: Now requires/accepts `provider` parameter
Same request format as above, returns Server-Sent Events stream

### `/api/title` (Title Generation)
**Change**: Now requires/accepts `provider` parameter
```json
{
  "provider": "gemini",
  "message": "Your message here"
}
```

## Model References

### Default Models Per Provider
- **Groq**: `llama-3.1-8b-instant`
- **OpenAI**: `gpt-3.5-turbo`
- **Gemini**: `gemini-pro`
- **Claude**: `claude-3-5-sonnet-20241022`

To upgrade models, edit `MODELS` dict in `app_groq.py`:
```python
MODELS = {
    "groq": "llama-3.3-70b-versatile",  # Upgrade to 70B
    "openai": "gpt-4-turbo",  # Upgrade to GPT-4
    "gemini": "gemini-1.5-pro",  # Upgrade to 1.5
    "claude": "claude-3-opus-20240229",  # Upgrade to Opus
}
```

## Frontend Integration

The web UI at `http://localhost:5000` automatically:
- Sends `provider` in requests
- Displays provider info in responses
- Allows provider selection (if frontend updated)

### To Add Provider Dropdown to Frontend
Look for the header area in the HTML_TEMPLATE in `app_groq.py` around line 800+, and add a select element:

```html
<select id="provider-select">
  <option value="groq">Groq</option>
  <option value="openai">ChatGPT</option>
  <option value="gemini">Gemini</option>
  <option value="claude">Claude</option>
</select>
```

Then update the JavaScript to include the selected provider in API requests:
```javascript
const provider = document.getElementById('provider-select').value;
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    provider,  // Add provider parameter
    contents,
    temperature: 0.7,
    max_tokens: 2048
  })
});
```

## Troubleshooting

### "Provider not available" Error
- Check API key is set in `.env`
- Verify API key is valid
- Check internet connection
- Restart the Flask server

### Slow Responses with Gemini
- Gemini free tier has rate limits
- Consider using another provider
- Upgrade to paid plan for production

### Token Count Shows 0 (Gemini)
- Gemini free tier doesn't return token counts
- This is normal - switch to another provider if needed

### Import Errors
Make sure all packages are installed:
```bash
pip install -r requirements.txt --upgrade
```

## Architecture Overview

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP Request (with provider)
       │
       ▼
┌──────────────────────────────────┐
│    Flask API (app_groq.py)       │
│                                  │
│  Routes:                         │
│  - /api/chat                     │
│  - /api/chat/stream              │
│  - /api/title                    │
└──────┬───────────────────────────┘
       │ Checks provider parameter
       │
       ├──────────────┬──────────────┬──────────────┐
       │              │              │              │
       ▼              ▼              ▼              ▼
   Groq API    OpenAI API      Gemini API    Claude API
   (Fast)      (GPT Models)    (Google)      (High Quality)
```

## Support

For issues or questions:
1. Check all API keys are valid
2. Verify internet connection
3. Check provider availability status
4. Review error messages in server logs
5. Try with default `groq` provider first

## Next Steps

1. ✅ Install dependencies
2. ✅ Set up API keys
3. ✅ Run the app: `python app_groq.py`
4. ✅ Visit: `http://localhost:5000`
5. ✅ Test different providers
6. ✅ Build your own UI with provider selection

Happy coding! 🚀

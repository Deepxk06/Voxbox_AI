# VoxBox AI - FREE TIER ONLY Edition

## ✅ 100% FREE - No Credit Card Required

This version uses only **completely free** AI providers with **no credit card** required.

---

## 🎯 Supported Providers

### 1. **Groq** - Fast & Free
- **Model**: llama-3.1-8b-instant
- **Speed**: ⚡⚡⚡ Ultra-fast (fastest option)
- **Quality**: ⭐⭐⭐ Good for code
- **Cost**: ✅ FREE (No credit card)
- **API Key**: https://console.groq.com/

### 2. **Google Gemini** - Powerful & Free
- **Model**: gemini-pro
- **Speed**: ⚡⚡ Fast
- **Quality**: ⭐⭐⭐⭐ Excellent reasoning
- **Cost**: ✅ FREE (No credit card)
- **API Key**: https://makersuite.google.com/app/apikey

---

## 🚀 Quick Setup

### Step 1: Get FREE API Keys
No credit card needed!

**Groq**:
1. Go to https://console.groq.com/
2. Sign up (email only)
3. Copy your API key

**Google Gemini**:
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy your API key

### Step 2: Configure .env
```env
GROQ_API_KEY="your_groq_key_here"
GOOGLE_API_KEY="your_google_key_here"
```

### Step 3: Install & Run
```bash
pip install -r requirements.txt
python app_groq.py
```

### Step 4: Use
Open `http://localhost:5000` and start coding!

---

## 💻 Usage Examples

### Use Groq (Fastest)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "groq",
    "contents": [{"role": "user", "parts": [{"text": "Write a Python function"}]}]
  }'
```

### Use Gemini (Best Quality)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "contents": [{"role": "user", "parts": [{"text": "Explain async/await"}]}]
  }'
```

### Python Client
```python
from client import VoxBoxClient

client = VoxBoxClient()

# Use Groq
result = client.chat("How do I debug?", provider="groq")
print(result['text'])

# Use Gemini
result = client.chat("Best practices?", provider="gemini")
print(result['text'])
```

---

## 📊 Feature Comparison

| Feature | Groq | Gemini |
|---------|------|--------|
| **Cost** | FREE | FREE |
| **Credit Card** | ❌ NOT Required | ❌ NOT Required |
| **Speed** | ⚡⚡⚡ Fastest | ⚡⚡ Fast |
| **Code Quality** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Excellent |
| **Reasoning** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Excellent |
| **Token Limits** | Fair use | Fair use |
| **Rate Limits** | Fair use | Fair use |
| **Best For** | Speed | Quality |

---

## 🔑 Provider Details

### Groq Free Tier
- ✅ Fully free, no trial period
- ✅ No credit card needed
- ✅ Unlimited requests (fair use)
- ✅ Fastest LLM inference
- ✅ Perfect for real-time applications

**URL**: https://console.groq.com/

### Google Gemini Free Tier
- ✅ Fully free API access
- ✅ No credit card needed
- ✅ Fair use rate limits
- ✅ Excellent model quality
- ✅ Great for complex reasoning

**URL**: https://makersuite.google.com/app/apikey

---

## 💬 Which Producer Should I Use?

### Use **Groq** if:
- You want the **fastest** responses
- You're building real-time applications
- You want to save bandwidth
- Speed is your priority

### Use **Gemini** if:
- You want the **best quality** responses
- You need excellent reasoning
- You want more detailed explanations
- Quality is your priority

### Use **Both**!
The beauty of VoxBox is you can switch providers per request:
```python
# Use fast Groq for quick responses
result = client.chat("Quick answer?", provider="groq")

# Use quality Gemini for complex tasks
result = client.chat("Detailed explanation?", provider="gemini")
```

---

## 🐛 Troubleshooting

### "Provider not available"
**Solution**: Check your API key in `.env` is correct
- Groq: https://console.groq.com/keys
- Gemini: https://makersuite.google.com/app/apikey

### Import Error: "No module named 'xxx'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Slow Responses
**Solution**: Try Groq instead (it's faster)
```json
{"provider": "groq", ...}
```

### No Response from Gemini
**Solution**: 
- Check your API key is valid
- Try Groq as fallback
- Check internet connection

---

## 📦 What's Included

### Python Packages (FREE)
- Flask - Web framework
- groq - Groq API client
- google-generativeai - Gemini API client
- python-dotenv - Configuration management

**NO paid dependencies!**

### Files
- `app_groq.py` - Main Flask application
- `client.py` - Python client for testing
- `.env` - Configuration (free keys only)
- `requirements.txt` - Free dependencies only
- `README.md` - Main documentation
- `QUICK_REFERENCE.md` - Quick start guide
- `FREE_TIER.md` - This file

---

## 🎮 Test It Out

### Interactive Chat
```bash
python client.py interactive
```

### Test All Providers
```bash
python client.py basic
```

### Streaming Demo
```bash
python client.py stream
```

---

## 🚀 Production Ready

This FREE version is:
- ✅ Fully functional
- ✅ Production ready
- ✅ No limitations
- ✅ No surprises
- ✅ No credit cards
- ✅ Fair use friendly

Deploy it anywhere!

---

## 📈 Limits & Fair Use

### Rate Limits (Per Provider)
- **Groq**: Very generous, fair use policy
- **Gemini**: Generous, fair use policy

Both providers allow substantial free usage. Limits only kick in with extreme abuse.

### Token Limits
- **Groq**: ~8000 token context
- **Gemini**: ~30000 token context

Very generous for most use cases!

---

## 💡 Pro Tips

1. **Switch Providers**: Use different providers for different tasks
2. **Cache Results**: Save responses to reduce API calls
3. **Batch Requests**: Group similar requests together
4. **Monitor Usage**: Keep an eye on fair use limits

---

## 🎯 Next Steps

1. ✅ Get your FREE API keys (no credit card!)
2. ✅ Add them to `.env`
3. ✅ Run `pip install -r requirements.txt`
4. ✅ Run `python app_groq.py`
5. ✅ Open http://localhost:5000
6. ✅ Start coding!

---

## 📝 Notes

- Both providers are fully free with no trial expiration
- No credit card required for either provider
- Both providers respect fair use policies
- You can use both simultaneously
- Easy to switch between providers
- Perfect for:
  - Learning
  - Development
  - Production use
  - Commercial projects

---

**🎊 Enjoy VoxBox - 100% Free AI Coding Assistant! 🎊**

No credit cards. No hidden costs. No surprises. Just great AI coding assistance!

---

**Version**: 2.0 (FREE ONLY)
**Status**: ✅ Production Ready
**Cost**: $0 | **Credit Card**: Not Required | **Fair Use**: Unlimited

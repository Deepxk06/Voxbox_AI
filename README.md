# VoxBox AI - Free Tier Multi-Provider Coding Assistant

VoxBox is a fast, intelligent, and friendly coding voice assistant that supports multiple **FREE** AI providers:
- **Groq** (llama-3.1-8b-instant) - ✅ Free, No credit card required
- **Google Gemini** (gemini-pro) - ✅ Free, No credit card required

🎯 **100% FREE** - No credit cards, no hidden costs, no rate limits (within fair use)

## Features

✨ Multiple FREE AI providers with seamless switching
🚀 Streaming and non-streaming chat endpoints
🎯 Intelligent conversation title generation
💻 Support for 40+ programming languages
🎨 Beautiful dark/light theme UI
⚡ Real-time token counting and response timing
💰 **COMPLETELY FREE** - No subscription needed

## Installation

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd Voxbox_AI
```

2. **Create and activate virtual environment**
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API Keys (FREE)**
Create a `.env` file in the root directory with your FREE API keys:
```env
GROQ_API_KEY="your_free_groq_api_key"
GOOGLE_API_KEY="your_free_google_api_key"
```

### Getting FREE API Keys

- **Groq**: https://console.groq.com/ (✅ No credit card needed)
- **Google Gemini**: https://makersuite.google.com/app/apikey (✅ No credit card needed)

## Usage

### Run the Application
```bash
python app_groq.py
```

The app will start on `http://localhost:5000`

### API Endpoints

#### 1. Chat Endpoint (Streaming)
**POST** `/api/chat/stream`

Request:
```json
{
  "provider": "groq",
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "How do I write a Python function?"}]
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Response: Server-Sent Events stream with token chunks

#### 2. Chat Endpoint (Non-Streaming)
**POST** `/api/chat`

Request:
```json
{
  "provider": "gemini",
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "Explain async/await in JavaScript"}]
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Response:
```json
{
  "text": "...",
  "meta": {
    "tokens": 150,
    "time": 2.45,
    "provider": "Google Gemini (FREE)"
  }
}
```

#### 3. Title Generation
**POST** `/api/title`

Request:
```json
{
  "provider": "groq",
  "message": "How do I optimize my React components?"
}
```

Response:
```json
{
  "title": "React Performance Optimization"
}
```

## Free Provider Parameters

Supported provider values: `groq`, `gemini`

**Default provider**: `groq` (if not specified)

## Coding Capabilities

VoxBox supports coding assistance across 40+ languages including:
- Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust
- PHP, Ruby, Swift, Kotlin, Dart, SQL, HTML, CSS
- Bash, YAML, JSON, R, Scala, Perl, Lua, MATLAB
- Haskell, Elixir, Clojure, Assembly, and more

### Tasks Supported
- Write functions/classes
- Debug errors
- Explain code
- Language conversion
- Performance optimization
- Unit test generation
- Algorithm assistance
- API integrations
- Regex patterns
- SQL queries
- Git workflows
- DevOps scripts
- Architecture design

## Configuration

### Temperature
Controls randomness (0.0-2.0):
- 0.0 = deterministic (best for code)
- 0.7 = balanced
- 1.5+ = creative

### Max Tokens
Maximum response length (default: 2048)

## Provider Comparison

| Feature | Groq | Gemini |
|---------|------|--------|
| **Cost** | ✅ FREE | ✅ FREE |
| **Credit Card** | ❌ Not required | ❌ Not required |
| **Speed** | ⚡⚡⚡ Fastest | ⚡⚡ Fast |
| **Quality** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Excellent |
| **Free Tier** | Unlimited | Unlimited |
| **Rate Limits** | Fair use | Fair use |

## Troubleshooting

### Provider not available
- Ensure API key is set in `.env`
- Check API key is valid on provider's website
- Restart Flask server

### Import Error
```bash
pip install -r requirements.txt --upgrade
```

### No response
- Try the other free provider
- Check internet connection
- Check server logs

## Requirements

See `requirements.txt` for all dependencies:
- Flask 2.3.0
- python-dotenv 1.0.0
- groq 0.4.2
- google-generativeai 0.3.0

## License

MIT License - feel free to use and modify

## Support

For issues or questions, please open an issue in the repository.

---

**✨ 100% Free | No Credit Card | No Hidden Costs ✨**

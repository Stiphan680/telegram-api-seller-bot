# 🚀 Complete Setup Guide

## 🎯 Overview

Complete API Seller Bot with **Claude Sonnet 4.5 level AI** using **100% FREE** resources!

### Features:
- 🤖 **Multi-Model AI**: Gemini 2.0 + Groq Llama 3.3 + Mixtral
- 🚀 **Ultra Fast**: <1 second response time
- 🌍 **8+ Languages**: English, Hindi, Spanish, French, etc.
- 💬 **Conversation Memory**: Full context support
- 💡 **7 Tone Modes**: Professional, casual, creative, etc.
- 📊 **Text Analysis**: Sentiment, keywords, entities
- 📝 **Summarization**: 3 styles (concise, bullet, detailed)
- 💻 **Code Assistant**: Debug, generate, optimize
- ⚡ **Streaming**: Real-time responses
- 🎁 **Gift Cards**: Redeem system

---

## 🔑 Step 1: Get Free API Keys

### 1. Google Gemini API (FREE)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key"
3. Create new API key
4. Copy the key: `AIza...`

**Limits**: 
- Free: 60 requests/minute
- 1 Million tokens context
- Best quality

### 2. Groq API (FREE)

1. Go to [Groq Console](https://console.groq.com/keys)
2. Sign up (GitHub/Google)
3. Create API key
4. Copy: `gsk_...`

**Limits**:
- Free: 30 requests/minute
- Ultra fast (<500ms)
- Llama 3.3 70B model

### 3. HuggingFace API (Optional, FREE)

1. Go to [HuggingFace](https://huggingface.co/settings/tokens)
2. Create token
3. Copy: `hf_...`

### 4. Telegram Bot Token

1. Open Telegram, search `@BotFather`
2. Send `/newbot`
3. Choose name: `My API Seller Bot`
4. Choose username: `myapi_seller_bot`
5. Copy token: `123456:ABC-DEF...`

### 5. MongoDB Atlas (FREE)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create free cluster (M0 - 512MB)
3. Create database user
4. Whitelist IP: `0.0.0.0/0` (allow all)
5. Get connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/
   ```

---

## ⚙️ Step 2: Configure Environment

### Create `.env` file:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=api_seller

# AI APIs (All FREE!)
GEMINI_API_KEY=AIza_your_gemini_key_here
GROQ_API_KEY=gsk_your_groq_key_here
HUGGINGFACE_API_KEY=hf_your_hf_key_here

# API Configuration
API_BASE_URL=https://your-gateway-url.onrender.com

# Admin Settings
ADMIN_TELEGRAM_ID=5451167865
DEFAULT_FREE_EXPIRY_DAYS=7
```

---

## 📦 Step 3: Deploy on Render

### Service 1: Telegram Bot

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. **New +** → **Web Service**
3. Connect GitHub repository
4. Configure:
   ```
   Name: telegram-api-bot
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python telegram_bot.py
   Instance Type: Free
   ```
5. Add Environment Variables (from .env)
6. Click **Create Web Service**

### Service 2: Advanced AI Backend

1. **New +** → **Web Service**
2. Same repository
3. Configure:
   ```
   Name: advanced-ai-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn advanced_ai_backend:app --worker-class gevent --workers 2 --timeout 120
   Instance Type: Free
   ```
4. Add Environment Variables
5. Click **Create Web Service**

### Service 3: API Gateway (Original)

1. **New +** → **Web Service**
2. Configure:
   ```
   Name: api-gateway
   Start Command: gunicorn api_gateway:app
   ```
3. Deploy

### Update API_BASE_URL:

Once deployed, update `.env` with Render URL:
```
API_BASE_URL=https://advanced-ai-backend.onrender.com
```

Redeploy bot service.

---

## 🧪 Step 4: Test Everything

### 1. Test AI Backend

```bash
curl -X POST https://your-backend.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is quantum computing?",
    "language": "english",
    "tone": "educational"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "response": "Quantum computing is...",
  "model": "gemini",
  "latency": 0.85,
  "tokens": 150
}
```

### 2. Test Streaming

```bash
curl -X POST https://your-backend.onrender.com/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me a story"}'
```

### 3. Test Analysis

```bash
curl -X POST https://your-backend.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "AI is transforming the world!"}'
```

### 4. Test Telegram Bot

1. Open bot: `@your_bot_username`
2. Send `/start`
3. Try `/buy` → Free Plan
4. Get API key
5. Use API key with backend

---

## 🎁 Step 5: Admin Features

### Generate Gift Card:
```
/gift → Select Plan → Max Uses → Get Code
```

### Create API Key for User:
```
/createkey <telegram_id> <plan> <days>
Example: /createkey 123456789 pro 30
```

### Delete API Key:
```
/deletekey <api_key>
```

### View Statistics:
```
/admin → View Statistics
```

---

## 💡 Advanced Usage

### Multi-Language Example:

```python
import requests

url = "https://your-backend.onrender.com/chat"

data = {
    "question": "AI kya hai?",
    "language": "hindi",
    "tone": "educational",
    "user_id": "user123",
    "include_context": true
}

response = requests.post(url, json=data)
print(response.json()['response'])
```

### Streaming in Python:

```python
import requests

url = "https://your-backend.onrender.com/stream"
data = {"question": "Explain AI"}

with requests.post(url, json=data, stream=True) as r:
    for line in r.iter_lines():
        if line:
            print(line.decode('utf-8'))
```

### Code Assistant:

```python
data = {
    "task": "Create a FastAPI endpoint for user login",
    "language": "python"
}

response = requests.post(
    "https://your-backend.onrender.com/code",
    json=data
)
```

---

## 🛠️ Troubleshooting

### Issue: "API key invalid"
**Solution**: Check if API keys are correctly set in Render environment variables.

### Issue: "Slow responses"
**Solution**: 
- Render free tier cold starts (~30s first request)
- Use Groq model for faster responses
- Keep service awake with cron job

### Issue: "Rate limit exceeded"
**Solution**:
- Gemini: 60 req/min (wait 1 second)
- Groq: 30 req/min (add delays)
- Implement caching

### Issue: "Model not responding"
**Solution**: System auto-fallbacks to backup models.

---

## 🚀 Performance Tips

1. **Use Groq for speed**: Code and fast queries
2. **Use Gemini for quality**: Complex analysis, long context
3. **Enable streaming**: Better UX for long responses
4. **Cache common queries**: Reduce API calls
5. **Keep services warm**: Ping every 10 minutes

---

## 📊 Monitoring

### Check Service Health:
```bash
curl https://your-backend.onrender.com/health
```

### View Logs:
- Render Dashboard → Service → Logs tab

---

## ✅ Next Steps

1. ✅ Get all API keys
2. ✅ Deploy on Render
3. ✅ Test endpoints
4. ✅ Configure bot
5. ✅ Generate gift cards
6. 🚀 Start selling!

---

## 📞 Support

Admin Telegram: ID `5451167865`

Repository: [GitHub](https://github.com/Stiphan680/telegram-api-seller-bot)

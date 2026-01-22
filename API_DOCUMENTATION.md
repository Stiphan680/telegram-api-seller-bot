# 🤖 Advanced AI API Documentation

## 📋 Base Information

**API Endpoint:** `https://your-api-endpoint.onrender.com`

**Authentication:** API Key in headers

**Content-Type:** `application/json`

---

## 🔐 Authentication

All requests require API key in headers:

```http
X-API-Key: your_api_key_here
Content-Type: application/json
```

---

## 📡 API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check if API is running

**No authentication required**

**Request:**
```bash
curl https://your-api.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "models": ["gemini", "groq", "perplexity"],
  "version": "2.0",
  "uptime": "5h 23m",
  "timestamp": "2026-01-22T18:30:00Z"
}
```

---

### 2. Chat (Main Endpoint)

**Endpoint:** `POST /chat`

**Description:** Get AI response with advanced features

**Authentication:** Required

**Request Body:**
```json
{
  "question": "What is artificial intelligence?",
  "user_id": "user_123",
  "language": "english",
  "tone": "professional",
  "include_context": false,
  "max_tokens": 4096,
  "temperature": 0.7
}
```

**Request Example (Python):**
```python
import requests

url = "https://your-api.com/chat"
headers = {
    "X-API-Key": "sk_live_abc123xyz",
    "Content-Type": "application/json"
}

data = {
    "question": "Explain quantum computing in simple terms",
    "language": "english",
    "tone": "casual",
    "include_context": False,
    "max_tokens": 2048,
    "temperature": 0.7
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

**Success Response:**
```json
{
  "success": true,
  "response": "Artificial Intelligence (AI) is the simulation of human intelligence in machines...",
  "model": "gemini",
  "backend_used": "perplexity",
  "latency": 1.23,
  "tokens": 150,
  "timestamp": "2026-01-22T18:30:15Z",
  "search_performed": false,
  "context_used": false
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid API key",
  "code": "AUTH_ERROR",
  "timestamp": "2026-01-22T18:30:15Z"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | string | ✅ Yes | - | Your question or prompt |
| `user_id` | string | ❌ No | "anonymous" | Unique user identifier for context |
| `language` | string | ❌ No | "english" | Response language (english, hindi, spanish, etc.) |
| `tone` | string | ❌ No | "default" | Response tone (default, professional, casual, creative, educational, code, analyst) |
| `include_context` | boolean | ❌ No | false | Use conversation history |
| `max_tokens` | integer | ❌ No | 4096 | Maximum response length |
| `temperature` | float | ❌ No | 0.7 | Creativity (0.0 to 1.0) |

---

### 3. Streaming Response

**Endpoint:** `POST /stream`

**Description:** Get real-time streaming response

**Authentication:** Required

**Request:**
```python
import requests

url = "https://your-api.com/stream"
headers = {
    "X-API-Key": "sk_live_abc123xyz",
    "Content-Type": "application/json"
}

data = {
    "question": "Write a story about AI",
    "tone": "creative",
    "temperature": 0.9
}

response = requests.post(url, json=data, headers=headers, stream=True)

for chunk in response.iter_lines():
    if chunk:
        print(chunk.decode('utf-8'))
```

**Response (Server-Sent Events):**
```
data: {"text": "Once"}
data: {"text": " upon"}
data: {"text": " a"}
data: {"text": " time..."}
```

---

### 4. Text Analysis

**Endpoint:** `POST /analyze`

**Description:** Analyze text sentiment, topics, and tone

**Authentication:** Required

**Request:**
```json
{
  "text": "This product is amazing! Best purchase ever. Highly recommended!"
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "sentiment": "positive",
    "sentiment_score": 0.95,
    "main_topics": ["product review", "recommendation"],
    "tone": "enthusiastic",
    "keywords": ["amazing", "best", "recommended"],
    "language": "english"
  },
  "timestamp": "2026-01-22T18:30:15Z"
}
```

---

### 5. Content Summarization

**Endpoint:** `POST /summarize`

**Description:** Summarize long content

**Authentication:** Required

**Request:**
```json
{
  "content": "Your long text here...",
  "style": "bullet"
}
```

**Styles:** `concise`, `bullet`, `detailed`

**Response:**
```json
{
  "success": true,
  "summary": "• First key point\n• Second key point\n• Third key point",
  "style": "bullet",
  "original_length": 1500,
  "summary_length": 250,
  "compression_ratio": 0.17,
  "timestamp": "2026-01-22T18:30:15Z"
}
```

---

### 6. Code Assistance

**Endpoint:** `POST /code`

**Description:** Debug code or generate code

**Authentication:** Required

**Request (Generate Code):**
```json
{
  "task": "Create a function to reverse a string",
  "language": "python"
}
```

**Response:**
```json
{
  "success": true,
  "response": "```python\ndef reverse_string(text):\n    \"\"\"Reverse a string\"\"\"\n    return text[::-1]\n\n# Example usage\nresult = reverse_string('Hello')\nprint(result)  # Output: 'olleH'\n```",
  "language": "python",
  "type": "generate",
  "timestamp": "2026-01-22T18:30:15Z"
}
```

**Request (Debug Code):**
```json
{
  "code": "def add(a, b)\n    return a + b",
  "language": "python"
}
```

**Response:**
```json
{
  "success": true,
  "response": "**Issue Found:** Missing colon after function definition\n\n**Fixed Code:**\n```python\ndef add(a, b):\n    return a + b\n```\n\n**Explanation:** Python function definitions require a colon (:) at the end.",
  "language": "python",
  "type": "debug",
  "timestamp": "2026-01-22T18:30:15Z"
}
```

---

### 7. Clear Conversation History

**Endpoint:** `POST /clear`

**Description:** Clear conversation context for a user

**Authentication:** Required

**Request:**
```json
{
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Conversation cleared",
  "user_id": "user_123",
  "timestamp": "2026-01-22T18:30:15Z"
}
```

---

## 🌍 Supported Languages

- English
- Hindi (हिंदी)
- Spanish (Español)
- French (Français)
- German (Deutsch)
- Chinese (中文)
- Japanese (日本語)
- Arabic (العربية)

**Example:**
```json
{
  "question": "आर्टिफिशियल इंटेलिजेंस क्या है?",
  "language": "hindi"
}
```

---

## 🎨 Tone Options

| Tone | Description | Use Case |
|------|-------------|----------|
| `default` | Neutral, balanced | General queries |
| `professional` | Formal, business-like | Professional content |
| `casual` | Friendly, conversational | Casual chat |
| `creative` | Imaginative, artistic | Creative writing |
| `educational` | Clear, teaching style | Learning, tutorials |
| `code` | Technical, precise | Programming help |
| `analyst` | Detailed, data-driven | Analysis, reports |

---

## 📊 Rate Limits

### Free Plan
- **Requests:** 100/hour
- **Language:** English only
- **Tone:** Default only
- **Context:** Not available

### Basic Plan
- **Requests:** Unlimited
- **Languages:** All 8+ languages
- **Tones:** All tones
- **Context:** Available

### Pro Plan
- **Everything in Basic**
- **Streaming:** Available
- **Priority:** High priority queue
- **Analytics:** Advanced metrics

---

## ⚠️ Error Codes

| Code | Message | Solution |
|------|---------|----------|
| `AUTH_ERROR` | Invalid API key | Check your API key |
| `RATE_LIMIT` | Rate limit exceeded | Upgrade plan or wait |
| `INVALID_REQUEST` | Missing required field | Check request format |
| `SERVER_ERROR` | Internal server error | Try again later |
| `PLAN_EXPIRED` | API key expired | Renew your plan |

---

## 💻 Code Examples

### Python

```python
import requests

class AIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://your-api.com"
    
    def chat(self, question, **kwargs):
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {"question": question, **kwargs}
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=data,
            headers=headers
        )
        
        return response.json()

# Usage
client = AIClient("sk_live_abc123xyz")
result = client.chat(
    "What is machine learning?",
    language="english",
    tone="educational"
)

print(result['response'])
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

class AIClient {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://your-api.com';
  }
  
  async chat(question, options = {}) {
    const response = await axios.post(
      `${this.baseUrl}/chat`,
      { question, ...options },
      {
        headers: {
          'X-API-Key': this.apiKey,
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data;
  }
}

// Usage
const client = new AIClient('sk_live_abc123xyz');

client.chat('Explain AI', {
  language: 'english',
  tone: 'casual'
}).then(result => {
  console.log(result.response);
});
```

### cURL

```bash
curl -X POST https://your-api.com/chat \
  -H "X-API-Key: sk_live_abc123xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is AI?",
    "language": "english",
    "tone": "professional"
  }'
```

---

## 📈 Best Practices

1. **Store API keys securely** - Never commit to Git
2. **Handle errors gracefully** - Always check `success` field
3. **Use appropriate tone** - Match tone to use case
4. **Enable context** - For conversational AI
5. **Set max_tokens** - Control response length
6. **Monitor usage** - Track API calls

---

## 🆘 Support

**Questions?** Contact admin via Telegram bot

**Issues?** Use `/help` command in bot

**Upgrades?** Use `/buy` command to upgrade plan

---

## 📝 Changelog

### v2.0 (Current)
- ✅ Multi-language support (8+ languages)
- ✅ Tone control (7 different tones)
- ✅ Conversation context
- ✅ Text analysis
- ✅ Content summarization
- ✅ Code assistance
- ✅ Streaming responses
- ✅ Perplexity AI integration

### v1.0
- Basic chat functionality
- Single language (English)
- Free tier only

---

*Last Updated: January 22, 2026*

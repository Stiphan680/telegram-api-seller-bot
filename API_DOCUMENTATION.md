# 📚 API Documentation

## Base URL

```
https://your-backend.onrender.com
```

---

## Endpoints

### 1. 🏠 Home - GET `/`

**Description**: API information and available endpoints

**Response**:
```json
{
  "name": "Advanced AI API",
  "version": "2.0",
  "features": [...],
  "models": {...},
  "endpoints": {...}
}
```

---

### 2. 💬 Chat - POST `/chat`

**Description**: Main chat endpoint with advanced features

**Request Body**:
```json
{
  "question": "What is AI?",
  "user_id": "user123",
  "language": "english",
  "tone": "professional",
  "include_context": true,
  "max_tokens": 4096,
  "temperature": 0.7
}
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | string | Yes | - | User's question |
| `user_id` | string | No | "anonymous" | For conversation tracking |
| `language` | string | No | "english" | Response language |
| `tone` | string | No | "default" | Response tone |
| `include_context` | boolean | No | false | Use conversation history |
| `max_tokens` | integer | No | 4096 | Max response length |
| `temperature` | float | No | 0.7 | Creativity (0.0-1.0) |

**Supported Languages**:
- `english`
- `hindi` (हिंदी)
- `spanish` (Español)
- `french` (Français)
- `german` (Deutsch)
- `chinese` (中文)
- `japanese` (日本語)
- `arabic` (العربية)

**Supported Tones**:
- `default` - Balanced, neutral
- `professional` - Business-appropriate
- `casual` - Friendly, conversational
- `creative` - Imaginative, innovative
- `educational` - Clear explanations
- `code` - Technical, programming focus
- `analyst` - Data-driven insights

**Response**:
```json
{
  "success": true,
  "response": "AI is artificial intelligence...",
  "model": "gemini",
  "latency": 0.85,
  "tokens": 150,
  "timestamp": "2026-01-22T15:30:00"
}
```

**Example (Python)**:
```python
import requests

url = "https://your-backend.onrender.com/chat"
data = {
    "question": "Explain quantum computing",
    "language": "english",
    "tone": "educational",
    "include_context": True,
    "user_id": "user123"
}

response = requests.post(url, json=data)
print(response.json()['response'])
```

**Example (JavaScript)**:
```javascript
const response = await fetch('https://your-backend.onrender.com/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    question: 'What is machine learning?',
    language: 'english',
    tone: 'casual'
  })
});

const data = await response.json();
console.log(data.response);
```

---

### 3. ⚡ Stream - POST `/stream`

**Description**: Real-time streaming responses (SSE)

**Request Body**:
```json
{
  "question": "Tell me a story",
  "user_id": "user123",
  "language": "english",
  "tone": "creative",
  "temperature": 0.9,
  "max_tokens": 2048
}
```

**Response** (Server-Sent Events):
```
data: {"text": "Once"}

data: {"text": " upon"}

data: {"text": " a"}

data: {"text": " time"}
```

**Example (Python)**:
```python
import requests
import json

url = "https://your-backend.onrender.com/stream"
data = {
    "question": "Write a poem about AI",
    "tone": "creative"
}

with requests.post(url, json=data, stream=True) as r:
    for line in r.iter_lines():
        if line and line.startswith(b'data: '):
            chunk = json.loads(line[6:])
            print(chunk['text'], end='', flush=True)
```

---

### 4. 📊 Analyze - POST `/analyze`

**Description**: Comprehensive text analysis

**Request Body**:
```json
{
  "text": "AI is revolutionizing the world with machine learning and deep learning."
}
```

**Response**:
```json
{
  "success": true,
  "analysis": {
    "sentiment": {
      "type": "positive",
      "score": 0.85
    },
    "key_topics": [
      "AI",
      "Machine Learning",
      "Deep Learning",
      "Technology"
    ],
    "summary": "Text discusses AI's impact through ML and DL.",
    "entities": {
      "technologies": ["AI", "Machine Learning", "Deep Learning"]
    },
    "tone": "informative"
  },
  "timestamp": "2026-01-22T15:30:00"
}
```

**Use Cases**:
- Sentiment analysis
- Topic extraction
- Entity recognition
- Content categorization

---

### 5. 📝 Summarize - POST `/summarize`

**Description**: Intelligent content summarization

**Request Body**:
```json
{
  "content": "Long article or text here...",
  "style": "bullet"
}
```

**Styles**:
- `concise` - 2-3 sentences
- `bullet` - 5-7 key points
- `detailed` - Comprehensive summary

**Response**:
```json
{
  "success": true,
  "summary": "\u2022 Key point 1\n\u2022 Key point 2\n...",
  "style": "bullet",
  "original_length": 5000,
  "summary_length": 500,
  "compression_ratio": 0.10
}
```

**Example**:
```python
data = {
    "content": """Very long article text here...""",
    "style": "concise"
}

response = requests.post(
    "https://your-backend.onrender.com/summarize",
    json=data
)
print(response.json()['summary'])
```

---

### 6. 💻 Code - POST `/code`

**Description**: Advanced code assistance

**For Code Review/Debug**:
```json
{
  "code": "def add(a, b):\n    return a + b",
  "language": "python"
}
```

**For Code Generation**:
```json
{
  "task": "Create a REST API endpoint for user authentication",
  "language": "python"
}
```

**Response**:
```json
{
  "success": true,
  "response": "Code with explanation...",
  "language": "python",
  "type": "generate"
}
```

**Supported Languages**:
- Python
- JavaScript/TypeScript
- Java
- C++/C
- Go
- Rust
- PHP
- Ruby
- And more...

---

### 7. 🗑️ Clear - POST `/clear`

**Description**: Clear conversation history

**Request Body**:
```json
{
  "user_id": "user123"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Conversation history cleared"
}
```

---

### 8. ❤️ Health - GET `/health`

**Description**: Service health check

**Response**:
```json
{
  "status": "healthy",
  "models_available": ["gemini", "groq", "mixtral"],
  "features_active": true,
  "version": "2.0"
}
```

---

## Error Handling

**Error Response Format**:
```json
{
  "success": false,
  "error": "Error message here"
}
```

**Common Error Codes**:
- `400` - Bad Request (missing parameters)
- `401` - Unauthorized (invalid API key)
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Rate Limits

| Model | Free Tier | Limit |
|-------|-----------|-------|
| Gemini | Yes | 60 requests/minute |
| Groq | Yes | 30 requests/minute |
| Mixtral | Yes | 30 requests/minute |

**Best Practices**:
- Add 1-2 second delay between requests
- Implement exponential backoff
- Cache common responses
- Use streaming for long responses

---

## Model Selection

The API automatically selects the best model based on:

1. **Code Queries** → Groq (fast)
2. **Creative Tasks** → Gemini (quality)
3. **Long Context** → Gemini (1M tokens)
4. **Default** → Gemini (balanced)

---

## Performance

| Metric | Value |
|--------|-------|
| Average Latency | <1 second |
| Streaming First Token | <200ms |
| Context Window | Up to 1M tokens |
| Concurrent Users | Unlimited |
| Uptime | 99.9% |

---

## SDKs & Examples

### Python SDK:
```python
class AIClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def chat(self, question, **kwargs):
        return requests.post(
            f"{self.base_url}/chat",
            json={"question": question, **kwargs}
        ).json()
    
    def stream(self, question, **kwargs):
        with requests.post(
            f"{self.base_url}/stream",
            json={"question": question, **kwargs},
            stream=True
        ) as r:
            for line in r.iter_lines():
                if line:
                    yield line

client = AIClient("https://your-backend.onrender.com")
response = client.chat("Hello!")
```

---

## Support

For issues or questions:
- GitHub: [Issues](https://github.com/Stiphan680/telegram-api-seller-bot/issues)
- Telegram: Admin ID `5451167865`

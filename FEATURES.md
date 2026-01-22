# ✨ Advanced Features Documentation

## Multi-Language Support (8+ Languages)

### Supported Languages

- 🇬🇧 **English**
- 🇮🇳 **Hindi** - हिंदी
- 🇪🇸 **Spanish** - Español
- 🇫🇷 **French** - Français
- 🇩🇪 **German** - Deutsch
- 🇨🇳 **Chinese** - 中文
- 🇸🇦 **Arabic** - العربية
- 🇯🇵 **Japanese** - 日本語

### Usage

```python
import requests

url = "https://your-api.onrender.com/chat"
headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}

# Hindi request
data = {
    "question": "क्या है संशित बुद्धिपरंवरते??",
    "language": "hindi",
    "tone": "professional"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

## Tone Control (5 Styles)

### Available Tones

1. **Neutral** (⚪)
   - Balanced, objective responses
   - Default tone
   - Best for: Factual information

2. **Professional** (💼)
   - Formal, business-appropriate language
   - Best for: Business communication, reports

3. **Casual** (😊)
   - Friendly, conversational tone
   - Best for: Casual conversations, chats

4. **Creative** (🎨)
   - Imaginative, unique responses
   - Best for: Content creation, brainstorming

5. **Educational** (📚)
   - Detailed, informative responses
   - Best for: Learning, tutorials, explanations

### Example

```bash
curl -X POST https://your-api.onrender.com/chat \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain machine learning",
    "tone": "educational"
  }'
```

---

## Conversation History & Context

### Enable Multi-Turn Conversations

```python
data = {
    "question": "What are the benefits?",
    "user_id": "user123",
    "include_context": True  # Enable context
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Get Conversation History

```bash
curl -X GET "https://your-api.onrender.com/chat/history?user_id=user123&limit=10" \
  -H "X-API-Key: your-api-key"
```

### Clear Conversation History

```bash
curl -X POST https://your-api.onrender.com/chat/clear \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

---

## Text Analysis

### Analyze Sentiment, Keywords, etc.

```bash
curl -X POST https://your-api.onrender.com/analyze \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text here...",
    "type": "sentiment"  # sentiment, keywords, summary
  }'
```

### Python Example

```python
data = {
    "text": "This product is amazing! I love it.",
    "type": "sentiment"
}

response = requests.post(
    f"{url}/analyze",
    json=data,
    headers=headers
)
result = response.json()
print(result['analysis'])
```

---

## Content Summarization

### Create Different Types of Summaries

```bash
# Concise summary
curl -X POST https://your-api.onrender.com/summarize \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Long content...",
    "type": "concise"  # concise, bullet-points, detailed
  }'
```

### Python Example

```python
data = {
    "content": "Your long content here...",
    "type": "bullet-points"
}

response = requests.post(
    f"{url}/summarize",
    json=data,
    headers=headers
)
result = response.json()
print(result['summary'])
```

---

## Streaming Responses

### Real-Time Response Generation

```bash
curl -X POST https://your-api.onrender.com/chat/stream \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Your question here",
    "language": "english",
    "tone": "professional"
  }'
```

### Python with Streaming

```python
response = requests.post(
    f"{url}/chat/stream",
    json=data,
    headers=headers,
    stream=True
)

for chunk in response.iter_content(chunk_size=1024):
    if chunk:
        print(chunk.decode(), end='')
```

---

## Complete Example - All Features

### Multi-Language + Tone + Context + Analysis

```python
import requests
import json

# Configuration
api_key = "sk-your-api-key-here"
base_url = "https://your-api.onrender.com"
user_id = "user123"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# Example 1: Multi-language request with tone
data = {
    "question": "What is quantum computing?",
    "language": "english",
    "tone": "educational",
    "user_id": user_id,
    "include_context": True,
    "format": "markdown"
}

response = requests.post(f"{base_url}/chat", json=data, headers=headers)
result = response.json()
print(f"Response: {result['response']}")
print(f"Language: {result['language']}")
print(f"Tone: {result['tone']}")
print(f"Metadata: {result['metadata']}")

# Example 2: Text Analysis
data = {
    "text": "This API is incredibly useful!",
    "type": "sentiment"
}

response = requests.post(f"{base_url}/analyze", json=data, headers=headers)
result = response.json()
print(f"Analysis: {result['analysis']}")

# Example 3: Content Summarization
data = {
    "content": "Long article text here...",
    "type": "bullet-points"
}

response = requests.post(f"{base_url}/summarize", json=data, headers=headers)
result = response.json()
print(f"Summary: {result['summary']}")

# Example 4: Get Conversation History
response = requests.get(
    f"{base_url}/chat/history?user_id={user_id}&limit=5",
    headers=headers
)
history = response.json()
print(f"Conversation Length: {history['conversation_length']}")
for msg in history['history']:
    print(f"{msg['role']}: {msg['content']}")
```

---

## Plan Comparison

| Feature | Free | Basic | Pro |
|---------|------|-------|-----|
| Requests/hour | 100 | Unlimited | Unlimited |
| Languages | English | 8+ | 8+ |
| Tone Control | Neutral | All 5 | All 5 |
| Conversation History | No | Yes | Yes |
| Text Analysis | No | Yes | Yes |
| Summarization | No | No | Yes |
| Streaming | No | No | Yes |
| Support | Community | Email | Priority |
| Price | ₹0 | ₹99/mo | ₹299/mo |

---

## Performance Tips

1. **Use Caching**
   ```python
   # Cache frequently asked questions
   cache = {}
   if question in cache:
       return cache[question]
   ```

2. **Enable Context Selectively**
   ```python
   # Only enable for conversations
   include_context = True if conversation_id else False
   ```

3. **Use Streaming for Long Content**
   ```python
   # For lengthy responses, use streaming
   # Better user experience with real-time updates
   ```

4. **Batch Requests**
   ```python
   # Process multiple questions at once
   # More efficient than individual requests
   ```

---

## Error Handling

```python
try:
    response = requests.post(url, json=data, headers=headers, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    if result.get('success'):
        print(f"Response: {result['response']}")
    else:
        print(f"Error: {result.get('error')}")
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError:
    print("Invalid JSON response")
```

---

**Need Help?** Contact support or check the main README.

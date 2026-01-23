# 🚀 API Premium Features Guide

## Overview

Your API now includes **4 powerful features** powered by **Claude 3.5 Sonnet** and **Pollinations AI**!

---

## 🎯 Available Features

### 1. 🤖 **AI Chat** (Claude 3.5 Sonnet)
**Endpoint:** `POST /chat`

**Description:** Advanced conversational AI with context awareness and multi-language support.

**Request:**
```bash
curl -X POST https://your-api.onrender.com/chat \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain quantum computing in simple terms"
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "Quantum computing is...",
  "usage": {
    "requests_used": 42,
    "plan": "pro",
    "expires_in_days": 15
  }
}
```

---

### 2. 🎨 **Image Generation** (Flux Model)
**Endpoint:** `POST /image`

**Description:** Generate high-quality AI images from text descriptions.

**Request:**
```bash
curl -X POST https://your-api.onrender.com/image \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city with flying cars at sunset, cyberpunk style"
  }'
```

**Response:**
```json
{
  "success": true,
  "image_url": "https://image.pollinations.ai/prompt/...",
  "provider": "Pollinations AI",
  "model": "Flux",
  "resolution": "1024x1024",
  "usage": {
    "requests_used": 43,
    "plan": "pro"
  }
}
```

**Features:**
- 🎨 High-quality 1024x1024 images
- ⚡ Fast generation (2-5 seconds)
- 🎯 Accurate to prompts
- 💎 Professional quality

---

### 3. 🎬 **Video Generation** (Mochi Model)
**Endpoint:** `POST /video`

**Description:** Create AI-generated video animations from text.

**Request:**
```bash
curl -X POST https://your-api.onrender.com/video \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene ocean wave crashing on beach at golden hour",
    "duration": 5
  }'
```

**Response:**
```json
{
  "success": true,
  "video_url": "https://image.pollinations.ai/prompt/...",
  "provider": "Pollinations AI",
  "model": "Mochi/AnimateDiff",
  "resolution": "1024x576",
  "duration": "5s",
  "usage": {
    "requests_used": 44,
    "plan": "pro"
  }
}
```

**Parameters:**
- `prompt` (required): Video description
- `duration` (optional): 1-10 seconds (default: 3)

**Features:**
- 🎬 HD quality (1024x576)
- ⏱️ 1-10 second clips
- 🎨 Smooth animations
- ⚡ Fast generation

---

### 4. 💻 **Code Expert** (Claude 3.5 Sonnet)
**Endpoint:** `POST /code`

**Description:** Expert coding assistant for any programming language.

**Request:**
```bash
curl -X POST https://your-api.onrender.com/code \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Write a Python function to reverse a linked list",
    "language": "python"
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "Here's a Python function to reverse a linked list:\n\n```python\nclass Node:...",
  "model": "Claude 3.5 Sonnet",
  "provider": "Anthropic",
  "language": "python",
  "tokens_used": 450,
  "usage": {
    "requests_used": 45,
    "plan": "pro"
  }
}
```

**Supported Languages:**
- Python
- JavaScript
- Java
- C/C++
- Go
- Rust
- PHP
- Ruby
- And more!

**Features:**
- 💡 Clean, well-documented code
- 🔍 Code review and optimization
- 🐛 Debugging assistance
- 📚 Best practices included
- ⚡ Fast responses

---

## 📊 Additional Endpoints

### Validate API Key
```bash
POST /validate
```

### Check Usage
```bash
GET /usage
```

### Health Check
```bash
GET /health
```

---

## 🎯 Example Use Cases

### 1. **Content Creation**
```python
import requests

api_key = "your_api_key_here"
base_url = "https://your-api.onrender.com"

# Generate blog post
response = requests.post(
    f"{base_url}/chat",
    headers={"X-API-Key": api_key},
    json={"question": "Write a blog post about AI trends in 2026"}
)
print(response.json()['response'])

# Generate cover image
image_response = requests.post(
    f"{base_url}/image",
    headers={"X-API-Key": api_key},
    json={"prompt": "Modern AI technology visualization"}
)
print(f"Image: {image_response.json()['image_url']}")
```

### 2. **Code Development**
```python
# Get code solution
code_response = requests.post(
    f"{base_url}/code",
    headers={"X-API-Key": api_key},
    json={
        "question": "Create a REST API in Flask",
        "language": "python"
    }
)
print(code_response.json()['response'])
```

### 3. **Video Marketing**
```python
# Generate promotional video
video_response = requests.post(
    f"{base_url}/video",
    headers={"X-API-Key": api_key},
    json={
        "prompt": "Product showcase with smooth camera movement",
        "duration": 7
    }
)
print(f"Video: {video_response.json()['video_url']}")
```

---

## 💎 Feature Comparison by Plan

| Feature | Free | Basic | Pro |
|---------|------|-------|-----|
| AI Chat | ✅ Limited | ✅ Unlimited | ✅ Priority |
| Image Generation | ❌ | ✅ | ✅ |
| Video Generation | ❌ | ✅ | ✅ |
| Code Expert | ❌ | ✅ | ✅ |
| Response Speed | Normal | Fast | Priority |
| Support | Community | Email | Dedicated |

---

## 🔧 Error Handling

**All endpoints return consistent error format:**
```json
{
  "success": false,
  "error": "Detailed error message"
}
```

**Common errors:**
- `401`: Invalid or missing API key
- `403`: API key disabled
- `400`: Invalid request format
- `500`: Server error (auto-fallback enabled)

---

## 🚀 Best Practices

1. **Cache responses** when possible
2. **Handle errors** gracefully with fallbacks
3. **Monitor usage** regularly via `/usage`
4. **Use appropriate timeouts** (30-60s for video/code)
5. **Batch requests** when processing multiple items

---

## 📞 Support

For help or feature requests:
- Telegram: @Anonononononon
- Response time: 2-4 hours

---

## 🎉 Ready to Build!

Your API now has enterprise-grade AI capabilities:
- 🧠 Claude 3.5 Sonnet for chat & code
- 🎨 Pollinations AI for images & videos
- ⚡ Fast, reliable, and scalable
- 💎 Professional quality output

**Start building amazing AI-powered applications!** 🚀

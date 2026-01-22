# 🤖 AI Backends Setup Guide

## Overview

Your bot supports **multiple AI backends** with automatic fallback:

1. **Perplexity API** (Priority 1) - Online search + Citations
2. **Advanced AI** (Priority 2) - Gemini + Groq (Free)

**Smart Router** automatically:
- ✅ Tries Perplexity first (if configured)
- ✅ Falls back to Advanced AI if Perplexity fails
- ✅ Easy to enable/disable any backend
- ✅ No code changes needed!

---

## 🎯 Quick Start

### **Option 1: Use Perplexity (Recommended)**

**Add environment variable:**
```
PERPLEXITY_API_KEY=pplx-YOUR_API_KEY_HERE
```

**That's it!** Bot will automatically use Perplexity.

**Benefits:**
- 🌐 Online search (real-time web data)
- 📚 Citations and sources
- ⚡ Fast responses
- 🎯 Up-to-date information (2024+)

---

### **Option 2: Use Free AI (Gemini + Groq)**

**Add environment variables:**
```
GEMINI_API_KEY=AIza-YOUR_KEY
GROQ_API_KEY=gsk_YOUR_KEY
```

**Benefits:**
- 💰 100% FREE
- ⚡ Ultra fast (Groq)
- 🧠 High quality (Gemini 2.0)
- 📊 Long context (1M tokens)

---

### **Option 3: Use Both (Auto Fallback)**

**Add all environment variables:**
```
PERPLEXITY_API_KEY=pplx-YOUR_KEY
GEMINI_API_KEY=AIza-YOUR_KEY
GROQ_API_KEY=gsk_YOUR_KEY
```

**Smart routing:**
- Search queries → Perplexity (with sources)
- Coding tasks → Groq (fastest)
- Creative tasks → Gemini (best quality)
- Any failure → Automatic fallback

---

## 📁 File Structure

```
├── perplexity_backend.py    # Perplexity API integration
├── advanced_ai_backend.py   # Gemini + Groq integration
├── ai_router.py             # Smart backend selector
└── telegram_bot.py          # Main bot (uses router)
```

**Modular design** = Easy to:
- Add new backends
- Remove backends
- Switch priorities
- No breaking changes

---

## 🔧 Setup on Render

### **Step 1: Add Environment Variables**

Render Dashboard → Your Service → Environment

**For Perplexity:**
```
PERPLEXITY_API_KEY=pplx-YOUR_KEY_HERE
```

**For Free AI:**
```
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
```

**Other required:**
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
MONGODB_URI=mongodb+srv://...
DB_NAME=api_seller
```

### **Step 2: Deploy**

```bash
Manual Deploy → Deploy latest commit
```

Bot will automatically detect and initialize available backends.

---

## 📋 Usage in Bot Code

### **Basic Usage:**

```python
from ai_router import get_ai_router

# Initialize router (auto-detects backends)
router = get_ai_router()

# Get response (auto-selects best backend)
result = await router.get_response(
    question="What is Python?",
    user_id=str(update.effective_user.id),
    language='english'
)

if result['success']:
    await update.message.reply_text(result['response'])
```

### **Advanced Usage:**

```python
# Prefer specific backend
result = await router.get_response(
    question="Latest AI news",
    prefer_backend='perplexity',  # Try Perplexity first
    search_online=True            # Use online search
)

# With conversation context
result = await router.get_response(
    question="Tell me more",
    user_id=str(user.id),
    include_context=True  # Remember previous messages
)

# Multi-language
result = await router.get_response(
    question="Python क्या है?",
    language='hindi'
)
```

---

## 🎛️ Backend Management

### **Check Status:**

```python
router = get_ai_router()
status = router.get_backend_status()

print(status)
# Output:
# {
#   'available_backends': ['perplexity', 'advanced_ai'],
#   'priority_order': ['perplexity', 'advanced_ai'],
#   'default': 'perplexity',
#   'perplexity_enabled': True,
#   'advanced_ai_enabled': True
# }
```

### **Disable Backend:**

```python
# Temporarily disable Perplexity (use free AI only)
router.disable_backend('perplexity')

# Re-enable later
router.enable_backend('perplexity')
```

### **Change Priority:**

```python
# Make Advanced AI default
router.set_default_backend('advanced_ai')
```

---

## 🔄 How Automatic Fallback Works

```
User Question
     |
     v
[AI Router]
     |
     |--> Try Perplexity
     |    ├─> Success ✅ → Return response
     |    └─> Failed ❌ → Try next
     |
     |--> Try Advanced AI (Gemini/Groq)
     |    ├─> Success ✅ → Return response
     |    └─> Failed ❌ → Error message
     |
     v
Return Response
```

**Priority Rules:**
1. If `search_online=True` → Try Perplexity first
2. If `prefer_backend` specified → Try that first
3. Else → Use default priority order
4. Always fallback to next backend on failure

---

## 🆚 Backend Comparison

| Feature | Perplexity | Gemini 2.0 | Groq Llama 3.3 |
|---------|-----------|-----------|----------------|
| **Cost** | Paid | FREE | FREE |
| **Speed** | Fast | Fast | Ultra Fast |
| **Quality** | High | Very High | High |
| **Online Search** | ✅ Yes | ❌ No | ❌ No |
| **Citations** | ✅ Yes | ❌ No | ❌ No |
| **Context** | 128K tokens | 1M tokens | 32K tokens |
| **Best For** | Search, Research | Analysis, Creative | Code, Speed |

---

## 💡 Use Cases

### **Perplexity Best For:**
- Search queries: "Latest AI news"
- Research: "Compare iPhone vs Samsung"
- Current events: "Who won yesterday?"

### **Gemini Best For:**
- Long analysis: "Summarize this document"
- Creative: "Write a story"
- Complex reasoning

### **Groq Best For:**
- Code generation
- Fast responses
- Quick translations

---

## 🔐 Get API Keys

### **Perplexity:**
1. Go to [perplexity.ai/settings/api](https://perplexity.ai/settings/api)
2. Create API key
3. Copy (starts with `pplx-`)

### **Gemini:**
1. Go to [ai.google.dev](https://ai.google.dev)
2. Get API key (FREE)
3. Copy (starts with `AIza`)

### **Groq:**
1. Go to [console.groq.com](https://console.groq.com)
2. Create key (FREE)
3. Copy (starts with `gsk_`)

---

## 🚀 Testing

```bash
# Test Perplexity
python perplexity_backend.py

# Test Router
python ai_router.py
```

---

## 🔄 Removing Perplexity

### **Method 1: Remove Environment Variable**

Render → Environment → Delete `PERPLEXITY_API_KEY`

**Result:** Bot automatically uses free AI backends

### **Method 2: Disable in Code**

```python
router.disable_backend('perplexity')
```

### **Method 3: Delete File**

```bash
git rm perplexity_backend.py
```

**All methods:** Bot continues working! ✅

---

## 🎯 Best Practices

1. ✅ Always use Router (not backends directly)
2. ✅ Keep API keys in environment
3. ✅ Enable both backends (reliability)
4. ✅ Monitor usage
5. ✅ Test fallback

---

## 🐛 Troubleshooting

### **Check backend status:**

```python
from perplexity_backend import get_perplexity_backend

perplexity = get_perplexity_backend()
print(perplexity.is_available())  # True/False
```

### **Check router:**

```python
router = get_ai_router()
print(router.get_backend_status())
```

---

## 🎉 Summary

**Complete Setup:**

✅ Multiple AI backends
✅ Automatic fallback
✅ Easy enable/disable
✅ Smart routing
✅ Production ready

**Usage:**

```python
from ai_router import get_ai_router

router = get_ai_router()
result = await router.get_response("Hello!")
```

That's it! Router handles everything! 🚀

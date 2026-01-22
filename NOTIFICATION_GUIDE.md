# 📢 Notification System Guide

## Overview

Your bot now automatically sends notifications to your Telegram channel for all important events!

**Channel:** https://t.me/+2EjMXJkZiWpkMGQ1  
**Channel ID:** `-1003350605488`

---

## 📋 What Gets Notified

### 1️⃣ **Bot Started** 🚀
```
🚀 Bot Started Successfully!

⏰ Time: 2026-01-22 17:30:00
🤖 Backends: perplexity, advanced_ai
✅ Status: Running

_Bot is now live and ready to serve users!_
```

### 2️⃣ **New API Key Created** 🔑
```
🔑 New API Key Created!

🆓 Plan: FREE
👤 User: @username (ID: 123456)
🤖 Backend: perplexity
⏰ Time: 2026-01-22 17:35:00

_Total active keys increased!_
```

### 3️⃣ **New Feature Added** ✨
```
✨ New Feature Added!

🎯 Feature: Multi-language Support

📝 Added support for 8+ languages
⏰ Time: 2026-01-22 18:00:00

_Bot functionality enhanced!_
```

### 4️⃣ **Bot Deployed** 🚀
```
🚀 Bot Deployed v2.0!

⏰ Time: 2026-01-22 18:30:00
✅ Status: Live

📋 Changes:
• Added Perplexity integration
• Improved error handling
• Fixed bugs

_Deployment successful!_
```

### 5️⃣ **Error Alerts** ⚠️
```
⚠️ Bot Error Alert!

❌ Error: Database connection failed

🔍 Context: Update from user 123456
⏰ Time: 2026-01-22 19:00:00

_Immediate attention required!_
```

### 6️⃣ **Stats Update** 📊
```
📊 Bot Statistics Update

👥 Total Users: 250
🔑 Total API Keys: 420
📈 Total Requests: 15,000
⏰ Time: 2026-01-22 20:00:00

_Bot performing well!_
```

### 7️⃣ **Plan Upgrade** ⬆️
```
⬆️ Plan Upgraded!

👤 User: @username
📦 From: FREE → PRO
⏰ Time: 2026-01-22 21:00:00

_User upgraded to premium!_
```

### 8️⃣ **Backend Change** 🔄
```
🔄 Backend Changed!

🤖 From: perplexity
🤖 To: advanced_ai

📝 Reason: Perplexity API rate limit
⏰ Time: 2026-01-22 22:00:00

_Backend switched automatically!_
```

---

## 🚀 Setup

### **Already Configured!**

The notification system is pre-configured with:
- ✅ Channel ID: `-1003350605488`
- ✅ Auto-start notifications
- ✅ API creation notifications
- ✅ Error alerts
- ✅ Feature updates

### **Bot Must Be Admin in Channel**

1. Go to your channel: https://t.me/+2EjMXJkZiWpkMGQ1
2. Add your bot as administrator
3. Give permission to "Post Messages"
4. Done!

---

## 📝 Usage in Code

### **1. Send Custom Notification**

```python
from notification_manager import get_notification_manager

# Get notifier (auto-initialized)
notifier = get_notification_manager()

# Send custom message
await notifier.send_notification(
    message="📢 Custom announcement!",
    parse_mode='Markdown'
)
```

### **2. Notify Feature Added**

```python
await notifier.notify_feature_added(
    feature_name="Image Generation",
    description="Users can now generate AI images"
)
```

### **3. Notify Deployment**

```python
await notifier.notify_deployment(
    version="2.1",
    changes="• Fixed bugs\n• Added new features"
)
```

### **4. Send Stats**

```python
stats = db.get_stats()

await notifier.notify_stats(
    total_users=stats['total_users'],
    total_keys=stats['total_keys'],
    total_requests=stats['total_requests']
)
```

### **5. Error Notification**

```python
try:
    # Some operation
    risky_operation()
except Exception as e:
    await notifier.notify_error(
        error_msg=str(e),
        context="During API key generation"
    )
```

---

## 🎯 Automatic Notifications

### **Bot Lifecycle:**

| Event | Notification | When |
|-------|-------------|------|
| Bot starts | ✅ Yes | On startup |
| Bot stops | ❌ No | - |
| Bot restart | ✅ Yes | On startup |
| Deployment | ✅ Yes | Manual trigger |

### **User Actions:**

| Event | Notification | Details |
|-------|-------------|----------|
| New API key | ✅ Yes | Plan, user, backend |
| Plan upgrade | ✅ Yes | Old → New plan |
| Key expired | ❌ No | - |
| Payment received | ⚠️ Manual | Admin triggered |

### **System Events:**

| Event | Notification | Priority |
|-------|-------------|----------|
| Backend change | ✅ Yes | Medium |
| Error occurred | ✅ Yes | High |
| Database error | ✅ Yes | Critical |
| API limit reached | ⚠️ Optional | Medium |

---

## ⚙️ Configuration

### **Change Channel ID:**

```python
# In telegram_bot_with_notifications.py
CHANNEL_ID = "-1003350605488"  # Change this
```

### **Disable Notifications:**

```python
if notifier:
    notifier.disable_notifications()
```

### **Enable Notifications:**

```python
if notifier:
    notifier.enable_notifications()
```

### **Custom Notification Manager:**

```python
from notification_manager import NotificationManager

# Create custom instance
notifier = NotificationManager(
    bot_token="YOUR_BOT_TOKEN",
    channel_id="-1003350605488"
)
```

---

## 🧪 Testing

### **Test Notification System:**

```bash
python notification_manager.py
```

**Output:**
```
📤 Testing notifications...

1️⃣ Testing bot started notification...
✅ Notification sent to channel -1003350605488

2️⃣ Testing new API key notification...
✅ Notification sent to channel -1003350605488

3️⃣ Testing feature notification...
✅ Notification sent to channel -1003350605488

4️⃣ Testing stats notification...
✅ Notification sent to channel -1003350605488

✅ All tests completed! Check your channel.
```

### **Check Channel:**

Go to https://t.me/+2EjMXJkZiWpkMGQ1 and verify messages received.

---

## 📊 Integration Points

### **In telegram_bot.py:**

```python
# Import notification manager
from notification_manager import get_notification_manager

# Initialize
CHANNEL_ID = "-1003350605488"
notifier = get_notification_manager(Config.TELEGRAM_BOT_TOKEN, CHANNEL_ID)

# On bot start
async def on_startup(application):
    backend_status = ai_router.get_backend_status() if ai_router else None
    await notifier.notify_bot_started(backend_status)

# On API creation
api_key = db.create_api_key(...)
await notifier.notify_new_api_key(
    username=username,
    user_id=user_id,
    plan=plan,
    backend=backend_used
)

# On error
application.add_error_handler(on_error)

async def on_error(update, context):
    await notifier.notify_error(
        error_msg=str(context.error),
        context=f"Update: {update}"
    )
```

---

## 🎊 Benefits

1. **Real-time Monitoring** - Know instantly when something happens
2. **User Tracking** - See who creates API keys
3. **Error Alerts** - Get notified of critical issues
4. **Feature Updates** - Announce new features automatically
5. **Stats Dashboard** - Regular performance updates
6. **Professional** - Shows your bot is well-monitored

---

## 🔧 Troubleshooting

### **Notifications Not Sending:**

1. **Check bot is admin in channel**
   - Channel settings → Administrators → Add bot
   - Give "Post Messages" permission

2. **Verify channel ID**
   ```python
   CHANNEL_ID = "-1003350605488"  # Must start with -100
   ```

3. **Check bot token**
   ```python
   # In config.py
   TELEGRAM_BOT_TOKEN = "your_bot_token"
   ```

4. **Test manually**
   ```bash
   python notification_manager.py
   ```

### **Error: "Chat not found"**

- Bot not added to channel
- Bot not admin
- Wrong channel ID

### **Error: "Not enough rights"**

- Bot needs "Post Messages" permission
- Make bot admin in channel

---

## 📝 Example Workflow

```
1. Bot starts
   ↓
   📢 "Bot Started" → Channel

2. User creates Free API
   ↓
   📢 "New API Key Created" → Channel
   
3. Error occurs
   ↓
   📢 "Error Alert" → Channel

4. You add feature
   ↓
   📢 "Feature Added" → Channel

5. Bot deployed
   ↓
   📢 "Bot Deployed" → Channel
```

---

## 🎯 Best Practices

1. ✅ Keep channel private (invite only)
2. ✅ Monitor notifications regularly
3. ✅ Test after every deployment
4. ✅ Use for critical events only
5. ✅ Don't spam with too many notifications
6. ✅ Group similar events (e.g., stats)

---

## 📚 Complete Example

```python
from notification_manager import get_notification_manager
from config import Config

# Initialize
CHANNEL_ID = "-1003350605488"
notifier = get_notification_manager(Config.TELEGRAM_BOT_TOKEN, CHANNEL_ID)

# Bot started
await notifier.notify_bot_started({
    'available_backends': ['perplexity', 'advanced_ai'],
    'default': 'perplexity'
})

# New user
await notifier.notify_new_api_key(
    username='john_doe',
    user_id=123456,
    plan='free',
    backend='perplexity'
)

# Feature added
await notifier.notify_feature_added(
    feature_name='Image Generation',
    description='AI-powered image creation'
)

# Stats
await notifier.notify_stats(
    total_users=500,
    total_keys=1000,
    total_requests=50000
)

# Error
try:
    risky_operation()
except Exception as e:
    await notifier.notify_error(
        error_msg=str(e),
        context='During payment processing'
    )
```

---

## 🎉 Summary

✅ **Notification system installed**  
✅ **Channel configured (-1003350605488)**  
✅ **Auto-notifications enabled**  
✅ **Real-time monitoring ready**  
✅ **Error alerts active**  
✅ **Feature updates automated**  

**Your channel will now receive all bot updates automatically!** 🚀

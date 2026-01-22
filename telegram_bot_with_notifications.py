import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database
from config import Config

# Import AI Router and Notification Manager
try:
    from ai_router import get_ai_router
    AI_ROUTER_AVAILABLE = True
except ImportError:
    AI_ROUTER_AVAILABLE = False
    print("⚠️ AI Router not available")

try:
    from notification_manager import get_notification_manager
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("⚠️ Notification Manager not available")

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

# Initialize AI Router
if AI_ROUTER_AVAILABLE:
    ai_router = get_ai_router()
    logger.info(f"✅ AI Router initialized: {ai_router.get_backend_status()}")
else:
    ai_router = None

# Initialize Notification Manager
CHANNEL_ID = "-1003350605488"  # Your channel ID
if NOTIFICATIONS_AVAILABLE:
    try:
        notifier = get_notification_manager(Config.TELEGRAM_BOT_TOKEN, CHANNEL_ID)
        logger.info(f"✅ Notification Manager initialized for channel {CHANNEL_ID}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize notifier: {e}")
        notifier = None
else:
    notifier = None

# Admin ID
ADMIN_ID = 5451167865
DEFAULT_FREE_EXPIRY_DAYS = 7

def is_admin(user_id):
    return user_id == ADMIN_ID

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection with notifications"""
    query = update.callback_query
    await query.answer()
    
    plan = query.data.replace('select_', '')
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    # Check if user already has plan
    has_plan = db.has_active_plan(user_id, plan)
    
    if has_plan:
        message = f"""
⚠️ *You already have an active {plan.upper()} plan!*

You can have multiple plans (e.g., Free + Premium).
But you cannot have multiple keys of the same plan type.

Use /myapi to view all your API keys.
        """
        keyboard = [[InlineKeyboardButton("📊 My API Keys", callback_data='my_api')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    # For free plan, generate key
    if plan == 'free':
        await query.edit_message_text("⏳ Generating your API key with AI backend...\n\nPlease wait...")
        
        api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
        
        if not api_key:
            await query.edit_message_text("❌ Error generating API key. Please try again.")
            return
        
        # Test API with backend
        backend_used = 'unknown'
        if ai_router:
            try:
                result = await ai_router.get_response(
                    question='Test query',
                    search_online=False,
                    include_context=False
                )
                backend_used = result.get('backend_used', 'unknown')
            except Exception as e:
                logger.error(f"Backend test error: {e}")
        
        # Send notification to channel
        if notifier:
            try:
                await notifier.notify_new_api_key(
                    username=username,
                    user_id=user_id,
                    plan=plan,
                    backend=backend_used
                )
                logger.info("✅ Notification sent to channel")
            except Exception as e:
                logger.error(f"❌ Notification failed: {e}")
        
        backend_info = f"\n🤖 *Backend:* {backend_used}\n✅ API tested successfully!\n" if backend_used != 'unknown' else ""
        
        success_message = f"""
✅ *Free API Key Generated Successfully!*

🔑 Your API Key:
`{api_key}`
{backend_info}
⏰ *Valid for {DEFAULT_FREE_EXPIRY_DAYS} days*

*🌟 Example - Simple Request (Python):*
```python
import requests

url = "YOUR_API_ENDPOINT/chat"
headers = {{
    "X-API-Key": "{api_key}",
    "Content-Type": "application/json"
}}

data = {{
    "question": "What is AI?",
    "language": "english"
}}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

*🌟 Free Plan Features:*
• 100 requests/hour
• English language only
• Valid for {DEFAULT_FREE_EXPIRY_DAYS} days
• Can upgrade to Premium anytime!

*💎 Want Premium Features?*
Upgrade to Basic or Pro for:
• Unlimited requests
• 8+ languages
• Advanced features
• No expiry (monthly renewal)

Contact admin for API endpoint details.
        """
        
        keyboard = [
            [InlineKeyboardButton("✨ Upgrade to Premium", callback_data='buy_api')],
            [InlineKeyboardButton("📊 My API Keys", callback_data='my_api')],
            [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')

# Add this at the end of main() function
async def on_startup(application):
    """Called when bot starts"""
    if notifier:
        try:
            backend_status = ai_router.get_backend_status() if ai_router else None
            await notifier.notify_bot_started(backend_status)
            logger.info("✅ Startup notification sent")
        except Exception as e:
            logger.error(f"❌ Startup notification failed: {e}")

async def on_error(update, context):
    """Handle errors and send notification"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if notifier:
        try:
            await notifier.notify_error(
                error_msg=str(context.error),
                context=f"Update: {update}"
            )
        except:
            pass

def main():
    """Start the bot"""
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers here (copy from original bot)
    # application.add_handler(CommandHandler("start", start))
    # ... etc
    
    # Error handler
    application.add_error_handler(on_error)
    
    # Send startup notification
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup(application))
    
    # Start bot
    backend_status = ai_router.get_backend_status() if ai_router else {}
    logger.info(f"🚀 Bot started - Backends: {backend_status.get('available_backends', [])}")
    logger.info(f"📣 Channel notifications: {'Enabled' if notifier else 'Disabled'}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

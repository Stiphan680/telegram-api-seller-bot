import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import Database
from config import Config

# Import AI Router, Notification Manager, and Manual Payment
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

try:
    from manual_payment import get_manual_payment_handler
    payment_handler = get_manual_payment_handler()
    PAYMENT_AVAILABLE = True
except ImportError:
    PAYMENT_AVAILABLE = False
    payment_handler = None
    print("⚠️ Manual Payment not available")

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
CHANNEL_ID = "-1003350605488"
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

# API Plans
PLANS = {
    'free': {
        'name': 'Free Plan',
        'price': 0,
        'description': f'Free for {DEFAULT_FREE_EXPIRY_DAYS} days',
        'features': [
            '100 requests/hour',
            'English language only',
            'Basic tone (neutral)',
            'No conversation history',
            f'Valid for {DEFAULT_FREE_EXPIRY_DAYS} days',
            'Community support'
        ]
    },
    'basic': {
        'name': 'Basic Plan',
        'price': 99,
        'description': '₹99/month',
        'features': [
            'Unlimited requests',
            '8+ language support',
            'All tone controls',
            'Conversation history',
            'Text analysis (sentiment, keywords)',
            'Email support',
            'No expiry (monthly renewal)'
        ]
    },
    'pro': {
        'name': 'Pro Plan',
        'price': 299,
        'description': '₹299/month',
        'features': [
            'Everything in Basic',
            'Content summarization',
            'Streaming responses',
            'Priority support',
            'Advanced analytics',
            'Custom features',
            'Dedicated support',
            'No expiry (monthly renewal)'
        ]
    }
}

def is_admin(user_id):
    return user_id == ADMIN_ID

def format_expiry(expiry_date_str):
    if not expiry_date_str:
        return "No expiry (Permanent)"
    try:
        expiry = datetime.fromisoformat(expiry_date_str)
        now = datetime.now()
        if now > expiry:
            return "⚠️ Expired"
        days_left = (expiry - now).days
        if days_left > 0:
            return f"✅ {days_left} days left (expires {expiry.strftime('%Y-%m-%d')})"
        return f"⚠️ {(expiry - now).seconds // 3600} hours left"
    except:
        return "Invalid date"

async def get_ai_backend_info():
    if ai_router:
        status = ai_router.get_backend_status()
        if 'perplexity' in status.get('available_backends', []):
            return "🔍 Powered by Perplexity AI (Online Search + Citations)"
        return "🤖 Powered by Gemini + Groq (Free AI)"
    return "🤖 Advanced AI Backend"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    backend_info = await get_ai_backend_info()
    
    if is_admin(user.id):
        welcome_text = f"""
🤖 *Welcome Admin {user.first_name}!* 👑

{backend_info}

*Admin Commands:*
/payments - View pending payments
/verify - Verify payment
/backend - Check AI Backend
        """
        keyboard = [
            [InlineKeyboardButton("💳 Pending Payments", callback_data='admin_payments')],
            [InlineKeyboardButton("📊 My API Keys", callback_data='my_api')]
        ]
    else:
        welcome_text = f"""
🤖 *Welcome to API Seller Bot!*

{backend_info}

Hello {user.first_name}!

*Commands:*
/buy - Get API access
/myapi - View your keys
/payment - Check payment status
/help - Get help
        """
        keyboard = [
            [InlineKeyboardButton("🛍️ Buy API", callback_data='buy_api')],
            [InlineKeyboardButton("📊 My Keys", callback_data='my_api')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def check_backend_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if not ai_router:
        await update.message.reply_text("❌ AI Router not available")
        return
    
    status = ai_router.get_backend_status()
    status_text = f"""
🤖 *AI Backend Status*

*Available:* {', '.join(status.get('available_backends', []))}
*Default:* {status.get('default', 'none')}
*Perplexity:* {'✅' if status.get('perplexity_enabled') else '❌'}
*Advanced AI:* {'✅' if status.get('advanced_ai_enabled') else '❌'}
    """
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def buy_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plans_text = f"""
💳 *Choose Your Plan*

*1️⃣ Free* - ₹0 ({DEFAULT_FREE_EXPIRY_DAYS} days)
*2️⃣ Basic* - ₹99/month
*3️⃣ Pro* - ₹299/month
    """
    
    keyboard = [
        [InlineKeyboardButton("🆓 Free Plan", callback_data='select_free')],
        [InlineKeyboardButton("💎 Basic Plan", callback_data='select_basic')],
        [InlineKeyboardButton("⭐ Pro Plan", callback_data='select_pro')],
        [InlineKeyboardButton("« Back", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(plans_text, reply_markup=reply_markup, parse_mode='Markdown')

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plan = query.data.replace('select_', '')
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    has_plan = db.has_active_plan(user_id, plan)
    if has_plan:
        await query.edit_message_text(f"⚠️ You already have {plan.upper()} plan active!")
        return
    
    if plan == 'free':
        await query.edit_message_text("⏳ Generating API key...")
        
        api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
        
        if not api_key:
            await query.edit_message_text("❌ Error! Try again.")
            return
        
        # Test backend
        backend_used = 'unknown'
        if ai_router:
            try:
                result = await ai_router.get_response(
                    question='Test',
                    search_online=False
                )
                backend_used = result.get('backend_used', 'unknown')
            except Exception as e:
                logger.error(f"Backend test error: {e}")
        
        # Send notification
        if notifier:
            try:
                await notifier.notify_new_api_key(
                    username=username,
                    user_id=user_id,
                    plan=plan,
                    backend=backend_used
                )
            except Exception as e:
                logger.error(f"Notification failed: {e}")
        
        backend_info = f"\n🤖 Backend: {backend_used}\n" if backend_used != 'unknown' else ""
        
        success_message = f"""
✅ *API Key Generated!*

🔑 `{api_key}`
{backend_info}
⏰ Valid for {DEFAULT_FREE_EXPIRY_DAYS} days

*Example:*
```python
import requests
url = "API_ENDPOINT/chat"
headers = {{"X-API-Key": "{api_key}"}}
data = {{"question": "Hello!"}}
requests.post(url, json=data, headers=headers)
```

Use /myapi to view all keys
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
            [InlineKeyboardButton("« Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    else:
        # Show manual payment instructions
        if payment_handler:
            payment_request = payment_handler.create_payment_request(
                user_id=user_id,
                username=username,
                plan=plan,
                amount=PLANS[plan]['price']
            )
            
            payment_msg = payment_request['instructions']
            
            keyboard = [
                [InlineKeyboardButton("✅ Payment Done?", callback_data=f'check_payment_{plan}')],
                [InlineKeyboardButton("« Back", callback_data='buy_api')]
            ]
        else:
            payment_msg = f"""
💳 *{PLANS[plan]['name']} Payment*

Price: *₹{PLANS[plan]['price']}/month*

Contact admin for payment details.
            """
            keyboard = [[InlineKeyboardButton("« Back", callback_data='buy_api')]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(payment_msg, reply_markup=reply_markup, parse_mode='Markdown')

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User checks their payment status"""
    user_id = update.effective_user.id
    
    if payment_handler:
        summary = payment_handler.get_payment_summary(user_id)
        await update.message.reply_text(summary, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Payment system not available")

async def admin_view_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin views all pending payments"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if payment_handler:
        summary = payment_handler.get_admin_summary()
        await update.message.reply_text(summary, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Payment system not available")

async def admin_verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin verifies a payment: /verify USER_123_BASIC"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /verify USER_123_BASIC")
        return
    
    reference = context.args[0]
    
    if payment_handler:
        payment = payment_handler.get_pending_payment(reference)
        
        if not payment:
            await update.message.reply_text("❌ Payment not found!")
            return
        
        # Create API key
        api_key = db.create_api_key(
            user_id=payment['user_id'],
            username=payment['username'],
            plan=payment['plan'],
            expiry_days=30  # Paid plans: 30 days
        )
        
        if api_key:
            # Mark as verified
            payment_handler.mark_payment_verified(reference)
            
            # Notify channel
            if notifier:
                try:
                    await notifier.notify_new_api_key(
                        username=payment['username'],
                        user_id=payment['user_id'],
                        plan=payment['plan'],
                        backend='manual_verified'
                    )
                except:
                    pass
            
            # Send to admin
            await update.message.reply_text(
                f"✅ *Payment Verified!*\n\n"
                f"User: @{payment['username']}\n"
                f"Plan: {payment['plan'].upper()}\n"
                f"API Key: `{api_key}`\n\n"
                f"User has been notified.",
                parse_mode='Markdown'
            )
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=payment['user_id'],
                    text=f"✅ *Payment Verified!*\n\n"
                         f"🔑 Your API Key:\n`{api_key}`\n\n"
                         f"Plan: {payment['plan'].upper()}\n"
                         f"Valid for 30 days\n\n"
                         f"Use /myapi to view all keys",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")
        else:
            await update.message.reply_text("❌ Failed to create API key!")
    else:
        await update.message.reply_text("❌ Payment system not available")

async def my_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        edit_message = True
    else:
        user_id = update.effective_user.id
        edit_message = False
    
    keys = db.get_active_api_keys(user_id)
    
    if not keys:
        message = "❌ No active keys. Use /buy to get one!"
        keyboard = [[InlineKeyboardButton("🛍️ Buy API", callback_data='buy_api')]]
    else:
        message = f"🔑 *Your API Keys* ({len(keys)})\n\n"
        for idx, key in enumerate(keys, 1):
            plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(key.get('plan'), "❓")
            expiry_info = format_expiry(key.get('expiry_date'))
            message += f"{idx}. {plan_emoji} *{key.get('plan', 'N/A').upper()}*\n"
            message += f"   `{key.get('api_key')}`\n"
            message += f"   {expiry_info}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Get More", callback_data='buy_api')],
            [InlineKeyboardButton("« Menu", callback_data='back_to_menu')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    menu_text = "🤖 *Main Menu*\n\nWhat would you like to do?"
    keyboard = [
        [InlineKeyboardButton("🛍️ Buy API", callback_data='buy_api')],
        [InlineKeyboardButton("📊 My Keys", callback_data='my_api')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""
📚 *Help & Commands*

/start - Start bot
/buy - Get API access
/myapi - View your keys
/payment - Check payment status
/help - This message

*Plans:*
Free: ₹0 ({DEFAULT_FREE_EXPIRY_DAYS} days)
Basic: ₹99/month
Pro: ₹299/month
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

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
    """Handle errors"""
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
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("backend", check_backend_status))
    application.add_handler(CommandHandler("myapi", my_api_key))
    application.add_handler(CommandHandler("payment", check_payment_status))
    application.add_handler(CommandHandler("payments", admin_view_payments))
    application.add_handler(CommandHandler("verify", admin_verify_payment))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    
    # Error handler
    application.add_error_handler(on_error)
    
    # Send startup notification
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup(application))
    
    # Start bot
    backend_status = ai_router.get_backend_status() if ai_router else {}
    logger.info(f"🚀 Bot started - Backends: {backend_status.get('available_backends', [])}")
    logger.info(f"📣 Notifications: {'Enabled' if notifier else 'Disabled'}")
    logger.info(f"💳 Payment: {'Manual' if payment_handler else 'Disabled'}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

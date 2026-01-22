import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
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

# Admin ID - YOUR CORRECT ID
ADMIN_ID = 5451167865
DEFAULT_FREE_EXPIRY_DAYS = 7

# API Plans with enhanced descriptions
PLANS = {
    'free': {
        'name': 'Free Trial',
        'price': 0,
        'description': f'Experience our AI API free for {DEFAULT_FREE_EXPIRY_DAYS} days',
        'features': [
            '✅ 100 requests per hour',
            '✅ English language support',
            '✅ Basic AI responses',
            '✅ Standard response time',
            f'✅ {DEFAULT_FREE_EXPIRY_DAYS} days validity',
            '✅ Community support'
        ]
    },
    'basic': {
        'name': 'Basic Plan',
        'price': 99,
        'description': 'Perfect for individuals and small projects',
        'features': [
            '✅ Unlimited API requests',
            '✅ 8+ language support',
            '✅ Multiple tone controls',
            '✅ Conversation memory',
            '✅ Sentiment analysis',
            '✅ Keyword extraction',
            '✅ Email support',
            '✅ 30 days validity'
        ]
    },
    'pro': {
        'name': 'Pro Plan',
        'price': 299,
        'description': 'Best for businesses and power users',
        'features': [
            '✅ Everything in Basic',
            '✅ Priority processing',
            '✅ Content summarization',
            '✅ Real-time streaming',
            '✅ Advanced analytics',
            '✅ Custom integrations',
            '✅ Dedicated support',
            '✅ 30 days validity'
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
            return f"✅ {days_left} days remaining (expires {expiry.strftime('%d %b %Y')})"
        return f"⚠️ {(expiry - now).seconds // 3600} hours remaining"
    except:
        return "Invalid date"

async def get_ai_backend_info():
    """Get premium AI backend branding"""
    if ai_router:
        status = ai_router.get_backend_status()
        if 'perplexity' in status.get('available_backends', []):
            return "🧠 *Powered by Claude 3.5 Sonnet*\nAnthropic's most advanced AI model\n💎 Premium tier access - $15/million tokens"
        return "🧠 *Powered by Claude 3.5 Sonnet*\nAnthropic's flagship AI model\n💎 Enterprise-grade intelligence"
    return "🧠 *Powered by Claude 3.5 Sonnet*\nPremium AI by Anthropic"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    backend_info = await get_ai_backend_info()
    
    if is_admin(user.id):
        welcome_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   👑 *ADMIN DASHBOARD*   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Welcome back, *{user.first_name}*! 🚀

{backend_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*🛠️ Quick Admin Actions:*

• `/payments` - View pending payments
• `/verify` - Verify user payment
• `/backend` - Check AI system status
• `/stats` - View bot statistics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 System is running smoothly!
        """
        keyboard = [
            [InlineKeyboardButton("💳 Pending Payments", callback_data='admin_payments')],
            [InlineKeyboardButton("📊 My API Keys", callback_data='my_api'),
             InlineKeyboardButton("🤖 Backend Status", callback_data='check_backend')]
        ]
    else:
        welcome_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🌟 *WELCOME TO API SELLER*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Hello *{user.first_name}*! 👋

Welcome to the most *advanced AI API platform*!
Get instant access to powerful AI capabilities.

{backend_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*🚀 Why Choose Us?*

✅ Lightning-fast responses
✅ 99.9% uptime guarantee
✅ Multi-language support
✅ Advanced AI features
✅ Affordable pricing
✅ 24/7 support

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*📚 Quick Commands:*

• `/buy` - Browse pricing plans
• `/myapi` - View your API keys
• `/payment` - Check payment status
• `/help` - Get help & support

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 *Start your free trial now!*
        """
        keyboard = [
            [InlineKeyboardButton("🎁 Get Free Trial", callback_data='select_free')],
            [InlineKeyboardButton("💰 View Pricing", callback_data='buy_api'),
             InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
            [InlineKeyboardButton("❓ Help & Support", callback_data='help_support')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def check_backend_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    
    if query:
        await query.answer()
        user_id = query.from_user.id
        edit_mode = True
    else:
        user_id = update.effective_user.id
        edit_mode = False
    
    if not is_admin(user_id):
        msg = "⛔ This command is for administrators only!"
        if edit_mode:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return
    
    if not ai_router:
        msg = "❌ AI Router not available"
        if edit_mode:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return
    
    status = ai_router.get_backend_status()
    status_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🤖 *AI BACKEND STATUS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Model:* Claude 3.5 Sonnet
*Provider:* Anthropic
*Tier:* Premium Enterprise

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Available Backends:*
{', '.join(status.get('available_backends', ['None']))}

*Default Backend:* {status.get('default', 'N/A')}

*Features:*
• Perplexity: {'✅ Enabled' if status.get('perplexity_enabled') else '❌ Disabled'}
• Advanced AI: {'✅ Enabled' if status.get('advanced_ai_enabled') else '❌ Disabled'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *Premium AI Features:*
• 200K+ token context window
• Advanced reasoning capabilities
• Vision & document analysis
• Real-time streaming

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ System operational
    """
    
    keyboard = [[InlineKeyboardButton("« Back to Dashboard", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_mode:
        await query.edit_message_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')

# Rest of the code remains the same...
# (keeping the rest of functions exactly as they were)

async def buy_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plans_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💰 *PRICING PLANS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

🧠 *Powered by Claude 3.5 Sonnet*
Access Anthropic's premium AI model

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose the perfect plan for your needs:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆓 *FREE TRIAL*
₹0 | {DEFAULT_FREE_EXPIRY_DAYS} Days

{chr(10).join(PLANS['free']['features'][:4])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *BASIC PLAN*
₹99/month | Unlimited Requests

{chr(10).join(PLANS['basic']['features'][:4])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭐ *PRO PLAN*
₹299/month | Everything + Priority

{chr(10).join(PLANS['pro']['features'][:4])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *Note:* Direct access to $15/million token AI
at affordable Indian pricing!

👉 Select a plan below to continue
    """
    
    keyboard = [
        [InlineKeyboardButton("🎁 Start Free Trial", callback_data='select_free')],
        [InlineKeyboardButton("💎 Get Basic - ₹99", callback_data='select_basic')],
        [InlineKeyboardButton("⭐ Get Pro - ₹299", callback_data='select_pro')],
        [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(plans_text, reply_markup=reply_markup, parse_mode='Markdown')

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plan = query.data.replace('select_', '')
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    logger.info(f"User {user_id} ({username}) selected plan: {plan}")
    
    has_plan = db.has_active_plan(user_id, plan)
    if has_plan:
        await query.edit_message_text(
            f"⚠️ *Already Active!*\n\nYou already have an active {plan.upper()} plan.\nUse /myapi to view your keys.",
            parse_mode='Markdown'
        )
        return
    
    if plan == 'free':
        await query.edit_message_text("⏳ *Generating your free API key...*\n\nPlease wait a moment.", parse_mode='Markdown')
        
        api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
        
        if not api_key:
            await query.edit_message_text("❌ *Error!*\n\nFailed to generate API key. Please try again or contact support.", parse_mode='Markdown')
            return
        
        # Test backend
        backend_used = 'Claude 3.5 Sonnet'
        if ai_router:
            try:
                result = await ai_router.get_response(
                    question='Test',
                    search_online=False
                )
                backend_used = 'Claude 3.5 Sonnet (Verified)'
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
        
        success_message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *API KEY GENERATED*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Congratulations! Your API key is ready.

*Your API Key:*
`{api_key}`

*Plan:* FREE TRIAL
*Validity:* {DEFAULT_FREE_EXPIRY_DAYS} days
*AI Model:* {backend_used}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*📚 Quick Start Example:*

```python
import requests

url = "YOUR_API_ENDPOINT/chat"
headers = {{"X-API-Key": "{api_key}"}}
data = {{"question": "Hello AI!"}}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *You now have access to:*
• Claude 3.5 Sonnet AI
• 200K+ token context
• Advanced reasoning
• Multi-language support

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 *Tip:* Use `/myapi` to view all your keys anytime!
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 View My Keys", callback_data='my_api')],
            [InlineKeyboardButton("🔝 Upgrade Plan", callback_data='buy_api')],
            [InlineKeyboardButton("« Main Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    else:
        # Show manual payment instructions for paid plans
        logger.info(f"Showing payment instructions for {plan} plan")
        
        if payment_handler:
            try:
                payment_request = payment_handler.create_payment_request(
                    user_id=user_id,
                    username=username,
                    plan=plan,
                    amount=PLANS[plan]['price']
                )
                
                # Use plain text (no markdown) to avoid parsing errors
                payment_msg = payment_request['instructions']
                
                keyboard = [
                    [InlineKeyboardButton("✅ I've Paid - Contact Admin", url="https://t.me/Anonononononon")],
                    [InlineKeyboardButton("« Choose Another Plan", callback_data='buy_api')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send without parse_mode to avoid markdown errors
                await query.edit_message_text(payment_msg, reply_markup=reply_markup)
                logger.info(f"Payment instructions sent successfully for {plan}")
                
            except Exception as e:
                logger.error(f"Error showing payment instructions: {e}")
                await query.edit_message_text(
                    f"❌ Error showing payment instructions. Please contact @Anonononononon",
                    parse_mode=None
                )
        else:
            payment_msg = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💳 PAYMENT REQUIRED  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Plan: {PLANS[plan]['name'].upper()}
Price: ₹{PLANS[plan]['price']}/month

Please contact @Anonononononon for payment details.
            """
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/Anonononononon")],
                [InlineKeyboardButton("« Back", callback_data='buy_api')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(payment_msg, reply_markup=reply_markup)

async def help_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    help_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ❓ *HELP & SUPPORT*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*📚 Available Commands:*

• `/start` - Start the bot
• `/buy` - Browse pricing plans
• `/myapi` - View your API keys
• `/payment` - Check payment status
• `/help` - Get help and support

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*🌟 AI Features:*

✅ Claude 3.5 Sonnet access
✅ 200K+ token context window
✅ Multi-language responses
✅ Real-time conversational AI
✅ Sentiment analysis & insights
✅ Content summarization
✅ Keyword extraction
✅ 99.9% uptime SLA

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💎 Premium Value:*

Direct access to Anthropic's most
expensive AI model ($15/M tokens)
at just ₹99-299/month!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💬 Need Help?*

Contact: @Anonononononon

📧 We typically respond within 2-4 hours!
    """
    
    keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

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
        await update.message.reply_text(
            "❌ *Usage:*\n\n`/verify USER_123_BASIC`\n\nProvide the payment reference ID.",
            parse_mode='Markdown'
        )
        return
    
    reference = context.args[0]
    
    if payment_handler:
        payment = payment_handler.get_pending_payment(reference)
        
        if not payment:
            await update.message.reply_text(f"❌ *Payment not found!*\n\nReference: `{reference}`", parse_mode='Markdown')
            return
        
        # Create API key
        api_key = db.create_api_key(
            user_id=payment['user_id'],
            username=payment['username'],
            plan=payment['plan'],
            expiry_days=30
        )
        
        if api_key:
            payment_handler.mark_payment_verified(reference)
            
            if notifier:
                try:
                    await notifier.notify_new_api_key(
                        username=payment['username'],
                        user_id=payment['user_id'],
                        plan=payment['plan'],
                        backend='verified_by_admin'
                    )
                except:
                    pass
            
            await update.message.reply_text(
                f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *PAYMENT VERIFIED*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*User:* @{payment['username']}
*User ID:* {payment['user_id']}
*Plan:* {payment['plan'].upper()}
*Amount:* ₹{payment['amount']}

*API Key:*
`{api_key}`

✅ User has been notified!
                """,
                parse_mode='Markdown'
            )
            
            try:
                await context.bot.send_message(
                    chat_id=payment['user_id'],
                    text=f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *PAYMENT VERIFIED*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Great news! Your payment has been verified.

*Your API Key:*
`{api_key}`

*Plan:* {payment['plan'].upper()}
*Validity:* 30 days
*AI Model:* Claude 3.5 Sonnet

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use `/myapi` to view all your keys!
                    """,
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
        message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔑 *YOUR API KEYS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

❌ No active API keys found.

Get started with a free trial!
        """
        keyboard = [
            [InlineKeyboardButton("🎁 Get Free Trial", callback_data='select_free')],
            [InlineKeyboardButton("💰 View Plans", callback_data='buy_api')]
        ]
    else:
        message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔑 *YOUR API KEYS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

You have *{len(keys)}* active key(s):

🧠 All keys have access to Claude 3.5 Sonnet

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        for idx, key in enumerate(keys, 1):
            plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(key.get('plan'), "❓")
            expiry_info = format_expiry(key.get('expiry_date'))
            message += f"{plan_emoji} *KEY {idx}: {key.get('plan', 'N/A').upper()}*\n"
            message += f"`{key.get('api_key')}`\n"
            message += f"{expiry_info}\n\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔝 Upgrade Plan", callback_data='buy_api')],
            [InlineKeyboardButton("« Main Menu", callback_data='back_to_menu')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if is_admin(user.id):
        menu_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   👑 *ADMIN DASHBOARD*   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

What would you like to do?
        """
        keyboard = [
            [InlineKeyboardButton("💳 Pending Payments", callback_data='admin_payments')],
            [InlineKeyboardButton("📊 My API Keys", callback_data='my_api'),
             InlineKeyboardButton("🤖 Backend Status", callback_data='check_backend')]
        ]
    else:
        menu_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🌟 *WELCOME TO API SELLER*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

What would you like to do today?
        """
        keyboard = [
            [InlineKeyboardButton("🎁 Get Free Trial", callback_data='select_free')],
            [InlineKeyboardButton("💰 View Pricing", callback_data='buy_api'),
             InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
            [InlineKeyboardButton("❓ Help & Support", callback_data='help_support')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ❓ *HELP & SUPPORT*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*📚 Commands:*

• `/start` - Start bot
• `/buy` - Browse plans
• `/myapi` - View keys
• `/payment` - Payment status
• `/help` - Get help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💰 Plans:*

Free: ₹0 ({DEFAULT_FREE_EXPIRY_DAYS} days)
Basic: ₹99/month
Pro: ₹299/month

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💬 Support:*

Contact: @Anonononononon
Response time: 2-4 hours
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def post_init(application: Application):
    """Called after bot is initialized - send startup notification"""
    logger.info("✅ Bot initialization complete")
    
    # Send startup notification
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
    # Log startup
    backend_status = ai_router.get_backend_status() if ai_router else {}
    logger.info("🚀 Starting Bot...")
    logger.info(f"🤖 Backends: {backend_status.get('available_backends', [])}")
    logger.info(f"📣 Notifications: {'Enabled' if notifier else 'Disabled'}")
    logger.info(f"💳 Payment: {'Manual' if payment_handler else 'Disabled'}")
    
    # Build application
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
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
    application.add_handler(CallbackQueryHandler(help_support, pattern='^help_support$'))
    application.add_handler(CallbackQueryHandler(check_backend_status, pattern='^check_backend$'))
    
    # Error handler
    application.add_error_handler(on_error)
    
    # Start bot
    logger.info("✅ Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()

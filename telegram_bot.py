import os
import logging
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
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
DEFAULT_FREE_EXPIRY_DAYS = 2

# Payment UPI ID
UPI_ID = "aman4380@kphdfc"
UPI_NAME = "Aman"

# Health Check Server for Render FREE tier
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        stats = db.get_stats()
        status_html = f"""
        <html>
        <head><title>🤖 API Seller Bot Status</title></head>
        <body style="font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff;">
            <h1>🤖 Telegram Bot - Active</h1>
            <p><strong>Status:</strong> ✅ Running</p>
            <p><strong>Admin ID:</strong> {ADMIN_ID}</p>
            <p><strong>AI Router:</strong> {'✅ Connected' if ai_router else '❌ Disabled'}</p>
            <p><strong>Notifications:</strong> {'✅ Enabled' if notifier else '❌ Disabled'}</p>
            <p><strong>Payments:</strong> ✅ UPI ({UPI_ID})</p>
            <hr>
            <h2>📊 Statistics</h2>
            <p>Total Users: {stats.get('total_users', 0)}</p>
            <p>Active API Keys: {stats.get('active_keys', 0)}</p>
            <p>Gift Cards: {stats.get('active_gifts', 0)} active / {stats.get('total_gifts', 0)} total</p>
            <p>Total Requests: {stats.get('total_requests', 0)}</p>
            <hr>
            <small>Render Free Tier - Health Check Endpoint</small>
        </body>
        </html>
        """
        self.wfile.write(status_html.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def run_health_server():
    """Run health check HTTP server on port 10000 for Render"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"🌐 Health check server running on port {port}")
    server.serve_forever()

# API Plans
PLANS = {
    'free': {
        'name': 'Free Trial',
        'price': 0,
        'description': f'Experience our AI API free for {DEFAULT_FREE_EXPIRY_DAYS} days',
        'features': [
            '✅ All Premium Features',
            '✅ AI Chat (Claude 3.5)',
            '✅ Image Generation (1024x1024)',
            '✅ Video Generation (HD)',
            '✅ Code Expert Assistant',
            f'✅ {DEFAULT_FREE_EXPIRY_DAYS} days validity',
            '✅ No credit card required'
        ]
    },
    'basic': {
        'name': 'Basic Plan',
        'price': 99,
        'description': 'Perfect for individuals and small projects',
        'features': [
            '✅ Unlimited API requests',
            '✅ All AI features included',
            '✅ Chat, Images, Videos, Code',
            '✅ Priority support',
            '✅ Fast response time',
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
            '✅ Advanced AI models',
            '✅ Highest quality output',
            '✅ 24/7 dedicated support',
            '✅ Custom integrations',
            '✅ 30 days validity'
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - shows welcome message"""
    user = update.effective_user
    
    # Register user
    db.register_user(user.id, user.username or user.first_name)
    
    welcome_message = f"""
🎉 *Welcome to Premium API Store!*

Hello {user.first_name}! Get instant access to powerful AI features:

🤖 *AI Chat* - Claude 3.5 Sonnet
🎨 *Image Generation* - Flux AI (1024x1024)
🎬 *Video Generation* - Mochi AI (HD)
💻 *Code Expert* - Claude Assistant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 *Get {DEFAULT_FREE_EXPIRY_DAYS}-Day Free Trial!*

Try all features completely free!

• `/start` - Show this menu
• `/myapi` - View your API keys
• `/buy` - Browse paid plans
• `/redeem` - Redeem gift card
• `/help` - Get support
    """
    
    keyboard = [
        [InlineKeyboardButton("🎁 Get Free Trial", callback_data='select_free')],
        [InlineKeyboardButton("💰 View Pricing", callback_data='buy_api'),
         InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
        [InlineKeyboardButton("❓ Help & Support", callback_data='help_support')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection"""
    query = update.callback_query
    await query.answer()
    
    plan = query.data.replace('select_', '')
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    # Check if user already has this plan
    has_plan = db.has_active_plan(user_id, plan)
    if has_plan:
        await query.edit_message_text(
            f"⚠️ *Already Active!*\n\nYou already have an active {plan.upper()} plan.\n\nUse `/myapi` to view your keys.",
            parse_mode='Markdown'
        )
        return
    
    if plan == 'free':
        # Generate free trial API key (2 days)
        await query.edit_message_text("⏳ *Generating your free API key...*\n\nPlease wait.", parse_mode='Markdown')
        
        api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
        
        if api_key:
            success_message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *API KEY GENERATED*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Congratulations! Your API key is ready.

*Your API Key:*
`{api_key}`

*Plan:* FREE TRIAL
*Validity:* {DEFAULT_FREE_EXPIRY_DAYS} days
*Features:* All premium features included!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *You now have access to:*
• AI Chat (Claude 3.5 Sonnet)
• Image Generation (1024x1024)
• Video Generation (HD)
• Code Expert Assistant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 Use `/myapi` to view all your keys!
            """
            
            # Notify admin
            if notifier:
                try:
                    await notifier.notify_new_api_key(
                        username=username,
                        user_id=user_id,
                        plan=plan,
                        backend=f"Free Trial ({DEFAULT_FREE_EXPIRY_DAYS}d)"
                    )
                except:
                    pass
            
            keyboard = [
                [InlineKeyboardButton("📊 View My Keys", callback_data='my_api')],
                [InlineKeyboardButton("🔝 Upgrade Plan", callback_data='buy_api')],
                [InlineKeyboardButton("« Main Menu", callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ *Error!*\n\nFailed to generate API key. Please try again.", parse_mode='Markdown')
    else:
        # Show payment instructions for paid plans
        payment_msg = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💳 *PAYMENT DETAILS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Selected Plan:* {PLANS[plan]['name']}
*Price:* ₹{PLANS[plan]['price']}/month
*Validity:* 30 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💸 *Payment Method: UPI*

*UPI ID:*
`{UPI_ID}`

*Name:* {UPI_NAME}
*Amount:* ₹{PLANS[plan]['price']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 *Payment Steps:*

1️⃣ Open any UPI app (GPay, PhonePe, Paytm)
2️⃣ Enter UPI ID: `{UPI_ID}`
3️⃣ Send ₹{PLANS[plan]['price']}
4️⃣ Take screenshot of payment
5️⃣ Send screenshot to admin with your:
   • Telegram Username: @{username}
   • Selected Plan: {PLANS[plan]['name']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ *Quick Payment:*
upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={PLANS[plan]['price']}&cu=INR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 After payment, contact admin:
@Anonononononon

⏱️ API key will be activated within 2-4 hours!
        """
        
        keyboard = [
            [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/Anonononononon")],
            [InlineKeyboardButton("🔙 Back to Plans", callback_data='buy_api')],
            [InlineKeyboardButton("« Main Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(payment_msg, reply_markup=reply_markup, parse_mode='Markdown')

async def my_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's API keys"""
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

Get started with a {DEFAULT_FREE_EXPIRY_DAYS}-day free trial!
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        for idx, key in enumerate(keys, 1):
            plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(key.get('plan'), "❓")
            
            # Calculate expiry
            expiry_text = "No expiry"
            if key.get('expiry_date'):
                try:
                    expiry = datetime.fromisoformat(key['expiry_date'])
                    days_left = (expiry - datetime.now()).days
                    if days_left > 0:
                        expiry_text = f"{days_left} days remaining"
                    else:
                        expiry_text = "Expired"
                except:
                    pass
            
            message += f"{plan_emoji} *KEY {idx}: {key.get('plan', 'N/A').upper()}*\n"
            message += f"`{key.get('api_key')}`\n"
            message += f"{expiry_text}\n\n"
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

async def buy_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pricing plans"""
    query = update.callback_query
    await query.answer()
    
    plans_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💰 *PRICING PLANS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

🆓 *FREE TRIAL*
₹0 | {DEFAULT_FREE_EXPIRY_DAYS} Days

• All premium features
• AI Chat, Images, Videos
• Code Expert included
• No payment required

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *BASIC PLAN*
₹99/month | 30 Days

• Unlimited API requests
• All AI features
• Priority support
• Fast response time

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭐ *PRO PLAN*
₹299/month | 30 Days

• Everything in Basic
• Advanced AI models
• Highest quality output
• 24/7 dedicated support

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💸 *Payment: UPI*
UPI ID: `{UPI_ID}`

👉 Select a plan below:
    """
    
    keyboard = [
        [InlineKeyboardButton(f"🎁 Start {DEFAULT_FREE_EXPIRY_DAYS}-Day Free Trial", callback_data='select_free')],
        [InlineKeyboardButton("💎 Buy Basic - ₹99", callback_data='select_basic')],
        [InlineKeyboardButton("⭐ Buy Pro - ₹299", callback_data='select_pro')],
        [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(plans_text, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    query = update.callback_query
    await query.answer()
    
    menu_text = f"""
🌟 *Welcome to Premium API Store!*

Get instant access to powerful AI:

🤖 AI Chat | 🎨 Images | 🎬 Videos | 💻 Code

🎁 Try free for {DEFAULT_FREE_EXPIRY_DAYS} days!
    """
    
    keyboard = [
        [InlineKeyboardButton("🎁 Get Free Trial", callback_data='select_free')],
        [InlineKeyboardButton("💰 View Pricing", callback_data='buy_api'),
         InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
        [InlineKeyboardButton("❓ Help & Support", callback_data='help_support')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help and support info"""
    query = update.callback_query
    await query.answer()
    
    help_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ❓ *HELP & SUPPORT*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*📚 Commands:*

• `/start` - Main menu
• `/myapi` - View API keys
• `/buy` - Browse plans
• `/redeem <code>` - Use gift card
• `/help` - This help page

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💎 Features:*

• AI Chat (Claude 3.5 Sonnet)
• Image Generation (1024x1024)
• Video Generation (HD)
• Code Expert Assistant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💸 Payment:*

UPI ID: `{UPI_ID}`
Name: {UPI_NAME}

Accepted: GPay, PhonePe, Paytm, etc.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💬 Support:*

Contact: @Anonononononon
Response: 2-4 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 Start your {DEFAULT_FREE_EXPIRY_DAYS}-day free trial now!
    """
    
    keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    """Start the bot"""
    # Start health check server
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("🌐 Health check server started")
    
    logger.info("🚀 Starting Bot...")
    logger.info(f"🎁 Free Trial: {DEFAULT_FREE_EXPIRY_DAYS} days")
    logger.info(f"💸 Payment: UPI ({UPI_ID})")
    logger.info(f"🤖 AI: {'Enabled' if ai_router else 'Disabled'}")
    logger.info(f"📣 Notifications: {'Enabled' if notifier else 'Disabled'}")
    
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myapi", my_api_key))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(help_support, pattern='^help_support$'))
    
    logger.info("✅ Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()

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

# Check admin
def is_admin(user_id):
    return user_id == ADMIN_ID

# Health Check Server
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
            <p>Total Requests: {stats.get('total_requests', 0)}</p>
            <hr>
            <small>Premium API Gateway</small>
        </body>
        </html>
        """
        self.wfile.write(status_html.encode())
    
    def log_message(self, format, *args):
        pass

def run_health_server():
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
            '✅ Image Generation',
            '✅ Video Generation',
            '✅ Code Expert',
            f'✅ {DEFAULT_FREE_EXPIRY_DAYS} days validity'
        ]
    },
    'basic': {
        'name': 'Basic Plan',
        'price': 99,
        'description': 'Perfect for individuals',
        'features': [
            '✅ Unlimited Requests',
            '✅ All Features',
            '✅ Priority Support',
            '✅ 30 days validity'
        ]
    },
    'pro': {
        'name': 'Pro Plan',
        'price': 299,
        'description': 'Best for professionals',
        'features': [
            '✅ Everything in Basic',
            '✅ Advanced Models',
            '✅ 24/7 Support',
            '✅ 30 days validity'
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.username or user.first_name)
    
    welcome_message = f"""
🎉 *Welcome to Premium API Store!*

Hello {user.first_name}!

🤖 *AI Chat* - Claude 3.5 Sonnet
🎨 *Image Generation* - Flux AI
🎬 *Video Generation* - Mochi AI
💻 *Code Expert* - Claude Assistant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 *Get {DEFAULT_FREE_EXPIRY_DAYS}-Day Free Trial!*

Try all features completely free!
    """
    
    keyboard = [
        [InlineKeyboardButton("🎁 Get Free Trial", callback_data='select_free')],
        [InlineKeyboardButton("💰 View Pricing", callback_data='buy_api'),
         InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
        [InlineKeyboardButton("❓ Help", callback_data='help_support')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plan = query.data.replace('select_', '')
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    has_plan = db.has_active_plan(user_id, plan)
    if has_plan:
        await query.edit_message_text(
            f"⚠️ *Already Active!*\n\nYou already have an active {plan.upper()} plan.\n\nUse `/myapi` to view your keys.",
            parse_mode='Markdown'
        )
        return
    
    if plan == 'free':
        await query.edit_message_text("⏳ *Generating your free API key...*\n\nPlease wait.", parse_mode='Markdown')
        
        api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
        
        if api_key:
            success_message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *API KEY GENERATED*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Congratulations!

*Your API Key:*
`{api_key}`

*Plan:* FREE TRIAL
*Validity:* {DEFAULT_FREE_EXPIRY_DAYS} days
*Features:* All premium features!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *Access to:*
• AI Chat, Images, Videos, Code

📌 Use `/myapi` to view keys!
            """
            
            if notifier:
                try:
                    await notifier.notify_new_api_key(username=username, user_id=user_id, plan=plan, backend=f"Free ({DEFAULT_FREE_EXPIRY_DAYS}d)")
                except:
                    pass
            
            keyboard = [
                [InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
                [InlineKeyboardButton("🔝 Upgrade", callback_data='buy_api')],
                [InlineKeyboardButton("« Menu", callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ *Error!*\n\nFailed to generate API key.", parse_mode='Markdown')
    else:
        # Create payment request with reference ID
        if PAYMENT_AVAILABLE:
            payment_result = payment_handler.create_payment_request(
                user_id=user_id,
                username=username,
                plan=plan,
                amount=PLANS[plan]['price']
            )
            
            if payment_result['success']:
                reference = payment_result['reference']
                amount = payment_result['amount']
                
                payment_msg = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💳 *PAYMENT DETAILS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

🏷️ *Plan:* {PLANS[plan]['name']}
💵 *Amount:* ₹{amount}
🎯 *Reference:* `{reference}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💸 *UPI Payment Method*

*UPI ID:*
`{UPI_ID}`

*Name:* {UPI_NAME}
*Amount:* ₹{amount}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 *Payment Steps:*

1️⃣ Open UPI app (GPay/PhonePe/Paytm)
2️⃣ Pay to: `{UPI_ID}`
3️⃣ Amount: ₹{amount}
4️⃣ Add Note: `{reference}`
5️⃣ Take screenshot
6️⃣ Send to admin with:
   • Reference: `{reference}`
   • Screenshot

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ *Quick Pay:*
`upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={amount}&tn={reference}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 *Contact Admin:* @Anonononononon

⏱️ API activated in 5-10 minutes!

⚠️ *IMPORTANT:* Don't forget Reference ID!
                """
                
                keyboard = [
                    [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/Anonononononon")],
                    [InlineKeyboardButton("🔙 Back", callback_data='buy_api')],
                    [InlineKeyboardButton("« Menu", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(payment_msg, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Payment request failed. Try again!", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Payment system unavailable!", parse_mode='Markdown')

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

❌ No active API keys.

Get {DEFAULT_FREE_EXPIRY_DAYS}-day free trial!
        """
        keyboard = [
            [InlineKeyboardButton("🎁 Free Trial", callback_data='select_free')],
            [InlineKeyboardButton("💰 Plans", callback_data='buy_api')]
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
            
            expiry_text = "No expiry"
            if key.get('expiry_date'):
                try:
                    expiry = datetime.fromisoformat(key['expiry_date'])
                    days_left = (expiry - datetime.now()).days
                    expiry_text = f"{days_left} days left" if days_left > 0 else "Expired"
                except:
                    pass
            
            message += f"{plan_emoji} *{key.get('plan', 'N/A').upper()}*\n"
            message += f"`{key.get('api_key')}`\n"
            message += f"{expiry_text}\n\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔝 Upgrade", callback_data='buy_api')],
            [InlineKeyboardButton("« Menu", callback_data='back_to_menu')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def buy_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plans_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💰 *PRICING PLANS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

🆓 *FREE TRIAL* - ₹0
{DEFAULT_FREE_EXPIRY_DAYS} Days | All Features

💎 *BASIC* - ₹99/month
30 Days | Unlimited Requests

⭐ *PRO* - ₹299/month
30 Days | Priority + Advanced

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💸 Payment: UPI `{UPI_ID}`
    """
    
    keyboard = [
        [InlineKeyboardButton(f"🎁 {DEFAULT_FREE_EXPIRY_DAYS}D Free Trial", callback_data='select_free')],
        [InlineKeyboardButton("💎 Basic ₹99", callback_data='select_basic')],
        [InlineKeyboardButton("⭐ Pro ₹299", callback_data='select_pro')],
        [InlineKeyboardButton("« Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(plans_text, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    menu_text = f"""
🌟 *Premium API Store*

Powerful AI APIs:
🤖 Chat | 🎨 Images | 🎬 Videos | 💻 Code

🎁 Try free for {DEFAULT_FREE_EXPIRY_DAYS} days!
    """
    
    keyboard = [
        [InlineKeyboardButton("🎁 Free Trial", callback_data='select_free')],
        [InlineKeyboardButton("💰 Pricing", callback_data='buy_api'),
         InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
        [InlineKeyboardButton("❓ Help", callback_data='help_support')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    help_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ❓ *HELP & SUPPORT*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Commands:*
• `/start` - Main menu
• `/myapi` - View keys
• `/buy` - Plans

*Features:*
• AI Chat (Claude 3.5)
• Image Generation
• Video Generation
• Code Expert

*Payment:*
UPI: `{UPI_ID}`

*Support:*
@Anonononononon
    """
    
    keyboard = [[InlineKeyboardButton("« Menu", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

# Admin Commands
async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin verifies payment and activates API key"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if not PAYMENT_AVAILABLE:
        await update.message.reply_text("❌ Payment system unavailable!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "⚠️ Usage: `/verify REFERENCE_ID`\n\nExample:\n`/verify USER_123_BASIC`",
            parse_mode='Markdown'
        )
        return
    
    reference = context.args[0]
    payment = payment_handler.get_pending_payment(reference)
    
    if not payment:
        await update.message.reply_text(f"❌ Payment not found: `{reference}`", parse_mode='Markdown')
        return
    
    if payment['status'] != 'pending':
        await update.message.reply_text(f"⚠️ Already processed!")
        return
    
    # Generate API key
    api_key = db.create_api_key(
        telegram_id=payment['user_id'],
        username=payment['username'],
        plan=payment['plan'],
        expiry_days=30,
        created_by_admin=True
    )
    
    if api_key:
        # Mark payment as verified
        payment_handler.mark_payment_verified(reference)
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=payment['user_id'],
                text=f"""
✅ *Payment Verified!*

Your API key is activated!

*Plan:* {payment['plan'].upper()}
*API Key:*
`{api_key}`

*Valid for:* 30 days

🚀 Start using now!
                """,
                parse_mode='Markdown'
            )
        except:
            pass
        
        # Notify admin
        await update.message.reply_text(
            f"""
✅ *Payment Verified!*

Reference: `{reference}`
User: @{payment['username']}
Plan: {payment['plan'].upper()}
Amount: ₹{payment['amount']}

API Key: `{api_key}`

✅ User notified!
            """,
            parse_mode='Markdown'
        )
        
        # Notify channel
        if notifier:
            try:
                await notifier.notify_new_api_key(
                    username=payment['username'],
                    user_id=payment['user_id'],
                    plan=payment['plan'],
                    backend=f"Paid ₹{payment['amount']}"
                )
            except:
                pass
    else:
        await update.message.reply_text("❌ Failed to generate API key!")

async def pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending payments to admin"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if not PAYMENT_AVAILABLE:
        await update.message.reply_text("❌ Payment system unavailable!")
        return
    
    summary = payment_handler.get_admin_summary()
    await update.message.reply_text(summary, parse_mode='Markdown')

def main():
    # Start health server
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    logger.info("🚀 Starting Bot...")
    logger.info(f"🎁 Free Trial: {DEFAULT_FREE_EXPIRY_DAYS} days")
    logger.info(f"💸 Payment: UPI ({UPI_ID})")
    
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myapi", my_api_key))
    
    # Admin commands
    application.add_handler(CommandHandler("verify", verify_payment))
    application.add_handler(CommandHandler("pending", pending_payments))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(help_support, pattern='^help_support$'))
    
    logger.info("✅ Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()

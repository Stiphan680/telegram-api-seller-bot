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
DEFAULT_FREE_EXPIRY_DAYS = 7

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
            <p><strong>Payments:</strong> {'✅ Manual' if payment_handler else '❌ Disabled'}</p>
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

*🛠️ Admin Commands:*

*Gift Cards:*
• `/creategift <count> <days> <plan>` - Bulk create
• `/giftcards` - View all gift cards
• `/deletegift <code>` - Delete gift card

*API Management:*
• `/allkeys` - View all API keys
• `/deletekey <api_key>` - Delete any key

*Payments:*
• `/payments` - View pending payments
• `/verify <ref>` - Verify payment

*System:*
• `/stats` - Bot statistics
• `/backend` - AI status

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 System is running smoothly!
        """
        keyboard = [
            [InlineKeyboardButton("🎁 Gift Cards", callback_data='admin_gifts'),
             InlineKeyboardButton("🔑 All Keys", callback_data='admin_allkeys')],
            [InlineKeyboardButton("💳 Payments", callback_data='admin_payments'),
             InlineKeyboardButton("📊 Stats", callback_data='admin_stats')],
            [InlineKeyboardButton("📊 My Keys", callback_data='my_api'),
             InlineKeyboardButton("🤖 Backend", callback_data='check_backend')]
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
• `/redeem <code>` - Redeem gift card
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

# ============= GIFT CARD COMMANDS =============

async def create_gift_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin creates bulk gift cards: /creategift <count> <days> <plan>"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ *Usage:*\n\n`/creategift <count> <days> <plan>`\n\n*Examples:*\n"
            "`/creategift 5 7 free` - 5 cards, 7 days, FREE\n"
            "`/creategift 10 30 basic` - 10 cards, 30 days, BASIC\n"
            "`/creategift 3 90 pro` - 3 cards, 90 days, PRO\n"
            "`/creategift 1 0 pro` - 1 card, PERMANENT, PRO",
            parse_mode='Markdown'
        )
        return
    
    try:
        count = int(context.args[0])
        days = int(context.args[1])
        plan = context.args[2].lower()
        
        if plan not in ['free', 'basic', 'pro']:
            await update.message.reply_text("❌ Plan must be: free, basic, or pro")
            return
        
        if count < 1 or count > 100:
            await update.message.reply_text("❌ Count must be between 1 and 100")
            return
        
        # Create gift cards
        codes = []
        for i in range(count):
            code = db.create_gift_card(
                plan=plan,
                max_uses=1,  # Single use per card
                card_expiry_days=None,  # No card expiry
                api_expiry_days=days if days > 0 else None,  # 0 = permanent
                created_by=update.effective_user.id,
                note=f"Bulk created by admin"
            )
            if code:
                codes.append(code)
        
        # Format response
        expiry_text = "PERMANENT" if days == 0 else f"{days} days"
        message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *GIFT CARDS CREATED*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Created:* {len(codes)} cards
*Plan:* {plan.upper()}
*API Validity:* {expiry_text}
*Single Use:* Yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Gift Codes:*

"""
        for i, code in enumerate(codes, 1):
            message += f"{i}. `{code}`\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "💡 *Share these codes with users!*\n"
        message += "Users can redeem with: `/redeem <code>`"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except ValueError:
        await update.message.reply_text("❌ Invalid format! Count and days must be numbers.")
    except Exception as e:
        logger.error(f"Error creating gift cards: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def list_gift_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin views all gift cards"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    gifts = db.get_all_gift_cards()
    
    if not gifts:
        await update.message.reply_text("❌ No gift cards found.")
        return
    
    active_gifts = [g for g in gifts if g.get('is_active', False)]
    used_gifts = [g for g in gifts if g.get('used_count', 0) >= g.get('max_uses', 1)]
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🎁 *GIFT CARDS OVERVIEW*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Total:* {len(gifts)} cards
*Active:* {len(active_gifts)} available
*Redeemed:* {len(used_gifts)} fully used

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Active Gift Cards:*

"""
    
    for gift in active_gifts[:20]:  # Show first 20
        plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(gift.get('plan'), "❓")
        used = gift.get('used_count', 0)
        max_uses = gift.get('max_uses', 1)
        api_days = gift.get('api_expiry_days')
        expiry_text = "PERMANENT" if api_days is None else f"{api_days}d"
        
        message += f"{plan_emoji} `{gift['code']}`\n"
        message += f"   Plan: {gift['plan'].upper()} | Validity: {expiry_text}\n"
        message += f"   Used: {used}/{max_uses}\n\n"
    
    if len(active_gifts) > 20:
        message += f"\n_...and {len(active_gifts) - 20} more active cards_\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "💡 Use `/deletegift <code>` to remove a card"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def delete_gift_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin deletes a gift card: /deletegift GIFT-XXXX-XXXX-XXXX"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:*\n\n`/deletegift GIFT-XXXX-XXXX-XXXX`",
            parse_mode='Markdown'
        )
        return
    
    code = context.args[0].upper()
    
    # Check if exists
    gift = db.get_gift_card(code)
    if not gift:
        await update.message.reply_text(f"❌ Gift card `{code}` not found.", parse_mode='Markdown')
        return
    
    # Delete
    success = db.delete_gift_card(code)
    
    if success:
        await update.message.reply_text(
            f"✅ *Gift Card Deleted*\n\nCode: `{code}`\nPlan: {gift['plan'].upper()}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to delete gift card.")

async def redeem_gift_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User redeems a gift card: /redeem GIFT-XXXX-XXXX-XXXX"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:*\n\n`/redeem GIFT-XXXX-XXXX-XXXX`\n\n"
            "Enter your gift card code to redeem.",
            parse_mode='Markdown'
        )
        return
    
    code = context.args[0].upper()
    
    result = db.redeem_gift_card(code, user_id, username)
    
    if result['success']:
        expiry_text = "PERMANENT" if result['expiry_days'] is None else f"{result['expiry_days']} days"
        
        message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *GIFT CARD REDEEMED!*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Congratulations! Your API key is ready.

*Your API Key:*
`{result['api_key']}`

*Plan:* {result['plan'].upper()}
*Validity:* {expiry_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *You now have access to:*
• Claude 3.5 Sonnet AI
• 200K+ token context
• Advanced reasoning
• Multi-language support

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 Use `/myapi` to view all your keys!
        """
        
        # Notify admin
        if notifier:
            try:
                await notifier.notify_new_api_key(
                    username=username,
                    user_id=user_id,
                    plan=result['plan'],
                    backend=f"Gift: {code}"
                )
            except:
                pass
        
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *Error:* {result['error']}", parse_mode='Markdown')

# ============= API KEY MANAGEMENT =============

async def view_all_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin views ALL API keys"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    keys = db.get_all_api_keys()
    
    if not keys:
        await update.message.reply_text("❌ No API keys found.")
        return
    
    active_keys = [k for k in keys if k.get('is_active', False)]
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔑 *ALL API KEYS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Total:* {len(keys)} keys
*Active:* {len(active_keys)} keys

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Recent Active Keys:*

"""
    
    for key in active_keys[:15]:  # Show first 15
        plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(key.get('plan'), "❓")
        username = key.get('username', 'Unknown')
        user_id = key.get('telegram_id')
        expiry_info = format_expiry(key.get('expiry_date'))
        requests = key.get('requests_used', 0)
        
        message += f"{plan_emoji} @{username} (ID: {user_id})\n"
        message += f"   `{key['api_key'][:35]}...`\n"
        message += f"   {expiry_info} | {requests} requests\n\n"
    
    if len(active_keys) > 15:
        message += f"\n_...and {len(active_keys) - 15} more active keys_\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "💡 Use `/deletekey <api_key>` to remove a key"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def delete_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin deletes an API key: /deletekey sk-..."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:*\n\n`/deletekey sk-...`\n\nProvide the full API key.",
            parse_mode='Markdown'
        )
        return
    
    api_key = context.args[0]
    
    # Get key info first
    key = db.validate_api_key(api_key)
    if not key:
        await update.message.reply_text("❌ API key not found or already deleted.")
        return
    
    # Delete
    success = db.delete_api_key(api_key)
    
    if success:
        username = key.get('username', 'Unknown')
        plan = key.get('plan', 'unknown')
        
        await update.message.reply_text(
            f"✅ *API Key Deleted*\n\nUser: @{username}\nPlan: {plan.upper()}\nKey: `{api_key[:35]}...`",
            parse_mode='Markdown'
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=key['telegram_id'],
                text=f"⚠️ Your {plan.upper()} API key has been deactivated by admin.\n\nContact @Anonononononon for support."
            )
        except:
            pass
    else:
        await update.message.reply_text("❌ Failed to delete API key.")

# ============= STATS =============

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin views bot statistics"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    stats = db.get_stats()
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📊 *BOT STATISTICS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*👥 Users:*
Total Users: {stats.get('total_users', 0)}

*🔑 API Keys:*
Total Keys: {stats.get('total_keys', 0)}
Active Keys: {stats.get('active_keys', 0)}
Total Requests: {stats.get('total_requests', 0):,}

*🎁 Gift Cards:*
Total Cards: {stats.get('total_gifts', 0)}
Active Cards: {stats.get('active_gifts', 0)}
Total Redemptions: {stats.get('total_redemptions', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ System operational!
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ============= EXISTING FUNCTIONS (keeping same) =============

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
        logger.info(f"Showing payment instructions for {plan} plan")
        
        if payment_handler:
            try:
                payment_request = payment_handler.create_payment_request(
                    user_id=user_id,
                    username=username,
                    plan=plan,
                    amount=PLANS[plan]['price']
                )
                
                payment_msg = payment_request['instructions']
                
                keyboard = [
                    [InlineKeyboardButton("✅ I've Paid - Contact Admin", url="https://t.me/Anonononononon")],
                    [InlineKeyboardButton("« Choose Another Plan", callback_data='buy_api')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
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
• `/redeem <code>` - Redeem gift card
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
    user_id = update.effective_user.id
    
    if payment_handler:
        summary = payment_handler.get_payment_summary(user_id)
        await update.message.reply_text(summary, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Payment system not available")

async def admin_view_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    if payment_handler:
        summary = payment_handler.get_admin_summary()
        await update.message.reply_text(summary, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Payment system not available")

async def admin_verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            [InlineKeyboardButton("🎁 Gift Cards", callback_data='admin_gifts'),
             InlineKeyboardButton("🔑 All Keys", callback_data='admin_allkeys')],
            [InlineKeyboardButton("💳 Payments", callback_data='admin_payments'),
             InlineKeyboardButton("📊 Stats", callback_data='admin_stats')],
            [InlineKeyboardButton("📊 My Keys", callback_data='my_api'),
             InlineKeyboardButton("🤖 Backend", callback_data='check_backend')]
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
• `/redeem <code>` - Redeem gift
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

# Callback handlers for admin buttons
async def admin_gifts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Convert to command-style call
    update.message = update.callback_query.message
    await list_gift_cards(update, context)

async def admin_allkeys_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    update.message = update.callback_query.message
    await view_all_keys(update, context)

async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    update.message = update.callback_query.message
    await show_stats(update, context)

async def post_init(application: Application):
    logger.info("✅ Bot initialization complete")
    
    if notifier:
        try:
            backend_status = ai_router.get_backend_status() if ai_router else None
            await notifier.notify_bot_started(backend_status)
            logger.info("✅ Startup notification sent")
        except Exception as e:
            logger.error(f"❌ Startup notification failed: {e}")

async def on_error(update, context):
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
    # Start health check server in background
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("🌐 Health check server started")
    
    backend_status = ai_router.get_backend_status() if ai_router else {}
    logger.info("🚀 Starting Bot...")
    logger.info(f"🤖 Backends: {backend_status.get('available_backends', [])}")
    logger.info(f"📣 Notifications: {'Enabled' if notifier else 'Disabled'}")
    logger.info(f"💳 Payment: {'Manual' if payment_handler else 'Disabled'}")
    
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("backend", check_backend_status))
    application.add_handler(CommandHandler("myapi", my_api_key))
    application.add_handler(CommandHandler("payment", check_payment_status))
    application.add_handler(CommandHandler("payments", admin_view_payments))
    application.add_handler(CommandHandler("verify", admin_verify_payment))
    application.add_handler(CommandHandler("help", help_command))
    
    # Gift card commands
    application.add_handler(CommandHandler("creategift", create_gift_cards))
    application.add_handler(CommandHandler("giftcards", list_gift_cards))
    application.add_handler(CommandHandler("deletegift", delete_gift_card))
    application.add_handler(CommandHandler("redeem", redeem_gift_card))
    
    # API management commands
    application.add_handler(CommandHandler("allkeys", view_all_keys))
    application.add_handler(CommandHandler("deletekey", delete_api_key))
    application.add_handler(CommandHandler("stats", show_stats))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(help_support, pattern='^help_support$'))
    application.add_handler(CallbackQueryHandler(check_backend_status, pattern='^check_backend$'))
    application.add_handler(CallbackQueryHandler(admin_gifts_callback, pattern='^admin_gifts$'))
    application.add_handler(CallbackQueryHandler(admin_allkeys_callback, pattern='^admin_allkeys$'))
    application.add_handler(CallbackQueryHandler(admin_stats_callback, pattern='^admin_stats$'))
    
    application.add_error_handler(on_error)
    
    logger.info("✅ Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()

import os
import logging
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError
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

# Configuration
ADMIN_ID = 5451167865
DEFAULT_FREE_EXPIRY_DAYS = 2
REQUIRED_CHANNEL = "@ShadowAPIstore"  # Channel to join
REQUIRED_CHANNEL_ID = "-1002705568330"  # Channel ID for verification
REFERRALS_FOR_FREE_API = 2  # Number of referrals needed for free trial

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
            <p><strong>Free Trial:</strong> {DEFAULT_FREE_EXPIRY_DAYS} days</p>
            <p><strong>Referral System:</strong> ✅ Active (Need {REFERRALS_FOR_FREE_API} refs)</p>
            <p><strong>Required Channel:</strong> {REQUIRED_CHANNEL}</p>
            <hr>
            <h2>📊 Statistics</h2>
            <p>Total Users: {stats.get('total_users', 0)}</p>
            <p>Active API Keys: {stats.get('active_keys', 0)}</p>
            <p>Total Referrals: {stats.get('total_referrals', 0)}</p>
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

# Plans
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
        'features': [
            '✅ Unlimited Requests',
            '✅ All Features',
            '✅ 30 days validity'
        ]
    },
    'pro': {
        'name': 'Pro Plan',
        'price': 299,
        'features': [
            '✅ Priority Support',
            '✅ Advanced Features',
            '✅ 30 days validity'
        ]
    }
}

def is_admin(user_id):
    return user_id == ADMIN_ID

async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user is member of required channel"""
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    # Check if user came via referral link
    if context.args and len(context.args) > 0:
        referrer_id = context.args[0].replace('ref_', '')
        try:
            referrer_id = int(referrer_id)
            if referrer_id != user_id:
                # Check if user already exists
                existing_user = db.users.find_one({'telegram_id': user_id})
                if not existing_user:
                    # Check channel membership first
                    is_member = await check_channel_membership(context, user_id)
                    if is_member:
                        # Add referral
                        db.add_referral(referrer_id, user_id, username)
                        
                        # Notify referrer
                        try:
                            ref_count = db.get_referral_count(referrer_id)
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text=f"🎉 *New Referral!*\n\n@{username} joined using your link!\n\n📊 Total Referrals: {ref_count}/{REFERRALS_FOR_FREE_API}\n\n" + 
                                     (f"✅ You can now claim your free trial!" if ref_count >= REFERRALS_FOR_FREE_API else f"Need {REFERRALS_FOR_FREE_API - ref_count} more for free trial!"),
                                parse_mode='Markdown'
                            )
                        except:
                            pass
        except:
            pass
    
    # Register user
    db.register_user(user_id, username)
    
    # Get referral stats
    ref_count = db.get_referral_count(user_id)
    ref_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    
    if is_admin(user_id):
        welcome_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   👑 *ADMIN DASHBOARD*   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Welcome back, Admin!

📊 *Quick Actions:*
Use buttons below or commands
        """
        keyboard = [
            [InlineKeyboardButton("🎁 Gift Cards", callback_data='admin_gifts'),
             InlineKeyboardButton("🔑 All Keys", callback_data='admin_allkeys')],
            [InlineKeyboardButton("💳 Payments", callback_data='admin_payments'),
             InlineKeyboardButton("📊 Stats", callback_data='admin_stats')],
            [InlineKeyboardButton("👥 Referrals", callback_data='admin_referrals')]
        ]
    else:
        welcome_text = f"""
🎉 *Welcome to Shadow API Store!*

Hello {user.first_name}!

💎 *Premium AI Features:*
🤖 AI Chat (Claude 3.5)
🎨 Image Generation (1024x1024)
🎬 Video Generation (HD)
💻 Code Expert Assistant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 *Get Free Trial:*
Invite {REFERRALS_FOR_FREE_API} friends to get {DEFAULT_FREE_EXPIRY_DAYS}-day free trial!

📊 *Your Referrals:* {ref_count}/{REFERRALS_FOR_FREE_API}
🔗 *Your Link:* `{ref_link}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *Important:* Friends must join {REQUIRED_CHANNEL} for referral to count!
        """
        
        if ref_count >= REFERRALS_FOR_FREE_API:
            keyboard = [
                [InlineKeyboardButton("🎁 Claim Free Trial", callback_data='claim_free_trial')],
                [InlineKeyboardButton("💰 Buy Premium", callback_data='buy_api'),
                 InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
                [InlineKeyboardButton("👥 My Referrals", callback_data='my_referrals')]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton(f"📢 Join Channel ({REQUIRED_CHANNEL})", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
                [InlineKeyboardButton("💰 Buy Premium", callback_data='buy_api'),
                 InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
                [InlineKeyboardButton("👥 My Referrals", callback_data='my_referrals')]
            ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def claim_free_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim free trial using referrals"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    # Check referral count
    ref_count = db.get_referral_count(user_id)
    
    if ref_count < REFERRALS_FOR_FREE_API:
        await query.edit_message_text(
            f"❌ *Not Enough Referrals!*\n\nYou have {ref_count}/{REFERRALS_FOR_FREE_API} referrals.\n\nInvite {REFERRALS_FOR_FREE_API - ref_count} more friends!",
            parse_mode='Markdown'
        )
        return
    
    # Check if already claimed
    if db.has_active_plan(user_id, 'free'):
        await query.edit_message_text(
            "⚠️ *Already Active!*\n\nYou already have an active free trial.",
            parse_mode='Markdown'
        )
        return
    
    # Generate free API key
    await query.edit_message_text("⏳ *Generating your free API key...*", parse_mode='Markdown')
    
    api_key = db.create_api_key(user_id, username, 'free', expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
    
    if api_key:
        # Mark referrals as used
        db.mark_referrals_used(user_id)
        
        success_message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ✅ *FREE TRIAL ACTIVATED*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Congratulations! 🎉

*Your API Key:*
`{api_key}`

*Plan:* FREE TRIAL
*Validity:* {DEFAULT_FREE_EXPIRY_DAYS} days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *You now have access to:*
✅ AI Chat (Claude 3.5 Sonnet)
✅ Image Generation (1024x1024)
✅ Video Generation (HD)
✅ Code Expert Assistant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 API Docs: /myapi
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 View My Keys", callback_data='my_api')],
            [InlineKeyboardButton("« Main Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Notify admin
        if notifier:
            try:
                await notifier.notify_new_api_key(
                    username=username,
                    user_id=user_id,
                    plan='free',
                    backend=f"Referral (2 refs)"
                )
            except:
                pass
    else:
        await query.edit_message_text("❌ Failed to generate API key. Try again!", parse_mode='Markdown')

async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's referrals"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    ref_count = db.get_referral_count(user_id)
    referrals = db.get_user_referrals(user_id)
    ref_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  👥 *YOUR REFERRALS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📊 *Stats:*
Total Referrals: {ref_count}
Required: {REFERRALS_FOR_FREE_API}
Progress: {'✅ Completed!' if ref_count >= REFERRALS_FOR_FREE_API else f'{ref_count}/{REFERRALS_FOR_FREE_API}'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 *Your Referral Link:*
`{ref_link}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 *Recent Referrals:*
"""
    
    if referrals:
        for idx, ref in enumerate(referrals[:5], 1):
            status = "✅" if ref.get('is_used') else "🟢"
            message += f"{status} @{ref.get('referred_username', 'User')}\n"
    else:
        message += "No referrals yet.\n"
    
    message += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💡 *How it works:*\n1. Share your link\n2. Friends join {REQUIRED_CHANNEL}\n3. Get {REFERRALS_FOR_FREE_API} referrals\n4. Claim free trial!"
    
    keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

# Admin Functions
async def admin_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin view all referrals"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔ Admin only!")
        return
    
    stats = db.get_referral_stats()
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📊 *REFERRAL STATS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Overview:*
Total Users: {stats['total_users']}
Total Referrals: {stats['total_referrals']}
Claimed Trials: {stats['claimed_trials']}

*Top Referrers:*
"""
    
    for idx, user in enumerate(stats['top_referrers'][:10], 1):
        message += f"{idx}. @{user['username']}: {user['count']} refs\n"
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    gifts = db.get_all_gift_cards()
    active = [g for g in gifts if g.get('is_active')]
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🎁 *GIFT CARDS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Total: {len(gifts)}
Active: {len(active)}

Use `/creategift` to create new cards.
    """
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_allkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    keys = db.get_all_api_keys()
    active = [k for k in keys if k.get('is_active')]
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔑 *ALL API KEYS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Total Keys: {len(keys)}
Active: {len(active)}

Use `/allkeys` for detailed list.
    """
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    if payment_handler:
        summary = payment_handler.get_admin_summary()
        keyboard = [[InlineKeyboardButton("« Back", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await query.edit_message_text("❌ Payment system not available")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    stats = db.get_stats()
    ref_stats = db.get_referral_stats()
    
    message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📊 *BOT STATISTICS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Users:*
Total: {stats.get('total_users', 0)}

*API Keys:*
Total: {stats.get('total_keys', 0)}
Active: {stats.get('active_keys', 0)}
Requests: {stats.get('total_requests', 0):,}

*Referrals:*
Total: {ref_stats['total_referrals']}
Claimed: {ref_stats['claimed_trials']}

*Gift Cards:*
Active: {stats.get('active_gifts', 0)}
    """
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

# Other handlers
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
        ref_count = db.get_referral_count(user_id)
        message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔑 *YOUR API KEYS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

❌ No active API keys.

🎁 Get free trial by referring {REFERRALS_FOR_FREE_API} friends!
Your referrals: {ref_count}/{REFERRALS_FOR_FREE_API}
        """
        keyboard = [
            [InlineKeyboardButton("👥 My Referrals", callback_data='my_referrals')],
            [InlineKeyboardButton("💰 Buy Premium", callback_data='buy_api')]
        ]
    else:
        message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔑 *YOUR API KEYS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

You have {len(keys)} active key(s):

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
            
            message += f"{plan_emoji} *{key.get('plan', 'N/A').upper()}*\n`{key.get('api_key')}`\n{expiry_text}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔝 Upgrade Plan", callback_data='buy_api')],
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

🆓 *FREE TRIAL*
Refer {REFERRALS_FOR_FREE_API} friends → Get {DEFAULT_FREE_EXPIRY_DAYS} days free!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 *BASIC PLAN*
₹99/month | Unlimited

⭐ *PRO PLAN*
₹299/month | Priority

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 Contact admin for payment:
@Anonononononon
    """
    
    keyboard = [
        [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/Anonononononon")],
        [InlineKeyboardButton("« Back", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(plans_text, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    ref_count = db.get_referral_count(user_id)
    
    menu_text = f"""
🎉 *Shadow API Store*

💎 Premium AI Features
🎁 Refer & Earn Free Trial

📊 Your Referrals: {ref_count}/{REFERRALS_FOR_FREE_API}
    """
    
    if ref_count >= REFERRALS_FOR_FREE_API:
        keyboard = [
            [InlineKeyboardButton("🎁 Claim Free Trial", callback_data='claim_free_trial')],
            [InlineKeyboardButton("💰 Buy Premium", callback_data='buy_api'),
             InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
            [InlineKeyboardButton("👥 Referrals", callback_data='my_referrals')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"📢 Join {REQUIRED_CHANNEL}", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("💰 Buy Premium", callback_data='buy_api'),
             InlineKeyboardButton("📊 My Keys", callback_data='my_api')],
            [InlineKeyboardButton("👥 Referrals", callback_data='my_referrals')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    logger.info("🚀 Starting Bot...")
    logger.info(f"🎁 Free Trial: {DEFAULT_FREE_EXPIRY_DAYS} days")
    logger.info(f"👥 Referrals needed: {REFERRALS_FOR_FREE_API}")
    logger.info(f"📢 Required channel: {REQUIRED_CHANNEL}")
    
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myapi", my_api_key))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(claim_free_trial, pattern='^claim_free_trial$'))
    application.add_handler(CallbackQueryHandler(my_referrals, pattern='^my_referrals$'))
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    
    # Admin callbacks
    application.add_handler(CallbackQueryHandler(admin_referrals, pattern='^admin_referrals$'))
    application.add_handler(CallbackQueryHandler(admin_gifts, pattern='^admin_gifts$'))
    application.add_handler(CallbackQueryHandler(admin_allkeys, pattern='^admin_allkeys$'))
    application.add_handler(CallbackQueryHandler(admin_payments, pattern='^admin_payments$'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    
    logger.info("✅ Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

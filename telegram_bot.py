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

# NEW: Import API Key Tester
try:
    from api_key_tester import get_api_key_tester
    api_tester = get_api_key_tester()
    TESTER_AVAILABLE = True
except ImportError:
    TESTER_AVAILABLE = False
    api_tester = None
    print("⚠️ API Key Tester not available")

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
            <p><strong>API Tester:</strong> {'✅ Enabled' if api_tester else '❌ Disabled'}</p>
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
            return "🧠 *Powered by Perplexity + Claude*\nAdvanced search with Claude 3.5 Sonnet\n💎 Premium AI with real-time web search"
        return "🧠 *Powered by Claude 3.5 Sonnet*\nAnthropic's flagship AI model\n💎 Enterprise-grade intelligence"
    return "🧠 *Powered by Claude 3.5 Sonnet*\nPremium AI by Anthropic"

# ============= NEW: API KEY TESTER COMMAND =============

async def test_api_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test an API key: /testapi <api_key>"""
    if not TESTER_AVAILABLE or not api_tester:
        await update.message.reply_text("❌ API key testing is not available.")
        return
    
    if not context.args:
        help_msg = """┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔍 *TEST YOUR API KEY*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

*Usage:*
`/testapi <your_api_key>`

*Example:*
`/testapi sk-ant-api03-abc...`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*What it checks:*
✅ Database validation
✅ API gateway connection
✅ Chat endpoint functionality
✅ Expiry status
✅ Request count

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Paste your API key after the command!"""
        await update.message.reply_text(help_msg, parse_mode='Markdown')
        return
    
    api_key = context.args[0].strip()
    test_msg = await update.message.reply_text("🔍 *Testing your API key...*\n\nPlease wait, this may take 10-30 seconds.", parse_mode='Markdown')
    
    try:
        result_text = await api_tester.quick_test(api_key)
        await test_msg.edit_text(f"""┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🔍 *API KEY TEST RESULTS*  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

{result_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Use `/myapi` to view all your keys""", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"API test error: {e}")
        await test_msg.edit_text(f"❌ *Test Failed*\n\nError: {str(e)}\n\nPlease try again or contact support.", parse_mode='Markdown')

# =============  REST OF THE CODE (UNCHANGED) =============


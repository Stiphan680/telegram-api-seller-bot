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
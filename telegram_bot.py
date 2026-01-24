import os
import logging
import asyncio
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import Database
from config import Config

# Import AI Router, Notification Manager, Manual Payment, and System Monitor
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

try:
    from system_monitor import get_system_monitor
    SYSTEM_MONITOR_AVAILABLE = True
except ImportError:
    SYSTEM_MONITOR_AVAILABLE = False
    print("⚠️ System Monitor not available")

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

# Initialize System Monitor
SYSTEM_CHANNEL_ID = "-1003350605488"  # Your monitoring channel
if SYSTEM_MONITOR_AVAILABLE:
    try:
        system_monitor = get_system_monitor(Config.TELEGRAM_BOT_TOKEN, SYSTEM_CHANNEL_ID)
        logger.info(f"✅ System Monitor initialized for channel {SYSTEM_CHANNEL_ID}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize system monitor: {e}")
        system_monitor = None
else:
    system_monitor = None

# Admin ID
ADMIN_ID = 5451167865
DEFAULT_FREE_EXPIRY_DAYS = 2

# Payment UPI ID
UPI_ID = "aman4380@kphdfc"
UPI_NAME = "Aman"

# Check admin
def is_admin(user_id):
    return user_id == ADMIN_ID

# Escape markdown special characters
def escape_markdown(text):
    """Escape special characters for Markdown"""
    if not text:
        return text
    # Escape markdown special characters
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Health Check Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            stats = db.get_stats()
            status_html = f"""
            <html>
            <head><title>Bot Status</title></head>
            <body style="font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff;">
                <h1>Telegram Bot - Active</h1>
                <p><strong>Status:</strong> OK</p>
                <p><strong>Admin ID:</strong> {ADMIN_ID}</p>
                <p><strong>AI Router:</strong> {'Connected' if ai_router else 'Disabled'}</p>
                <p><strong>Notifications:</strong> {'Enabled' if notifier else 'Disabled'}</p>
                <p><strong>System Monitor:</strong> {'Active' if system_monitor else 'Disabled'}</p>
                <p><strong>Payments:</strong> UPI {UPI_ID}</p>
                <hr>
                <h2>Statistics</h2>
                <p>Total Users: {stats.get('total_users', 0)}</p>
                <p>Active API Keys: {stats.get('active_keys', 0)}</p>
                <p>Total Requests: {stats.get('total_requests', 0)}</p>
                <hr>
                <small>Premium API Gateway</small>
            </body>
            </html>
            """
            self.wfile.write(status_html.encode())
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"500 Internal Server Error")
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    """Run health check server on port 10000 for Render"""
    try:
        # Use fixed port 10000 for Render
        port = 10000
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🌐 Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Failed to start health server: {e}")
        # Don't fail - bot can work without health server

# API Plans
PLANS = {
    'free': {
        'name': 'Free Trial',
        'price': 0,
        'description': f'Experience our AI API free for {DEFAULT_FREE_EXPIRY_DAYS} days',
        'features': [
            'All Premium Features',
            'AI Chat (Claude 3.5)',
            'Image Generation',
            'Video Generation',
            'Code Expert',
            f'{DEFAULT_FREE_EXPIRY_DAYS} days validity'
        ]
    },
    'basic': {
        'name': 'Basic Plan',
        'price': 99,
        'description': 'Perfect for individuals',
        'features': [
            'Unlimited Requests',
            'All Features',
            'Priority Support',
            '30 days validity'
        ]
    },
    'pro': {
        'name': 'Pro Plan',
        'price': 299,
        'description': 'Best for professionals',
        'features': [
            'Everything in Basic',
            'Advanced Models',
            '24/7 Support',
            '30 days validity'
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        is_new = db.register_user(user.id, user.username or user.first_name)
        
        # Notify about new user
        if system_monitor and is_new:
            try:
                await system_monitor.notify_new_user(user.username or user.first_name, user.id)
            except Exception as e:
                logger.error(f"Failed to notify new user: {e}")
        
        welcome_message = f"""Welcome to Premium API Store!

Hello {user.first_name}!

AI Chat - Claude 3.5 Sonnet
Image Generation - Flux AI
Video Generation - Mochi AI
Code Expert - Claude Assistant

Get {DEFAULT_FREE_EXPIRY_DAYS}-Day Free Trial!
Try all features completely free!
        """
        
        keyboard = [
            [InlineKeyboardButton(f"Get {DEFAULT_FREE_EXPIRY_DAYS}D Free Trial", callback_data='select_free')],
            [InlineKeyboardButton("View Pricing", callback_data='buy_api'),
             InlineKeyboardButton("My Keys", callback_data='my_api')],
            [InlineKeyboardButton("Help", callback_data='help_support')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("Error starting bot. Please try again.")

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        plan = query.data.replace('select_', '')
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        
        has_plan = db.has_active_plan(user_id, plan)
        if has_plan:
            await query.edit_message_text(
                f"Already Active!\n\nYou already have an active {plan.upper()} plan.\n\nUse /myapi to view your keys."
            )
            return
        
        if plan == 'free':
            await query.edit_message_text("Generating your free API key...\n\nPlease wait.")
            
            api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
            
            if api_key:
                success_message = f"""API KEY GENERATED

Congratulations!

Your API Key:
{api_key}

Plan: FREE TRIAL
Validity: {DEFAULT_FREE_EXPIRY_DAYS} days
Features: All premium features!

Access to:
AI Chat, Images, Videos, Code

Use /myapi to view keys!
                """
                
                if notifier:
                    try:
                        await notifier.notify_new_api_key(username=username, user_id=user_id, plan=plan, backend=f"Free ({DEFAULT_FREE_EXPIRY_DAYS}d)")
                    except:
                        pass
                
                keyboard = [
                    [InlineKeyboardButton("My Keys", callback_data='my_api')],
                    [InlineKeyboardButton("Upgrade", callback_data='buy_api')],
                    [InlineKeyboardButton("Menu", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(success_message, reply_markup=reply_markup)
            else:
                await query.edit_message_text("Error!\n\nFailed to generate API key.")
        else:
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
                    
                    payment_msg = f"""PAYMENT DETAILS

Plan: {PLANS[plan]['name']}
Amount: {amount}
Reference: {reference}

UPI Payment Method

UPI ID:
{UPI_ID}

Name: {UPI_NAME}
Amount: {amount}

Payment Steps:

1. Open UPI app (GPay/PhonePe/Paytm)
2. Pay to: {UPI_ID}
3. Amount: {amount}
4. Add Note: {reference}
5. Take screenshot
6. Click I Have Paid button

API activated in 5-10 minutes!

IMPORTANT: Don't forget Reference ID!
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("I Have Paid", callback_data=f'paid_{reference}')],
                        [InlineKeyboardButton("Contact Admin", url="https://t.me/Anonononononon")],
                        [InlineKeyboardButton("Back", callback_data='buy_api')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(payment_msg, reply_markup=reply_markup)
                else:
                    await query.edit_message_text("Payment request failed. Try again!")
            else:
                await query.edit_message_text("Payment system unavailable!")
    except Exception as e:
        logger.error(f"Error in select_plan: {e}")
        await query.answer("Error processing request", show_alert=True)

async def payment_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'I Have Paid' button click"""
    try:
        query = update.callback_query
        await query.answer()
        
        reference = query.data.replace('paid_', '')
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        
        if not PAYMENT_AVAILABLE:
            await query.edit_message_text("Payment system unavailable!")
            return
        
        payment = payment_handler.get_pending_payment(reference)
        
        if not payment:
            await query.edit_message_text("Payment not found!")
            return
        
        await query.edit_message_text(
            f"""Payment Notification Sent!

Your payment has been reported to admin.

Reference: {reference}
Amount: {payment['amount']}
Plan: {payment['plan'].upper()}

Admin will verify your payment

Expected time: 5-10 minutes
You'll get API key automatically

Need help? Contact @Anonononononon
            """
        )
        
        # Notify system monitor (channel notification)
        if system_monitor:
            try:
                await system_monitor.notify_payment_received(
                    username=username,
                    user_id=user_id,
                    plan=payment['plan'],
                    amount=payment['amount'],
                    reference=reference
                )
            except Exception as e:
                logger.error(f"Failed to notify payment to channel: {e}")
        
        # Send direct notification to admin
        try:
            admin_notification = f"""NEW PAYMENT NOTIFICATION

USER DETAILS
Username: @{username}
User ID: {user_id}

PAYMENT DETAILS  
Plan: {payment['plan'].upper()}
Amount: {payment['amount']}
Reference: {reference}

TIME
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            admin_keyboard = [
                [InlineKeyboardButton("Verify & Activate API", callback_data=f'verify_{reference}')],
                [InlineKeyboardButton("View All Pending", callback_data='admin_pending')]
            ]
            admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_notification,
                reply_markup=admin_reply_markup
            )
            
            logger.info(f"✅ Payment notification sent to admin for {username} - {reference}")
            
        except Exception as e:
            logger.error(f"❌ Failed to notify admin: {e}")
            try:
                fallback_msg = f"NEW PAYMENT\n\nUser: @{username} (ID: {user_id})\nPlan: {payment['plan'].upper()}\nAmount: {payment['amount']}\nRef: {reference}\n\nUse /verify {reference} to activate"
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=fallback_msg
                )
                logger.info("✅ Sent fallback notification to admin")
            except Exception as e2:
                logger.error(f"❌ Fallback notification also failed: {e2}")
    except Exception as e:
        logger.error(f"Error in payment_done_handler: {e}")
        await query.answer("Error processing payment", show_alert=True)

async def verify_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin verifies payment from button"""
    try:
        query = update.callback_query
        await query.answer()
        
        if not is_admin(query.from_user.id):
            await query.answer("Admin only!", show_alert=True)
            return
        
        reference = query.data.replace('verify_', '')
        
        if not PAYMENT_AVAILABLE:
            await query.answer("Payment system unavailable!", show_alert=True)
            return
        
        payment = payment_handler.get_pending_payment(reference)
        
        if not payment:
            await query.answer("Payment not found!", show_alert=True)
            return
        
        if payment['status'] != 'pending':
            await query.answer("Already verified!", show_alert=True)
            return
        
        api_key = db.create_api_key(
            telegram_id=payment['user_id'],
            username=payment['username'],
            plan=payment['plan'],
            expiry_days=30,
            created_by_admin=True
        )
        
        if api_key:
            payment_handler.mark_payment_verified(reference)
            
            if system_monitor:
                try:
                    await system_monitor.notify_payment_verified(
                        username=payment['username'],
                        user_id=payment['user_id'],
                        plan=payment['plan'],
                        amount=payment['amount'],
                        api_key=api_key
                    )
                except Exception as e:
                    logger.error(f"Failed to notify payment verified: {e}")
            
            try:
                await context.bot.send_message(
                    chat_id=payment['user_id'],
                    text=f"""Payment Verified!

Your API key is activated!

Plan: {payment['plan'].upper()}
API Key:
{api_key}

Valid for: 30 days

Start using now!
Support: @Anonononononon
                    """
                )
            except:
                pass
            
            await query.edit_message_text(
                f"""Payment Verified Successfully!

Reference: {reference}
User: @{payment['username']}
Plan: {payment['plan'].upper()}
Amount: {payment['amount']}

API Key: {api_key}

User notified automatically!
                """
            )
            
            if notifier:
                try:
                    await notifier.notify_new_api_key(
                        username=payment['username'],
                        user_id=payment['user_id'],
                        plan=payment['plan'],
                        backend=f"Paid {payment['amount']}"
                    )
                except:
                    pass
        else:
            await query.answer("Failed to generate API key!", show_alert=True)
            if system_monitor:
                try:
                    await system_monitor.notify_error("API Generation", "Failed to create API key", f"Payment: {reference}")
                except:
                    pass
    except Exception as e:
        logger.error(f"Error in verify_from_button: {e}")
        await query.answer("Error verifying payment", show_alert=True)

async def admin_pending_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending payments from button"""
    try:
        query = update.callback_query
        await query.answer()
        
        if not is_admin(query.from_user.id):
            await query.answer("Admin only!", show_alert=True)
            return
        
        if not PAYMENT_AVAILABLE:
            await query.answer("Payment system unavailable!", show_alert=True)
            return
        
        summary = payment_handler.get_admin_summary()
        await query.edit_message_text(summary)
    except Exception as e:
        logger.error(f"Error in admin_pending_button: {e}")
        await query.answer("Error loading pending payments", show_alert=True)

async def my_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
            message = f"""YOUR API KEYS

No active API keys.

Get {DEFAULT_FREE_EXPIRY_DAYS}-day free trial!
            """
            keyboard = [
                [InlineKeyboardButton("Free Trial", callback_data='select_free')],
                [InlineKeyboardButton("Plans", callback_data='buy_api')]
            ]
        else:
            message = f"""YOUR API KEYS

You have {len(keys)} active key(s):

"""
            for idx, key in enumerate(keys, 1):
                plan_emoji = {"free": "F", "basic": "B", "pro": "P"}.get(key.get('plan'), "?")
                
                expiry_text = "No expiry"
                if key.get('expiry_date'):
                    try:
                        expiry = datetime.fromisoformat(key['expiry_date'])
                        days_left = (expiry - datetime.now()).days
                        expiry_text = f"{days_left} days left" if days_left > 0 else "Expired"
                    except:
                        pass
                
                message += f"{plan_emoji} {key.get('plan', 'N/A').upper()}\n"
                message += f"{key.get('api_key')}\n"
                message += f"{expiry_text}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("Upgrade", callback_data='buy_api')],
                [InlineKeyboardButton("Menu", callback_data='back_to_menu')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if edit_message:
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in my_api_key: {e}")
        if edit_message:
            await query.answer("Error loading API keys", show_alert=True)
        else:
            await update.message.reply_text("Error loading API keys")

async def buy_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        plans_text = f"""PRICING PLANS

FREE TRIAL - 0
{DEFAULT_FREE_EXPIRY_DAYS} Days | All Features

BASIC - 99/month
30 Days | Unlimited Requests

PRO - 299/month
30 Days | Priority + Advanced

Payment: UPI {UPI_ID}
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{DEFAULT_FREE_EXPIRY_DAYS}D Free Trial", callback_data='select_free')],
            [InlineKeyboardButton("Basic 99", callback_data='select_basic')],
            [InlineKeyboardButton("Pro 299", callback_data='select_pro')],
            [InlineKeyboardButton("Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(plans_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in buy_api: {e}")
        await query.answer("Error loading plans", show_alert=True)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        menu_text = f"""Premium API Store

Powerful AI APIs:
Chat | Images | Videos | Code

Try free for {DEFAULT_FREE_EXPIRY_DAYS} days!
        """
        
        keyboard = [
            [InlineKeyboardButton("Free Trial", callback_data='select_free')],
            [InlineKeyboardButton("Pricing", callback_data='buy_api'),
             InlineKeyboardButton("My Keys", callback_data='my_api')],
            [InlineKeyboardButton("Help", callback_data='help_support')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(menu_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in back_to_menu: {e}")
        await query.answer("Error loading menu", show_alert=True)

async def help_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        help_text = f"""HELP & SUPPORT

Commands:
/start - Main menu
/myapi - View keys
/buy - Plans
/redeem CODE - Use gift card

Features:
AI Chat (Claude 3.5)
Image Generation
Video Generation
Code Expert

Payment:
UPI: {UPI_ID}

Support:
@Anonononononon
        """
        
        keyboard = [[InlineKeyboardButton("Menu", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in help_support: {e}")
        await query.answer("Error loading help", show_alert=True)

# ========== ADMIN COMMANDS ==========

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        stats = db.get_stats()
        
        panel_text = f"""ADMIN PANEL

Statistics:
Total Users: {stats.get('total_users', 0)}
Active API Keys: {stats.get('active_keys', 0)}
Total Requests: {stats.get('total_requests', 0)}

Payment Commands:
/pending - View pending payments
/verify REF - Verify payment

Gift Card Commands:
/giftgen PLAN DAYS COUNT - Generate gift cards
/giftlist - View all gift cards
/giftdel CODE - Delete gift card

API Management:
/apilist - View all API keys
/apicreate USER_ID PLAN DAYS - Create API key
/apidel API_KEY - Delete API key

Stats:
/stats - Detailed statistics
/admin - This panel

Admin ID: {ADMIN_ID}
        """
        
        await update.message.reply_text(panel_text)
    except Exception as e:
        logger.error(f"Error in admin_panel: {e}")
        await update.message.reply_text("Error loading admin panel")

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin verifies payment via command"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        if not PAYMENT_AVAILABLE:
            await update.message.reply_text("Payment system unavailable!")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "Usage: /verify REFERENCE_ID\n\nExample:\n/verify USER_123_BASIC"
            )
            return
        
        reference = context.args[0]
        payment = payment_handler.get_pending_payment(reference)
        
        if not payment:
            await update.message.reply_text(f"Payment not found: {reference}")
            return
        
        if payment['status'] != 'pending':
            await update.message.reply_text("Already processed!")
            return
        
        api_key = db.create_api_key(
            telegram_id=payment['user_id'],
            username=payment['username'],
            plan=payment['plan'],
            expiry_days=30,
            created_by_admin=True
        )
        
        if api_key:
            payment_handler.mark_payment_verified(reference)
            
            if system_monitor:
                try:
                    await system_monitor.notify_payment_verified(
                        username=payment['username'],
                        user_id=payment['user_id'],
                        plan=payment['plan'],
                        amount=payment['amount'],
                        api_key=api_key
                    )
                except Exception as e:
                    logger.error(f"Failed to notify payment verified: {e}")
            
            try:
                await context.bot.send_message(
                    chat_id=payment['user_id'],
                    text=f"""Payment Verified!

Your API key is activated!

Plan: {payment['plan'].upper()}
API Key:
{api_key}

Valid for: 30 days

Start using now!
                    """
                )
            except:
                pass
            
            await update.message.reply_text(
                f"""Payment Verified!

Reference: {reference}
User: @{payment['username']}
Plan: {payment['plan'].upper()}
Amount: {payment['amount']}

API Key: {api_key}

User notified!
                """
            )
            
            if notifier:
                try:
                    await notifier.notify_new_api_key(
                        username=payment['username'],
                        user_id=payment['user_id'],
                        plan=payment['plan'],
                        backend=f"Paid {payment['amount']}"
                    )
                except:
                    pass
        else:
            await update.message.reply_text("Failed to generate API key!")
    except Exception as e:
        logger.error(f"Error in verify_payment: {e}")
        await update.message.reply_text(f"Error verifying payment: {str(e)}")

async def pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending payments to admin"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        if not PAYMENT_AVAILABLE:
            await update.message.reply_text("Payment system unavailable!")
            return
        
        summary = payment_handler.get_admin_summary()
        await update.message.reply_text(summary)
    except Exception as e:
        logger.error(f"Error in pending_payments: {e}")
        await update.message.reply_text(f"Error loading pending payments: {str(e)}")

# Gift Card System
async def generate_gift_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate gift cards - /giftgen PLAN DAYS COUNT"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "Usage: /giftgen PLAN DAYS COUNT\n\nExample:\n/giftgen basic 30 5\n/giftgen pro 60 10"
            )
            return
        
        plan = context.args[0].lower()
        try:
            days = int(context.args[1])
            count = int(context.args[2])
        except:
            await update.message.reply_text("Days and count must be numbers!")
            return
        
        if plan not in ['free', 'basic', 'pro']:
            await update.message.reply_text("Invalid plan! Use: free, basic, or pro")
            return
        
        if count > 50:
            await update.message.reply_text("Max 50 gift cards at once!")
            return
        
        codes = []
        for i in range(count):
            code = db.create_gift_card(plan=plan, max_uses=1, api_expiry_days=days, created_by=ADMIN_ID)
            if code:
                codes.append(code)
        
        if codes:
            if system_monitor:
                try:
                    await system_monitor.notify_gift_generated(plan=plan, days=days, count=len(codes), admin_id=ADMIN_ID)
                except Exception as e:
                    logger.error(f"Failed to notify gift generated: {e}")
            
            codes_text = "\n".join([code for code in codes])
            message = f"""Gift Cards Generated!

Plan: {plan.upper()}
Validity: {days} days
Count: {len(codes)}

Codes:
{codes_text}

Users can redeem with:
/redeem CODE
            """
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("Failed to generate gift cards!")
    except Exception as e:
        logger.error(f"Error in generate_gift_cards: {e}")
        await update.message.reply_text(f"Error generating gift cards: {str(e)}")

async def list_gift_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all gift cards"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        gifts = db.get_all_gift_cards()
        
        if not gifts:
            await update.message.reply_text("No gift cards found!")
            return
        
        active = [g for g in gifts if g.get('is_active') and g.get('used_count', 0) < g.get('max_uses', 1)]
        used = [g for g in gifts if g.get('used_count', 0) >= g.get('max_uses', 1)]
        
        message = f"""GIFT CARDS

Total: {len(gifts)}
Active: {len(active)}
Used: {len(used)}

Active Cards:

"""
        
        for idx, gift in enumerate(active[:10], 1):
            message += f"{idx}. {gift['code']} - {gift['plan'].upper()} ({gift.get('api_expiry_days', 'N/A')}d)\n"
        
        if len(active) > 10:
            message += f"\n... and {len(active) - 10} more\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in list_gift_cards: {e}")
        await update.message.reply_text(f"Error loading gift cards: {str(e)}")

async def delete_gift_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a gift card - /giftdel CODE"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "Usage: /giftdel CODE\n\nExample:\n/giftdel GIFT-ABC-123"
            )
            return
        
        code = context.args[0]
        result = db.delete_gift_card(code)
        
        if result:
            await update.message.reply_text(f"Gift card {code} deleted!")
        else:
            await update.message.reply_text(f"Gift card {code} not found!")
    except Exception as e:
        logger.error(f"Error in delete_gift_card: {e}")
        await update.message.reply_text(f"Error deleting gift card: {str(e)}")

async def redeem_gift_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User redeems gift card - /redeem CODE"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "Usage: /redeem CODE\n\nExample:\n/redeem GIFT-ABC-123"
            )
            return
        
        code = context.args[0]
        result = db.redeem_gift_card(code, user_id, username)
        
        if result['success']:
            api_key = result['api_key']
            plan = result['plan']
            days = result.get('expiry_days', 'Unlimited')
            
            if system_monitor:
                try:
                    await system_monitor.notify_gift_redeemed(username=username, user_id=user_id, plan=plan, code=code)
                except Exception as e:
                    logger.error(f"Failed to notify gift redeemed: {e}")
            
            message = f"""Gift Card Redeemed!

Your API key is activated!

Plan: {plan.upper()}
API Key:
{api_key}

Valid for: {days} days

Start using now!
            """
            await update.message.reply_text(message)
            
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"Gift card redeemed!\n\nUser: @{username}\nCode: {code}\nPlan: {plan.upper()}"
                )
            except:
                pass
        else:
            await update.message.reply_text(f"Error: {result['error']}")
    except Exception as e:
        logger.error(f"Error in redeem_gift_card: {e}")
        await update.message.reply_text(f"Error redeeming gift card: {str(e)}")

# API Management
async def list_all_apis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all API keys"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        all_keys = db.get_all_api_keys()
        
        if not all_keys:
            await update.message.reply_text("No API keys found!")
            return
        
        active = [k for k in all_keys if k.get('is_active')]
        inactive = [k for k in all_keys if not k.get('is_active')]
        
        message = f"""ALL API KEYS

Total: {len(all_keys)}
Active: {len(active)}
Inactive: {len(inactive)}

Active Keys (Latest 10):

"""
        
        for idx, key in enumerate(active[:10], 1):
            plan_emoji = {"free": "F", "basic": "B", "pro": "P"}.get(key.get('plan'), "?")
            expiry = "No expiry"
            if key.get('expiry_date'):
                try:
                    exp = datetime.fromisoformat(key['expiry_date'])
                    days = (exp - datetime.now()).days
                    expiry = f"{days}d left" if days > 0 else "Expired"
                except:
                    pass
            message += f"{idx}. {plan_emoji} {key['api_key'][:20]}... (@{key.get('username')}) - {expiry}\n"
        
        if len(active) > 10:
            message += f"\n... and {len(active) - 10} more\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in list_all_apis: {e}")
        await update.message.reply_text(f"Error loading API keys: {str(e)}")

async def create_api_key_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create API key - /apicreate USER_ID PLAN DAYS"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "Usage: /apicreate USER_ID PLAN DAYS\n\nExample:\n/apicreate 123456 basic 30\n/apicreate 789012 pro 365"
            )
            return
        
        try:
            user_id = int(context.args[0])
            plan = context.args[1].lower()
            days = int(context.args[2])
        except:
            await update.message.reply_text("Invalid parameters!")
            return
        
        if plan not in ['free', 'basic', 'pro']:
            await update.message.reply_text("Invalid plan! Use: free, basic, or pro")
            return
        
        try:
            user = await context.bot.get_chat(user_id)
            username = user.username or user.first_name
        except:
            username = f"user_{user_id}"
        
        api_key = db.create_api_key(
            telegram_id=user_id,
            username=username,
            plan=plan,
            expiry_days=days,
            created_by_admin=True
        )
        
        if api_key:
            if system_monitor:
                try:
                    await system_monitor.notify_api_created(username=username, user_id=user_id, plan=plan, days=days, admin_id=ADMIN_ID)
                except Exception as e:
                    logger.error(f"Failed to notify API created: {e}")
            
            message = f"""API Key Created!

User ID: {user_id}
Username: @{username}
Plan: {plan.upper()}
Validity: {days} days

API Key:
{api_key}

Key activated!
            """
            await update.message.reply_text(message)
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"""Admin Gift!

You've been granted API access!

Plan: {plan.upper()}
API Key:
{api_key}

Valid for: {days} days

Start using now!
                    """
                )
            except:
                pass
        else:
            await update.message.reply_text("Failed to create API key!")
    except Exception as e:
        logger.error(f"Error in create_api_key_admin: {e}")
        await update.message.reply_text(f"Error creating API key: {str(e)}")

async def delete_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete API key - /apidel API_KEY"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "Usage: /apidel API_KEY\n\nExample:\n/apidel sk-abc123..."
            )
            return
        
        api_key = context.args[0]
        result = db.delete_api_key(api_key)
        
        if result:
            if system_monitor:
                try:
                    await system_monitor.notify_api_deleted(api_key=api_key, admin_id=ADMIN_ID)
                except Exception as e:
                    logger.error(f"Failed to notify API deleted: {e}")
            
            await update.message.reply_text(f"API key deleted!\n\n{api_key}")
        else:
            await update.message.reply_text(f"API key not found!\n\n{api_key}")
    except Exception as e:
        logger.error(f"Error in delete_api_key: {e}")
        await update.message.reply_text(f"Error deleting API key: {str(e)}")

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get detailed statistics - admin only"""
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Admin only!")
            return
        
        stats = db.get_stats()
        
        if system_monitor:
            try:
                await system_monitor.notify_stats(stats)
            except Exception as e:
                logger.error(f"Failed to send stats: {e}")
        
        message = f"""DETAILED STATISTICS

Users: {stats.get('total_users', 0)}
API Keys: {stats.get('active_keys', 0)}/{stats.get('total_keys', 0)}
Gift Cards: {stats.get('active_gifts', 0)}/{stats.get('total_gifts', 0)}
Total Requests: {stats.get('total_requests', 0)}
Gift Redemptions: {stats.get('total_redemptions', 0)}

Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
        """
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        await update.message.reply_text(f"Error loading statistics: {str(e)}")

async def on_startup(application: Application):
    """Called when bot starts"""
    try:
        if system_monitor:
            try:
                await system_monitor.notify_bot_start(ADMIN_ID, DEFAULT_FREE_EXPIRY_DAYS, UPI_ID)
            except Exception as e:
                logger.error(f"Failed to send startup notification: {e}")
        logger.info("✅ Bot startup completed successfully")
    except Exception as e:
        logger.error(f"Error in on_startup: {e}")

def main():
    try:
        health_thread = Thread(target=run_health_server, daemon=True)
        health_thread.start()
    except Exception as e:
        logger.error(f"Failed to start health thread: {e}")
    
    logger.info("🚀 Starting Bot...")
    logger.info(f"🎁 Free Trial: {DEFAULT_FREE_EXPIRY_DAYS} days")
    logger.info(f"💸 Payment: UPI ({UPI_ID})")
    logger.info(f"👤 Admin: {ADMIN_ID}")
    logger.info(f"📢 System Monitor Channel: {SYSTEM_CHANNEL_ID}")
    
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myapi", my_api_key))
    application.add_handler(CommandHandler("redeem", redeem_gift_card))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("verify", verify_payment))
    application.add_handler(CommandHandler("pending", pending_payments))
    application.add_handler(CommandHandler("giftgen", generate_gift_cards))
    application.add_handler(CommandHandler("giftlist", list_gift_cards))
    application.add_handler(CommandHandler("giftdel", delete_gift_card))
    application.add_handler(CommandHandler("apilist", list_all_apis))
    application.add_handler(CommandHandler("apicreate", create_api_key_admin))
    application.add_handler(CommandHandler("apidel", delete_api_key))
    application.add_handler(CommandHandler("stats", get_stats))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(help_support, pattern='^help_support$'))
    application.add_handler(CallbackQueryHandler(payment_done_handler, pattern='^paid_'))
    application.add_handler(CallbackQueryHandler(verify_from_button, pattern='^verify_'))
    application.add_handler(CallbackQueryHandler(admin_pending_button, pattern='^admin_pending$'))
    
    # Startup notification
    application.post_init = on_startup
    
    logger.info("✅ Bot initialized successfully!")
    logger.info("👑 Admin panel: /admin")
    logger.info("📊 Statistics: /stats")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == '__main__':
    main()

import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from database import Database
from config import Config

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

# Admin Telegram ID
ADMIN_ID = 5451167865

# Default free plan expiry (in days) - Admin can change this
DEFAULT_FREE_EXPIRY_DAYS = 7  # 7 days default

# Conversation states for admin
SET_EXPIRY, SET_EXPIRY_DAYS = range(2)

# API Plans with Premium Features
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
    """Check if user is admin"""
    return user_id == ADMIN_ID

def format_expiry(expiry_date_str):
    """Format expiry date for display"""
    if not expiry_date_str:
        return "No expiry (Permanent)"
    
    try:
        expiry = datetime.fromisoformat(expiry_date_str)
        now = datetime.now()
        
        if now > expiry:
            return "⚠️ Expired"
        
        days_left = (expiry - now).days
        hours_left = (expiry - now).seconds // 3600
        
        if days_left > 0:
            return f"✅ {days_left} days left (expires {expiry.strftime('%Y-%m-%d')})"
        else:
            return f"⚠️ {hours_left} hours left"
    except:
        return "Invalid date"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with menu"""
    user = update.effective_user
    
    # Admin check
    if is_admin(user.id):
        welcome_text = f"""
🤖 *Welcome Admin {user.first_name}!* 👑

You have full admin access to the API Seller Bot.

*✨ Premium Features:*
🌍 Multi-language support (8+ languages)
💬 Tone control (professional, casual, creative, etc.)
📚 Conversation history & context
🔍 Text analysis & summarization
⚡ Streaming responses
📊 Advanced analytics

*Admin Commands:*
/admin - Admin Panel
/stats - System Statistics
/users - View All Users
/setexpiry - Set Free Plan Expiry Days
        """
        
        keyboard = [
            [InlineKeyboardButton("👑 Admin Panel", callback_data='admin_panel')],
            [InlineKeyboardButton("📊 My API Keys", callback_data='my_api')],
            [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
            [InlineKeyboardButton("✨ View Features", callback_data='features')]
        ]
    else:
        welcome_text = f"""
🤖 *Welcome to Advanced API Seller Bot!* 🤖

Hello {user.first_name}! 

I help you get your own Advanced AI Chatbot API key instantly.

*✨ Premium Features:*
🌍 Multi-language support (8+ languages)
💬 Tone control (professional, casual, creative, etc.)
📚 Conversation history & context
🔍 Text analysis & summarization
⚡ Streaming responses
📊 Advanced analytics

*Commands:*
/buy - Purchase API access
/myapi - Get your API keys
/usage - Check API usage
/features - View all features
/help - Get help
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Buy API Access", callback_data='buy_api')],
            [InlineKeyboardButton("📊 My API Keys", callback_data='my_api')],
            [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
            [InlineKeyboardButton("✨ View Features", callback_data='features')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id
    
    if not is_admin(user_id):
        if query:
            await query.answer("⛔ Admin access only!", show_alert=True)
        else:
            await update.message.reply_text("⛔ This command is for admins only.")
        return
    
    # Get stats
    stats = db.get_stats()
    all_keys = db.get_all_api_keys()
    
    # Count by plan
    free_count = len([k for k in all_keys if k.get('plan') == 'free'])
    basic_count = len([k for k in all_keys if k.get('plan') == 'basic'])
    pro_count = len([k for k in all_keys if k.get('plan') == 'pro'])
    
    # Count expired
    expired_count = 0
    for key in all_keys:
        if key.get('expiry_date'):
            try:
                expiry = datetime.fromisoformat(key['expiry_date'])
                if datetime.now() > expiry:
                    expired_count += 1
            except:
                pass
    
    admin_text = f"""
👑 *Admin Panel*

📊 *System Statistics:*
• Total Users: {stats.get('total_users', 0)}
• Total API Keys: {stats.get('total_keys', 0)}
• Active Keys: {stats.get('active_keys', 0)}
• Expired Keys: {expired_count}
• Total Requests: {stats.get('total_requests', 0)}

📋 *Plan Distribution:*
• Free: {free_count} keys
• Basic: {basic_count} keys
• Pro: {pro_count} keys

⚙️ *Settings:*
• Free Plan Expiry: {DEFAULT_FREE_EXPIRY_DAYS} days

*Available Actions:*
Use buttons below to manage the system.
    """
    
    keyboard = [
        [InlineKeyboardButton("👥 View All Keys", callback_data='admin_keys')],
        [InlineKeyboardButton("📊 Detailed Stats", callback_data='admin_stats')],
        [InlineKeyboardButton("⏰ Manage Expiry", callback_data='admin_expiry')],
        [InlineKeyboardButton("🔄 Clean Expired", callback_data='admin_clean')],
        [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_all_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all API keys with details"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Admin access only!", show_alert=True)
        return
    
    all_keys = db.get_all_api_keys()
    
    if not all_keys:
        message = "No API keys found."
    else:
        message = "🔑 *All API Keys:*\n\n"
        for idx, key in enumerate(all_keys[:15], 1):  # Show first 15
            status = "✅" if key.get('is_active') else "❌"
            plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(key.get('plan'), "❓")
            
            expiry_info = format_expiry(key.get('expiry_date'))
            
            message += f"{idx}. {status} {plan_emoji} @{key.get('username', 'N/A')}\n"
            message += f"   Plan: {key.get('plan', 'N/A').upper()} | Requests: {key.get('requests_used', 0)}\n"
            message += f"   Expiry: {expiry_info}\n"
            message += f"   Key: `{key.get('api_key', '')[:20]}...`\n\n"
        
        if len(all_keys) > 15:
            message += f"\n_Showing 15 of {len(all_keys)} keys_"
    
    keyboard = [[InlineKeyboardButton("« Back to Admin", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_clean_expired(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clean expired keys"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Admin access only!", show_alert=True)
        return
    
    count = db.deactivate_expired_keys()
    
    message = f"""
🔄 *Expired Keys Cleaned*

✅ Deactivated {count} expired API keys.

All expired keys have been automatically deactivated.
    """
    
    keyboard = [[InlineKeyboardButton("« Back to Admin", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed stats to admin"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Admin access only!", show_alert=True)
        return
    
    stats = db.get_stats()
    all_keys = db.get_all_api_keys()
    
    free_keys = [k for k in all_keys if k.get('plan') == 'free']
    basic_keys = [k for k in all_keys if k.get('plan') == 'basic']
    pro_keys = [k for k in all_keys if k.get('plan') == 'pro']
    
    free_requests = sum(k.get('requests_used', 0) for k in free_keys)
    basic_requests = sum(k.get('requests_used', 0) for k in basic_keys)
    pro_requests = sum(k.get('requests_used', 0) for k in pro_keys)
    
    total_keys = stats.get('total_keys', 0)
    
    stats_text = f"""
📊 *Detailed System Statistics*

*Users & Keys:*
• Total Users: {stats.get('total_users', 0)}
• Total API Keys: {total_keys}
• Active Keys: {stats.get('active_keys', 0)}

*Plan Distribution:*
• Free Plan: {len(free_keys)} keys ({len(free_keys)*100//total_keys if total_keys > 0 else 0}%)
• Basic Plan: {len(basic_keys)} keys ({len(basic_keys)*100//total_keys if total_keys > 0 else 0}%)
• Pro Plan: {len(pro_keys)} keys ({len(pro_keys)*100//total_keys if total_keys > 0 else 0}%)

*Request Statistics:*
• Total Requests: {stats.get('total_requests', 0)}
• Free Plan Requests: {free_requests}
• Basic Plan Requests: {basic_requests}
• Pro Plan Requests: {pro_requests}

*API Status:*
• API Gateway: Connected ✅
• Database: Connected ✅
• Bot Status: Running ✅
    """
    
    keyboard = [[InlineKeyboardButton("« Back to Admin", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')

async def buy_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show API purchase options"""
    query = update.callback_query
    await query.answer()
    
    plans_text = f"""
💳 *Choose Your Plan*

*1️⃣ Free Plan* - ₹0
   • 100 requests/hour
   • English language
   • Basic support
   • Valid for {DEFAULT_FREE_EXPIRY_DAYS} days
   • Perfect for testing

*2️⃣ Basic Plan* - ₹99/month
   • Unlimited requests
   • 8+ language support
   • Tone control
   • Conversation history
   • Text analysis
   • Email support
   • Monthly renewal (no expiry)

*3️⃣ Pro Plan* - ₹299/month
   • Everything in Basic
   • Content summarization
   • Streaming responses
   • Priority support
   • Advanced analytics
   • Dedicated support
   • Monthly renewal (no expiry)

Select a plan below:
    """
    
    keyboard = [
        [InlineKeyboardButton(f"🆓 Free Plan (₹0) - {DEFAULT_FREE_EXPIRY_DAYS} days", callback_data='select_free')],
        [InlineKeyboardButton("💎 Basic Plan - ₹99/mo", callback_data='select_basic')],
        [InlineKeyboardButton("⭐ Pro Plan - ₹299/mo", callback_data='select_pro')],
        [InlineKeyboardButton("« Back", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(plans_text, reply_markup=reply_markup, parse_mode='Markdown')

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection"""
    query = update.callback_query
    await query.answer()
    
    plan = query.data.replace('select_', '')
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    # Check if user already has this specific plan active
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
    
    # For free plan, generate key immediately with expiry
    if plan == 'free':
        api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
        
        if not api_key:
            await query.edit_message_text("❌ Error generating API key. Please try again.")
            return
        
        success_message = f"""
✅ *Free API Key Generated Successfully!*

🔑 Your API Key:
`{api_key}`

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
    "language": "english",
    "tone": "professional"
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
    
    else:
        # For paid plans, show payment instructions
        plan_info = PLANS[plan]
        payment_message = f"""
💳 *{plan_info['name']} Payment*

Price: *₹{plan_info['price']}/month*

*Features:*
"""
        for feature in plan_info['features']:
            payment_message += f"✅ {feature}\n"
        
        payment_message += f"""

*Payment Instructions:*

1️⃣ Send payment to:
   UPI: `your-upi-id@upi`
   Phone: +91-XXXXXXXXXX
   Reference: USER_{user_id}

2️⃣ Send screenshot with reference number

3️⃣ Your API key will be activated within 5 minutes

*Or contact admin:*
@YourAdminUsername

💡 _Demo mode: Integrate real payment gateway for production_
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Payment Done", callback_data=f'payment_done_{plan}')],
            [InlineKeyboardButton("« Back", callback_data='buy_api')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(payment_message, reply_markup=reply_markup, parse_mode='Markdown')

async def my_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's API keys with usage examples"""
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
        message = """
❌ *No Active API Keys Found*

You don't have any active API keys yet.
Click the button below to get one!
        """
        keyboard = [[InlineKeyboardButton("🛍️ Buy API Access", callback_data='buy_api')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        # Show API Base URL only to admin
        if is_admin(user_id):
            api_url_text = f"""*API Base URL:*
`{Config.API_BASE_URL}`

"""
        else:
            api_url_text = "_Contact admin for API endpoint details_\n\n"
        
        message = f"""
🔑 *Your API Keys*

{api_url_text}You have {len(keys)} active API key(s):

"""
        
        for idx, key in enumerate(keys, 1):
            plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(key.get('plan'), "❓")
            expiry_info = format_expiry(key.get('expiry_date'))
            
            message += f"{idx}. {plan_emoji} *{key.get('plan', 'N/A').upper()} Plan*\n"
            message += f"   Key: `{key.get('api_key')}`\n"
            message += f"   Status: {'✅ Active' if key.get('is_active') else '❌ Inactive'}\n"
            message += f"   Requests: {key.get('requests_used', 0)}\n"
            message += f"   Expiry: {expiry_info}\n\n"
        
        message += """
*📚 Usage Example:*
```bash
curl -X POST YOUR_API_ENDPOINT/chat \\
  -H "X-API-Key: your-key-here" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Hello!"}'
```

📖 Use /features for complete documentation
        """
        
        keyboard = [
            [InlineKeyboardButton("✨ View Features", callback_data='features')],
            [InlineKeyboardButton("🛍️ Get More Keys", callback_data='buy_api')],
            [InlineKeyboardButton("« Back", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show advanced features documentation"""
    query = update.callback_query
    await query.answer()
    
    features_text = """
✨ *Advanced Features*

*1️⃣ Multi-Language Support (8+ Languages)*
🌍 English, हिंदी, Español, Français, Deutsch, 中文, العربية, 日本語

```json
{"language": "hindi"}
```

*2️⃣ Tone Control*
⚪ Neutral - Balanced responses
💼 Professional - Business appropriate
😊 Casual - Friendly tone
🎨 Creative - Imaginative responses
📚 Educational - Detailed explanations

```json
{"tone": "professional"}
```

*3️⃣ Conversation History & Context*
Maintain multi-turn conversations with full context.

```json
{
  "include_context": true,
  "user_id": "your_user_id"
}
```

*4️⃣ Text Analysis*
Analyze sentiment, extract keywords, understand content.

*5️⃣ Content Summarization*
Create concise, bullet-point, or detailed summaries.

*6️⃣ Streaming Responses*
Real-time response generation for better UX.

*7️⃣ Rate Limiting*
✅ Free: 100 requests/hour
✅ Basic: Unlimited
✅ Pro: Unlimited + Priority

*Upgrade to unlock all features!*
    """
    
    keyboard = [
        [InlineKeyboardButton("💎 Upgrade to Basic", callback_data='select_basic')],
        [InlineKeyboardButton("⭐ Upgrade to Pro", callback_data='select_pro')],
        [InlineKeyboardButton("« Back", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(features_text, reply_markup=reply_markup, parse_mode='Markdown')

async def usage_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show API usage statistics"""
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
        message = "❌ No active API keys found. Use /buy to get one!"
        keyboard = [[InlineKeyboardButton("🛍️ Buy API", callback_data='buy_api')]]
    else:
        total_requests = sum(k.get('requests_used', 0) for k in keys)
        
        message = f"""
📈 *API Usage Statistics*

*Total API Keys:* {len(keys)}
*Total Requests:* {total_requests}

*Keys Breakdown:*
"""
        for key in keys:
            plan_emoji = {"free": "🆓", "basic": "💎", "pro": "⭐"}.get(key.get('plan'), "❓")
            expiry_info = format_expiry(key.get('expiry_date'))
            
            message += f"\n{plan_emoji} *{key.get('plan', 'N/A').upper()}*\n"
            message += f"  Status: {'✅ Active' if key.get('is_active') else '❌ Inactive'}\n"
            message += f"  Requests: {key.get('requests_used', 0)}\n"
            message += f"  Expiry: {expiry_info}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔑 My API Keys", callback_data='my_api')],
            [InlineKeyboardButton("✨ Get More Keys", callback_data='buy_api')],
            [InlineKeyboardButton("« Back", callback_data='back_to_menu')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check if admin
    if is_admin(user.id):
        menu_text = f"""👑 *Admin Menu*

Welcome back, {user.first_name}!

What would you like to do?
        """
        keyboard = [
            [InlineKeyboardButton("👑 Admin Panel", callback_data='admin_panel')],
            [InlineKeyboardButton("🔑 My API Keys", callback_data='my_api')],
            [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
            [InlineKeyboardButton("✨ View Features", callback_data='features')]
        ]
    else:
        menu_text = f"""
🤖 *Main Menu*

Welcome back, {user.first_name}!

What would you like to do?
        """
        keyboard = [
            [InlineKeyboardButton("🛍️ Buy API Access", callback_data='buy_api')],
            [InlineKeyboardButton("🔑 My API Keys", callback_data='my_api')],
            [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
            [InlineKeyboardButton("✨ View Features", callback_data='features')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        help_text = f"""
👑 *Admin Help & Documentation*

*Admin Commands:*
/admin - Open Admin Panel
/stats - View System Statistics

*User Commands:*
/start - Start the bot
/buy - Purchase API access
/myapi - View your API keys
/usage - Check usage statistics
/features - View all features
/help - Show this help

*Admin Features:*
• View all API keys
• System statistics
• Manage expiry dates
• Clean expired keys
• Free plan: {DEFAULT_FREE_EXPIRY_DAYS} days validity

*Multiple Keys:*
Users can have Free + Premium keys simultaneously.
Cannot have multiple keys of same plan type.
        """
    else:
        help_text = f"""
📚 *Help & Documentation*

*Commands:*
/start - Start the bot
/buy - Purchase API access
/myapi - View your API keys
/usage - Check usage statistics
/features - View all features
/help - Show this help

*Plans:*
• Free: ₹0 (valid for {DEFAULT_FREE_EXPIRY_DAYS} days)
• Basic: ₹99/month
• Pro: ₹299/month

*Multiple Keys:*
You can have both Free and Premium keys!

*Need Help?*
Contact admin for support.
        """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Start the bot"""
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("myapi", my_api_key))
    application.add_handler(CommandHandler("usage", usage_stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("buy", lambda u, c: buy_api(u, c)))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_all_keys, pattern='^admin_keys$'))
    application.add_handler(CallbackQueryHandler(admin_clean_expired, pattern='^admin_clean$'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(usage_stats, pattern='^usage$'))
    application.add_handler(CallbackQueryHandler(show_features, pattern='^features$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    
    # Start bot
    logger.info(f"Bot started with admin features... Free plan validity: {DEFAULT_FREE_EXPIRY_DAYS} days")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
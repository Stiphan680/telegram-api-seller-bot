import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import Database
from config import Config

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

# Admin Telegram ID
ADMIN_ID = 5451167865

# API Plans with Premium Features
PLANS = {
    'free': {
        'name': 'Free Plan',
        'price': 0,
        'description': 'Free forever',
        'features': [
            '100 requests/hour',
            'English language only',
            'Basic tone (neutral)',
            'No conversation history',
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
            'Email support'
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
            'Dedicated support'
        ]
    }
}

def is_admin(user_id):
    """Check if user is admin"""
    return user_id == ADMIN_ID

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
/broadcast - Send Broadcast Message
/deactivate - Deactivate API Key
/activate - Activate API Key
        """
        
        keyboard = [
            [InlineKeyboardButton("👑 Admin Panel", callback_data='admin_panel')],
            [InlineKeyboardButton("📊 My API Key", callback_data='my_api')],
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
/myapi - Get your API key
/usage - Check API usage
/features - View all features
/help - Get help
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Buy API Access", callback_data='buy_api')],
            [InlineKeyboardButton("📊 My API Key", callback_data='my_api')],
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
    all_users = db.get_all_users()
    total_users = len(all_users)
    active_users = len([u for u in all_users if u.get('is_active', True)])
    total_requests = sum(u.get('requests_used', 0) for u in all_users)
    
    # Count by plan
    free_count = len([u for u in all_users if u.get('plan') == 'free'])
    basic_count = len([u for u in all_users if u.get('plan') == 'basic'])
    pro_count = len([u for u in all_users if u.get('plan') == 'pro'])
    
    admin_text = f"""
👑 *Admin Panel*

📊 *System Statistics:*
• Total Users: {total_users}
• Active Keys: {active_users}
• Total Requests: {total_requests}

📋 *Plan Distribution:*
• Free: {free_count} users
• Basic: {basic_count} users
• Pro: {pro_count} users

*Available Actions:*
Use commands below to manage the system.
    """
    
    keyboard = [
        [InlineKeyboardButton("👥 View Users", callback_data='admin_users')],
        [InlineKeyboardButton("📊 Detailed Stats", callback_data='admin_stats')],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_broadcast')],
        [InlineKeyboardButton("🔑 Manage Keys", callback_data='admin_keys')],
        [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all users to admin"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Admin access only!", show_alert=True)
        return
    
    all_users = db.get_all_users()
    
    if not all_users:
        message = "No users found."
    else:
        message = "👥 *All Users:*\n\n"
        for idx, user in enumerate(all_users[:20], 1):  # Show first 20
            status = "✅" if user.get('is_active') else "❌"
            message += f"{idx}. {status} @{user.get('username', 'N/A')} - {user.get('plan', 'free').upper()}\n"
            message += f"   ID: `{user.get('telegram_id')}` | Requests: {user.get('requests_used', 0)}\n\n"
        
        if len(all_users) > 20:
            message += f"\n_Showing 20 of {len(all_users)} users_"
    
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
    
    all_users = db.get_all_users()
    
    # Calculate stats
    total_users = len(all_users)
    active_users = len([u for u in all_users if u.get('is_active', True)])
    inactive_users = total_users - active_users
    total_requests = sum(u.get('requests_used', 0) for u in all_users)
    avg_requests = total_requests // total_users if total_users > 0 else 0
    
    free_users = [u for u in all_users if u.get('plan') == 'free']
    basic_users = [u for u in all_users if u.get('plan') == 'basic']
    pro_users = [u for u in all_users if u.get('plan') == 'pro']
    
    free_requests = sum(u.get('requests_used', 0) for u in free_users)
    basic_requests = sum(u.get('requests_used', 0) for u in basic_users)
    pro_requests = sum(u.get('requests_used', 0) for u in pro_users)
    
    stats_text = f"""
📊 *Detailed System Statistics*

*Users Overview:*
• Total Users: {total_users}
• Active Keys: {active_users}
• Inactive Keys: {inactive_users}

*Plan Distribution:*
• Free Plan: {len(free_users)} users ({len(free_users)*100//total_users if total_users > 0 else 0}%)
• Basic Plan: {len(basic_users)} users ({len(basic_users)*100//total_users if total_users > 0 else 0}%)
• Pro Plan: {len(pro_users)} users ({len(pro_users)*100//total_users if total_users > 0 else 0}%)

*Request Statistics:*
• Total Requests: {total_requests}
• Average per User: {avg_requests}
• Free Plan Requests: {free_requests}
• Basic Plan Requests: {basic_requests}
• Pro Plan Requests: {pro_requests}

*API Status:*
• API Gateway: {Config.API_BASE_URL}
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
    
    plans_text = """
💳 *Choose Your Plan*

*1️⃣ Free Plan* - ₹0
   • 100 requests/hour
   • English language
   • Basic support
   • Perfect for testing

*2️⃣ Basic Plan* - ₹99/month
   • Unlimited requests
   • 8+ language support
   • Tone control
   • Conversation history
   • Text analysis
   • Email support

*3️⃣ Pro Plan* - ₹299/month
   • Everything in Basic
   • Content summarization
   • Streaming responses
   • Priority support
   • Advanced analytics
   • Dedicated support

Select a plan below:
    """
    
    keyboard = [
        [InlineKeyboardButton("🆓 Free Plan (₹0)", callback_data='select_free')],
        [InlineKeyboardButton("💎 Basic Plan - ₹99", callback_data='select_basic')],
        [InlineKeyboardButton("⭐ Pro Plan - ₹299", callback_data='select_pro')],
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
    
    # Check if user already has an API key
    existing_user = db.get_user_by_telegram_id(user_id)
    
    if existing_user:
        message = f"""
⚠️ *You already have an API key!*

Your current plan: *{existing_user['plan'].upper()}*
Created: {existing_user['created_at'][:10]}

Use /myapi to view your API key.
Use /usage to check your usage stats.

To upgrade your plan, contact support.
        """
        keyboard = [[InlineKeyboardButton("📊 My API Key", callback_data='my_api')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    # For free plan, generate key immediately
    if plan == 'free':
        api_key = db.create_api_key(user_id, username, plan)
        
        success_message = f"""
✅ *API Key Generated Successfully!*

🔑 Your API Key:
`{api_key}`

*🌟 Example - Simple Request (Python):*
```python
import requests

url = "YOUR_API_ENDPOINT/chat"
headers = {{
    "X-API-Key": "{api_key}",
    "Content-Type": "application/json"
}}

data = {{
    "question": "What is artificial intelligence?",
    "language": "english",
    "tone": "professional"
}}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

*🌟 Supported Languages:*
English, हिंदी, Español, Français, Deutsch, 中文, العربية, 日本語

*🌟 Tone Controls:*
neutral, professional, casual, creative, educational

*🌟 Free Plan Features:*
• 100 requests/hour
• English language only
• Basic tone (neutral)
• Community support

*📚 Premium Features Available:*
Upgrade to access multi-language, tone control, conversation history, text analysis & more!

Contact admin for API endpoint details.
        """
        
        keyboard = [
            [InlineKeyboardButton("✨ View Premium Features", callback_data='features')],
            [InlineKeyboardButton("📈 Check Usage", callback_data='usage')],
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
    """Show user's API key with usage examples"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        edit_message = True
    else:
        user_id = update.effective_user.id
        edit_message = False
    
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        message = """
❌ *No API Key Found*

You don't have an API key yet.
Click the button below to get one!
        """
        keyboard = [[InlineKeyboardButton("🛍️ Buy API Access", callback_data='buy_api')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        api_key = user['api_key']
        
        # Show API Base URL only to admin
        if is_admin(user_id):
            api_url_text = f"""*API Base URL:*
`{Config.API_BASE_URL}`

"""
        else:
            api_url_text = "_Contact admin for API endpoint details_\n\n"
        
        message = f"""
🔑 *Your API Key*

API Key:
`{api_key}`

{api_url_text}*Plan:* {user['plan'].upper()}
*Status:* {'✅ Active' if user['is_active'] else '❌ Inactive'}
*Requests Used:* {user['requests_used']}
*Created:* {user['created_at'][:10]}

*🌟 Example - Text Analysis:*
```bash
curl -X POST YOUR_API_ENDPOINT/analyze \\
  -H "X-API-Key: {api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "text": "Your text here",
    "type": "sentiment"
  }}'
```

*🌟 Available Languages:*
🇬🇧 English, 🇮🇳 Hindi, 🇪🇸 Spanish, 🇫🇷 French, 🇩🇪 German, 🇨🇳 Chinese, 🇸🇦 Arabic, 🇯🇵 Japanese

*🌟 Tone Controls:*
⚪ Neutral, 💼 Professional, 😊 Casual, 🎨 Creative, 📚 Educational

*🌟 Advanced Features:*
📊 Text Analysis
📝 Summarization
💬 Conversation History
⚡ Streaming Responses

📖 Use /features for complete documentation
        """
        keyboard = [
            [InlineKeyboardButton("✨ View Features", callback_data='features')],
            [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
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

```bash
POST /analyze
{"text": "...", "type": "sentiment"}
```

*5️⃣ Content Summarization*
Create concise, bullet-point, or detailed summaries.

```bash
POST /summarize
{"content": "...", "type": "bullet-points"}
```

*6️⃣ Streaming Responses*
Real-time response generation for better UX.

```bash
POST /chat/stream
{"question": "..."}
```

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
    
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        message = "❌ No API key found. Use /buy to get one!"
        keyboard = [[InlineKeyboardButton("🛍️ Buy API", callback_data='buy_api')]]
    else:
        plan_info = PLANS.get(user['plan'], {})
        message = f"""
📈 *API Usage Statistics*

*Plan:* {user['plan'].upper()}
*Status:* {'✅ Active' if user['is_active'] else '❌ Inactive'}
*Total Requests:* {user['requests_used']}
*Created:* {user['created_at'][:10]}

*API Key:* `{user['api_key'][:15]}...`

*Plan Benefits:*
"""
        for feature in plan_info.get('features', []):
            message += f"✅ {feature}\n"
        
        message += f"""

*Status:* {'🟢 All features available!' if user['plan'] != 'free' else '🟡 Upgrade for more features'}
        """
        keyboard = [
            [InlineKeyboardButton("🔑 My API Key", callback_data='my_api')],
            [InlineKeyboardButton("✨ Upgrade Plan", callback_data='buy_api')],
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
            [InlineKeyboardButton("🔑 My API Key", callback_data='my_api')],
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
            [InlineKeyboardButton("🔑 My API Key", callback_data='my_api')],
            [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
            [InlineKeyboardButton("✨ View Features", callback_data='features')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        help_text = """
👑 *Admin Help & Documentation*

*Admin Commands:*
/admin - Open Admin Panel
/stats - View System Statistics
/users - List All Users

*User Commands:*
/start - Start the bot
/buy - Purchase API access
/myapi - View your API key
/usage - Check usage statistics
/features - View all features
/help - Show this help

*API Endpoints:*
• POST /chat - Chat with AI
• POST /chat/stream - Streaming responses
• GET /chat/history - View history
• POST /analyze - Text analysis
• POST /summarize - Content summary
• GET /health - Status check

*Admin Features:*
👥 View all users
📊 System statistics
📢 Broadcast messages
🔑 Manage API keys

*Need Help?*
You are the admin!
        """
    else:
        help_text = """
📚 *Help & Documentation*

*Commands:*
/start - Start the bot
/buy - Purchase API access
/myapi - View your API key
/usage - Check usage statistics
/features - View all features
/help - Show this help

*API Endpoints:*
• POST /chat - Chat with AI (multi-lang, tone control, context)
• POST /chat/stream - Streaming responses
• GET /chat/history - View conversation history
• POST /analyze - Text sentiment & analysis
• POST /summarize - Content summarization
• POST /chat/clear - Clear conversation history
• GET /health - Status check

*Premium Features:*
🌍 8+ Languages
💬 Tone Control
📚 Conversation History
🔍 Text Analysis
📝 Summarization
⚡ Streaming

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
    application.add_handler(CallbackQueryHandler(admin_users, pattern='^admin_users$'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(usage_stats, pattern='^usage$'))
    application.add_handler(CallbackQueryHandler(show_features, pattern='^features$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    
    # Start bot
    logger.info("Bot started with admin features...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
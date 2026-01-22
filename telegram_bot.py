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

# API Plans
PLANS = {
    'free': {'name': 'Free Plan', 'price': 0, 'description': 'Free forever'},
    'basic': {'name': 'Basic Plan', 'price': 99, 'description': '₹99/month - Unlimited requests'},
    'pro': {'name': 'Pro Plan', 'price': 299, 'description': '₹299/month - Priority support'}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with menu"""
    user = update.effective_user
    
    welcome_text = f"""
🤖 *Welcome to API Seller Bot!* 🤖

Hello {user.first_name}! 

I help you get your own AI Chatbot API key instantly.

*Features:*
✅ Instant API key generation
✅ Usage tracking
✅ Multiple plans available
✅ 24/7 API access

*Commands:*
/buy - Purchase API access
/myapi - Get your API key
/usage - Check API usage
/help - Get help
/plans - View all plans

Click the button below to get started!
    """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Buy API Access", callback_data='buy_api')],
        [InlineKeyboardButton("📊 My API Key", callback_data='my_api')],
        [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
        [InlineKeyboardButton("💡 View Plans", callback_data='plans')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def buy_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show API purchase options"""
    query = update.callback_query
    await query.answer()
    
    plans_text = """
💳 *Choose Your Plan*

*1. Free Plan* - ₹0
   • Instant API key
   • Basic support
   • Perfect for testing

*2. Basic Plan* - ₹99/month
   • Unlimited requests
   • Email support
   • No rate limits

*3. Pro Plan* - ₹299/month
   • Everything in Basic
   • Priority support
   • Custom features
   • Dedicated support

Select a plan below:
    """
    
    keyboard = [
        [InlineKeyboardButton("🆓 Free Plan", callback_data='select_free')],
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

Your API Key:
`{api_key}`

*API Base URL:*
`{Config.API_BASE_URL}`

*Usage Example:*
```bash
curl -X POST {Config.API_BASE_URL}/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: {api_key}" \\
  -d '{{
    "question": "What is AI?"
  }}'
```

*Python Example:*
```python
import requests

url = "{Config.API_BASE_URL}/chat"
headers = {{
    "X-API-Key": "{api_key}",
    "Content-Type": "application/json"
}}
data = {{"question": "What is AI?"}}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

⚠️ *Keep your API key secure!*
Don't share it publicly.
        """
        
        keyboard = [
            [InlineKeyboardButton("📈 Check Usage", callback_data='usage')],
            [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    else:
        # For paid plans, show payment instructions
        payment_message = f"""
💳 *{PLANS[plan]['name']} Payment*

Price: *₹{PLANS[plan]['price']}*

*Payment Instructions:*

1. Send payment to:
   UPI: `yourpayment@upi`
   (Click to copy)

2. After payment, send screenshot here

3. Your API key will be activated within 5 minutes

*Or contact admin:*
@YourAdminUsername

_Currently showing demo. Integrate real payment gateway for production._
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Payment Done", callback_data=f'payment_done_{plan}')],
            [InlineKeyboardButton("« Back", callback_data='buy_api')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(payment_message, reply_markup=reply_markup, parse_mode='Markdown')

async def my_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's API key"""
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
        keyboard = [[InlineKeyboardButton("🛒 Buy API Access", callback_data='buy_api')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        api_key = user['api_key']
        message = f"""
🔑 *Your API Key*

API Key:
`{api_key}`

*API Base URL:*
`{Config.API_BASE_URL}`

*Plan:* {user['plan'].upper()}
*Status:* {'✅ Active' if user['is_active'] else '❌ Inactive'}
*Requests Used:* {user['requests_used']}

*Quick Test:*
```bash
curl -X POST {Config.API_BASE_URL}/chat \\
  -H "X-API-Key: {api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{"question": "Hello"
}}'
```

Use /usage for detailed stats.
        """
        keyboard = [
            [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
            [InlineKeyboardButton("« Back", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

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
        keyboard = [[InlineKeyboardButton("🛒 Buy API", callback_data='buy_api')]]
    else:
        message = f"""
📊 *API Usage Statistics*

*Plan:* {user['plan'].upper()}
*Status:* {'✅ Active' if user['is_active'] else '❌ Inactive'}
*Total Requests:* {user['requests_used']}
*Created:* {user['created_at'][:10]}

*API Key:* `{user['api_key'][:15]}...`

{'✨ Unlimited requests available!' if user['plan'] != 'free' else '🆓 Free tier active'}
        """
        keyboard = [
            [InlineKeyboardButton("🔑 My API Key", callback_data='my_api')],
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
    
    menu_text = f"""
🤖 *Main Menu*

Welcome back, {user.first_name}!

What would you like to do?
    """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Buy API Access", callback_data='buy_api')],
        [InlineKeyboardButton("📊 My API Key", callback_data='my_api')],
        [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
        [InlineKeyboardButton("💡 View Plans", callback_data='plans')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = """
📚 *Help & Documentation*

*Available Commands:*
/start - Start the bot
/buy - Purchase API access
/myapi - View your API key
/usage - Check usage statistics
/plans - View all available plans
/help - Show this help message

*API Documentation:*

*Endpoint:* `POST {Config.API_BASE_URL}/chat`

*Headers:*
- `Content-Type: application/json`
- `X-API-Key: YOUR_API_KEY`

*Body:*
```json
{{
  "question": "Your question here"
}}
```

*Response:*
```json
{{
  "success": true,
  "response": "AI response here",
  "usage": {{
    "requests_used": 42,
    "plan": "free"
  }}
}}
```

Need help? Contact @YourAdminUsername
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Start the bot"""
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myapi", my_api_key))
    application.add_handler(CommandHandler("usage", usage_stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("buy", lambda u, c: buy_api(u, c)))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^buy_api$'))
    application.add_handler(CallbackQueryHandler(select_plan, pattern='^select_'))
    application.add_handler(CallbackQueryHandler(my_api_key, pattern='^my_api$'))
    application.add_handler(CallbackQueryHandler(usage_stats, pattern='^usage$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(buy_api, pattern='^plans$'))
    
    # Start bot
    logger.info("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
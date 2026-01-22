import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from database import Database
from config import Config

# Import AI Router for Perplexity integration
try:
    from ai_router import get_ai_router
    AI_ROUTER_AVAILABLE = True
except ImportError:
    AI_ROUTER_AVAILABLE = False
    print("⚠️ AI Router not available, using default API backend")

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

# Admin Telegram ID
ADMIN_ID = 5451167865

# Default free plan expiry (in days)
DEFAULT_FREE_EXPIRY_DAYS = 7

# API Plans
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

async def get_ai_backend_info():
    """Get current AI backend information"""
    if ai_router:
        status = ai_router.get_backend_status()
        if 'perplexity' in status.get('available_backends', []):
            return "🔍 Powered by Perplexity AI (Online Search + Citations)"
        else:
            return "🤖 Powered by Gemini + Groq (Free AI)"
    return "🤖 Advanced AI Backend"

async def test_api_with_backend(api_key: str, plan: str) -> dict:
    """Test API key with AI backend"""
    if not ai_router:
        return {'success': False, 'backend': 'none'}
    
    try:
        # Test query based on plan
        test_queries = {
            'free': 'What is AI?',
            'basic': 'Explain artificial intelligence in Hindi',
            'pro': 'Search for latest AI developments'
        }
        
        result = await ai_router.get_response(
            question=test_queries.get(plan, 'Hello'),
            search_online=(plan == 'pro'),  # Pro plan gets online search
            include_context=False
        )
        
        return {
            'success': result.get('success', False),
            'backend': result.get('backend_used', 'unknown'),
            'response_preview': result.get('response', '')[:100] if result.get('success') else None
        }
    except Exception as e:
        logger.error(f"Test API error: {e}")
        return {'success': False, 'backend': 'error', 'error': str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with menu"""
    user = update.effective_user
    
    # Get AI backend info
    backend_info = await get_ai_backend_info()
    
    # Admin check
    if is_admin(user.id):
        welcome_text = f"""
🤖 *Welcome Admin {user.first_name}!* 👑

{backend_info}

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
/backend - Check AI Backend Status
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

{backend_info}

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

async def check_backend_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Check AI backend status"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⛔ This command is for admins only.")
        return
    
    if not ai_router:
        await update.message.reply_text("❌ AI Router not available")
        return
    
    status = ai_router.get_backend_status()
    
    status_text = f"""
🤖 *AI Backend Status*

*Available Backends:*
{', '.join(status.get('available_backends', []))}

*Priority Order:*
{' → '.join(status.get('priority_order', []))}

*Default Backend:*
{status.get('default', 'none')}

*Status:*
• Perplexity: {'✅' if status.get('perplexity_enabled') else '❌'}
• Advanced AI (Gemini/Groq): {'✅' if status.get('advanced_ai_enabled') else '❌'}

*Perplexity Features:*
• 🌐 Online search (real-time data)
• 📚 Citations and sources
• 🎯 Up-to-date information (2024+)
    """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection with Perplexity backend"""
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
    
    # For free plan, generate key immediately with AI backend test
    if plan == 'free':
        # Show processing message
        await query.edit_message_text("⏳ Generating your API key with AI backend...\n\nPlease wait...")
        
        api_key = db.create_api_key(user_id, username, plan, expiry_days=DEFAULT_FREE_EXPIRY_DAYS)
        
        if not api_key:
            await query.edit_message_text("❌ Error generating API key. Please try again.")
            return
        
        # Test API with backend
        test_result = await test_api_with_backend(api_key, plan)
        
        backend_info = ""
        if test_result.get('success'):
            backend_used = test_result.get('backend', 'unknown')
            if backend_used == 'perplexity':
                backend_info = "\n🔍 *Backend:* Perplexity AI (Online Search)\n✅ API tested successfully!\n"
            elif backend_used == 'advanced_ai':
                backend_info = "\n🤖 *Backend:* Advanced AI (Gemini + Groq)\n✅ API tested successfully!\n"
            else:
                backend_info = f"\n✅ Backend: {backend_used}\n"
        
        success_message = f"""
✅ *Free API Key Generated Successfully!*

🔑 Your API Key:
`{api_key}`
{backend_info}
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
        
        # Add backend info for premium plans
        if ai_router and 'perplexity' in ai_router.get_backend_status().get('available_backends', []):
            payment_message += "\n🔍 *Includes:* Perplexity AI with online search\n"
        
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

# ... (rest of the bot code remains same: admin_panel, buy_api, my_api_key, etc.)
# Copy all other functions from original telegram_bot.py

def main():
    """Start the bot"""
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("backend", check_backend_status))
    # ... add all other handlers
    
    # Start bot
    backend_status = ai_router.get_backend_status() if ai_router else {}
    logger.info(f"Bot started with AI Router - Backends: {backend_status.get('available_backends', [])}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

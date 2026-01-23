#!/bin/bash
# Script to restore working telegram_bot.py and add /testapi feature

echo "📦 Restoring working telegram_bot.py from commit 34a0e039..."

# Get the working version
git show 34a0e039e58011196259f5046d977093bc56156c:telegram_bot.py > telegram_bot.py.backup

echo "✅ Backup created"

# Now add the modifications using sed
echo "🔧 Adding api_key_tester import..."

# Add import after manual_payment section (after line 33)
sed -i '/print("⚠️ Manual Payment not available")/a\
\
try:\
    from api_key_tester import get_api_key_tester\
    api_tester = get_api_key_tester()\
    TESTER_AVAILABLE = True\
except ImportError:\
    TESTER_AVAILABLE = False\
    api_tester = None\
    print("⚠️ API Key Tester not available")' telegram_bot.py.backup

echo "🔧 Adding test_api_key_command function..."

# Add function before async def start
sed -i '/^async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):/i\
# ============= API KEY TESTER COMMAND =============\
\
async def test_api_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    """Test an API key: /testapi <api_key>"""\
    if not TESTER_AVAILABLE or not api_tester:\
        await update.message.reply_text("❌ API key testing is not available.")\
        return\
    \
    if not context.args:\
        help_msg = """┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\
┃  🔍 *TEST YOUR API KEY*  ┃\
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\
\
*Usage:*\
`/testapi <your_api_key>`\
\
*Example:*\
`/testapi sk-ant-api03-abc...`\
\
━━━━━━━━━━━━━━━━━━━━━━━━━━━━\
\
*What it checks:*\
✅ Database validation\
✅ API gateway connection\
✅ Chat endpoint functionality\
✅ Expiry status\
✅ Request count\
\
━━━━━━━━━━━━━━━━━━━━━━━━━━━━\
\
💡 Paste your API key after the command!"""\
        await update.message.reply_text(help_msg, parse_mode='Markdown')\
        return\
    \
    api_key = context.args[0].strip()\
    test_msg = await update.message.reply_text("🔍 *Testing your API key...*\\n\\nPlease wait, this may take 10-30 seconds.", parse_mode='Markdown')\
    \
    try:\
        result_text = await api_tester.quick_test(api_key)\
        await test_msg.edit_text(f"""┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\
┃  🔍 *API KEY TEST RESULTS*  ┃\
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\
\
{result_text}\
\
━━━━━━━━━━━━━━━━━━━━━━━━━━━━\
\
💡 Use `/myapi` to view all your keys""", parse_mode='Markdown')\
    except Exception as e:\
        logger.error(f"API test error: {e}")\
        await test_msg.edit_text(f"❌ *Test Failed*\\n\\nError: {str(e)}\\n\\nPlease try again or contact support.", parse_mode='Markdown')\
\
' telegram_bot.py.backup

echo "🔧 Adding /testapi to command handlers..."

# Add command handler after help command
sed -i '/application.add_handler(CommandHandler("help", help_command))/a\
    application.add_handler(CommandHandler("testapi", test_api_key_command))' telegram_bot.py.backup

echo "🔧 Updating admin help text..."
# Add to admin commands list
sed -i '/• `\/backend` - AI status/a\
• `/testapi <key>` - Test any API key' telegram_bot.py.backup

echo "🔧 Updating user help text..."
# Add to user commands list
sed -i '/• `\/help` - Get help & support/a\
• `/testapi <key>` - Test your API key' telegram_bot.py.backup

# Copy to final location
cp telegram_bot.py.backup telegram_bot.py

echo "✅ Done! telegram_bot.py has been updated with /testapi feature."
echo ""
echo "Changes made:"
echo "1. ✅ Added api_key_tester import"
echo "2. ✅ Added test_api_key_command() function"
echo "3. ✅ Registered /testapi command handler"
echo "4. ✅ Updated help text for users and admin"
echo ""
echo "🚀 You can now commit and push the changes!"

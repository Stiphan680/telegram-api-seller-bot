#!/usr/bin/env python3
"""Script to add /testapi command to telegram_bot.py"""

import re

def add_testapi_feature():
    # Read the current file
    with open('telegram_bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already added
    if 'test_api_key_command' in content:
        print("✅ /testapi command already exists in telegram_bot.py")
        return
    
    # 1. Add api_key_tester import after manual_payment import
    import_pattern = r"(try:\s+from manual_payment import get_manual_payment_handler.*?print\(\"⚠️ Manual Payment not available\"\))"
    import_addition = """\n\ntry:
    from api_key_tester import get_api_key_tester
    api_tester = get_api_key_tester()
    TESTER_AVAILABLE = True
except ImportError:
    TESTER_AVAILABLE = False
    api_tester = None
    print("⚠️ API Key Tester not available")"""
    
    content = re.sub(import_pattern, r"\1" + import_addition, content, flags=re.DOTALL)
    
    # 2. Update health check HTML to show tester status
    health_pattern = r"(<p><strong>Payments:</strong> \{.*?\}</p>)"
    health_addition = r"\1\n            <p><strong>API Tester:</strong> {'✅ Enabled' if api_tester else '❌ Disabled'}</p>"
    content = re.sub(health_pattern, health_addition, content)
    
    # 3. Add test_api_key_command function after get_ai_backend_info function
    function_location = content.find('async def start(update: Update')
    
    testapi_function = '''\n# ============= API KEY TESTER COMMAND =============

async def test_api_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test an API key - /testapi <api_key>"""
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
    test_msg = await update.message.reply_text("🔍 *Testing your API key...*\\n\\nPlease wait, this may take 10-30 seconds.", parse_mode='Markdown')
    
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
        await test_msg.edit_text(f"❌ *Test Failed*\\n\\nError: {str(e)}\\n\\nPlease try again or contact support.", parse_mode='Markdown')

'''
    
    content = content[:function_location] + testapi_function + '\n' + content[function_location:]
    
    # 4. Add command handler in main() function
    handler_pattern = r"(application\.add_handler\(CommandHandler\(\"help\", help_command\)\))"
    handler_addition = r"\1\n    application.add_handler(CommandHandler(\"testapi\", test_api_key_command))"
    content = re.sub(handler_pattern, handler_addition, content)
    
    # 5. Update /start welcome message to include /testapi
    # For users
    user_commands_pattern = r"(• `/help` - Get help & support)"
    user_commands_addition = r"\1\n• `/testapi <key>` - Test your API key"
    content = re.sub(user_commands_pattern, user_commands_addition, content)
    
    # For admin
    admin_system_pattern = r"(• `/backend` - AI status)"
    admin_system_addition = r"\1\n• `/testapi <key>` - Test any API key"
    content = re.sub(admin_system_pattern, admin_system_addition, content)
    
    # Write back
    with open('telegram_bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully added /testapi feature to telegram_bot.py!")
    print("\nChanges made:")
    print("1. Added api_key_tester import")
    print("2. Added test_api_key_command() function")
    print("3. Added /testapi command handler in main()")
    print("4. Updated welcome messages to show /testapi")
    print("5. Updated health check to show tester status")

if __name__ == '__main__':
    add_testapi_feature()

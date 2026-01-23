# Quick Fix: Add /testapi Command to telegram_bot.py

## Problem
The `/testapi` command is not working in the bot.

## Solution
Make these 3 simple changes to `telegram_bot.py`:

---

### Change 1: Add Import (Line 33)

**After this line:**
```python
    print("⚠️ Manual Payment not available")
```

**Add this:**
```python

# Import API Key Tester
try:
    from api_key_tester import get_api_key_tester
    api_tester = get_api_key_tester()
    TESTER_AVAILABLE = True
except ImportError:
    TESTER_AVAILABLE = False
    api_tester = None
    print("⚠️ API Key Tester not available")
```

---

### Change 2: Add Function (Before `async def start`)

**Before this line:**
```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
```

**Add this complete function:**
```python
# ============= API KEY TESTER COMMAND =============

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

```

---

### Change 3: Add Command Handler (in `main()` function)

**After this line:**
```python
    application.add_handler(CommandHandler("help", help_command))
```

**Add this:**
```python
    application.add_handler(CommandHandler("testapi", test_api_key_command))
```

---

### Change 4: Update Health Check HTML (Optional)

**Find this line:**
```python
            <p><strong>Payments:</strong> {'✅ Manual' if payment_handler else '❌ Disabled'}</p>
```

**After it, add:**
```python
            <p><strong>API Tester:</strong> {'✅ Enabled' if api_tester else '❌ Disabled'}</p>
```

---

### Change 5: Update Help Text (Optional)

**For Admin - Find:**
```python
• `/backend` - AI status
```

**After it, add:**
```python
• `/testapi <key>` - Test any API key
```

**For Users - Find:**
```python
• `/help` - Get help & support
```

**After it, add:**
```python
• `/testapi <key>` - Test your API key
```

---

## Quick Apply

Run this on your Render server:

```bash
cd /opt/render/project/src
# Backup first
cp telegram_bot.py telegram_bot.py.backup

# Edit the file manually using nano
nano telegram_bot.py

# Or restore from last good commit and apply changes
git checkout 34a0e039e58011196259f5046d977093bc56156c -- telegram_bot.py
# Then make the changes above

# Restart the bot
pkill -f telegram_bot.py
python telegram_bot.py
```

---

## Verify

After applying changes:
1. ✅ Bot should restart without errors
2. ✅ `/testapi` command should be available
3. ✅ Health check should show "API Tester: ✅ Enabled"
4. ✅ Command should work: `/testapi sk-ant-api03-...`

---

**Status:** Ready to apply ✅

#!/bin/bash

# Restoration script for clean telegram bot
# Removes all API Tester code and restores working version

echo "🔄 Restoring clean telegram bot version..."

# Go to project directory
cd /opt/render/project/src || cd .

echo "📥 Downloading complete working telegram_bot.py from commit 34a0e039..."

# Download the complete working version
curl -L -o telegram_bot.py https://raw.githubusercontent.com/Stiphan680/telegram-api-seller-bot/34a0e039e58011196259f5046d977093bc56156c/telegram_bot.py

if [ $? -eq 0 ]; then
    echo "✅ telegram_bot.py restored successfully!"
    
    # Verify file size (should be around 25KB)
    FILE_SIZE=$(wc -c < telegram_bot.py)
    echo "📊 File size: $FILE_SIZE bytes"
    
    if [ $FILE_SIZE -gt 20000 ]; then
        echo "✅ File size looks correct!"
        echo "🎉 Clean bot version restored successfully!"
        echo ""
        echo "Bot features:"
        echo "  ✅ Gift Card System"
        echo "  ✅ Manual Payments"
        echo "  ✅ AI Router"
        echo "  ✅ Notifications"
        echo "  ❌ API Tester (Removed)"
        echo ""
        echo "🔄 Bot will auto-restart in a moment..."
    else
        echo "⚠️ Warning: File size seems too small!"
        echo "Please check the file manually."
    fi
else
    echo "❌ Failed to download file!"
    echo "Please run manually: git reset --hard 34a0e039e58011196259f5046d977093bc56156c"
fi

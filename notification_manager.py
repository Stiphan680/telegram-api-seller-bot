"""
Notification Manager
Sends updates to channel about bot events
"""

import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
import asyncio

logger = logging.getLogger(__name__)

class NotificationManager:
    """
    Manages notifications to channel
    """
    
    def __init__(self, bot_token: str, channel_id: str):
        """
        Initialize notification manager
        
        Args:
            bot_token: Telegram bot token
            channel_id: Channel ID (e.g., -1003350605488)
        """
        self.bot = Bot(token=bot_token)
        self.channel_id = channel_id
        self.enabled = True
    
    async def send_notification(self, message: str, parse_mode: str = 'Markdown'):
        """
        Send notification to channel
        
        Args:
            message: Message text
            parse_mode: Markdown or HTML
        """
        if not self.enabled:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info(f"✅ Notification sent to channel {self.channel_id}")
            return True
        except TelegramError as e:
            logger.error(f"❌ Failed to send notification: {e}")
            return False
    
    async def notify_bot_started(self, backend_info: dict = None):
        """
        Notify when bot starts
        """
        backend_text = ""
        if backend_info:
            backends = backend_info.get('available_backends', [])
            backend_text = f"\n🤖 *Backends:* {', '.join(backends)}"
        
        message = f"""
🚀 *Bot Started Successfully!*

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{backend_text}
✅ Status: Running

_Bot is now live and ready to serve users!_
        """
        
        await self.send_notification(message)
    
    async def notify_new_api_key(self, username: str, user_id: int, plan: str, backend: str = None):
        """
        Notify when new API key is created
        """
        plan_emoji = {
            'free': '🆓',
            'basic': '💎',
            'pro': '⭐'
        }.get(plan, '❓')
        
        backend_text = f"\n🤖 Backend: {backend}" if backend else ""
        
        message = f"""
🔑 *New API Key Created!*

{plan_emoji} Plan: *{plan.upper()}*
👤 User: @{username} (ID: {user_id}){backend_text}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_Total active keys increased!_
        """
        
        await self.send_notification(message)
    
    async def notify_feature_added(self, feature_name: str, description: str = None):
        """
        Notify when new feature is added
        """
        desc_text = f"\n\n📝 {description}" if description else ""
        
        message = f"""
✨ *New Feature Added!*

🎯 Feature: *{feature_name}*{desc_text}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_Bot functionality enhanced!_
        """
        
        await self.send_notification(message)
    
    async def notify_deployment(self, version: str = None, changes: str = None):
        """
        Notify when bot is deployed
        """
        version_text = f" v{version}" if version else ""
        changes_text = f"\n\n📋 Changes:\n{changes}" if changes else ""
        
        message = f"""
🚀 *Bot Deployed{version_text}!*

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ Status: Live{changes_text}

_Deployment successful!_
        """
        
        await self.send_notification(message)
    
    async def notify_error(self, error_msg: str, context: str = None):
        """
        Notify about critical errors
        """
        context_text = f"\n\n🔍 Context: {context}" if context else ""
        
        message = f"""
⚠️ *Bot Error Alert!*

❌ Error: {error_msg}{context_text}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_Immediate attention required!_
        """
        
        await self.send_notification(message)
    
    async def notify_stats(self, total_users: int, total_keys: int, total_requests: int):
        """
        Send daily/periodic stats
        """
        message = f"""
📊 *Bot Statistics Update*

👥 Total Users: {total_users}
🔑 Total API Keys: {total_keys}
📈 Total Requests: {total_requests}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_Bot performing well!_
        """
        
        await self.send_notification(message)
    
    async def notify_upgrade(self, username: str, old_plan: str, new_plan: str):
        """
        Notify when user upgrades plan
        """
        message = f"""
⬆️ *Plan Upgraded!*

👤 User: @{username}
📦 From: {old_plan.upper()} → {new_plan.upper()}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_User upgraded to premium!_
        """
        
        await self.send_notification(message)
    
    async def notify_backend_change(self, old_backend: str, new_backend: str, reason: str = None):
        """
        Notify when AI backend changes
        """
        reason_text = f"\n\n📝 Reason: {reason}" if reason else ""
        
        message = f"""
🔄 *Backend Changed!*

🤖 From: {old_backend}
🤖 To: {new_backend}{reason_text}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_Backend switched automatically!_
        """
        
        await self.send_notification(message)
    
    async def notify_maintenance(self, message_text: str):
        """
        Send maintenance notification
        """
        message = f"""
🔧 *Maintenance Alert*

{message_text}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await self.send_notification(message)
    
    def disable_notifications(self):
        """Disable notifications"""
        self.enabled = False
        logger.info("📵 Notifications disabled")
    
    def enable_notifications(self):
        """Enable notifications"""
        self.enabled = True
        logger.info("🔔 Notifications enabled")


# Singleton instance
_notification_manager = None

def get_notification_manager(bot_token: str = None, channel_id: str = None):
    """
    Get or create notification manager
    
    Args:
        bot_token: Bot token (required first time)
        channel_id: Channel ID (required first time)
    """
    global _notification_manager
    
    if _notification_manager is None:
        if not bot_token or not channel_id:
            raise ValueError("bot_token and channel_id required for first initialization")
        
        _notification_manager = NotificationManager(bot_token, channel_id)
    
    return _notification_manager


# Test function
async def test_notifications():
    """Test notification system"""
    import os
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    channel_id = "-1003350605488"  # Your channel ID
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return
    
    notifier = get_notification_manager(bot_token, channel_id)
    
    print("📤 Testing notifications...\n")
    
    # Test 1: Bot started
    print("1️⃣ Testing bot started notification...")
    await notifier.notify_bot_started({'available_backends': ['perplexity', 'advanced_ai']})
    await asyncio.sleep(2)
    
    # Test 2: New API key
    print("2️⃣ Testing new API key notification...")
    await notifier.notify_new_api_key('testuser', 123456, 'free', 'perplexity')
    await asyncio.sleep(2)
    
    # Test 3: Feature added
    print("3️⃣ Testing feature notification...")
    await notifier.notify_feature_added('Multi-language Support', 'Added support for 8+ languages')
    await asyncio.sleep(2)
    
    # Test 4: Stats
    print("4️⃣ Testing stats notification...")
    await notifier.notify_stats(100, 250, 5000)
    
    print("\n✅ All tests completed! Check your channel.")


if __name__ == '__main__':
    asyncio.run(test_notifications())

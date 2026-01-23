import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, bot_token, notification_channel_id):
        """Initialize system monitor with bot token and notification channel"""
        self.bot = Bot(token=bot_token)
        self.channel_id = notification_channel_id
        self.start_time = datetime.now()
        
    async def send_notification(self, message, parse_mode='Markdown'):
        """Send notification to channel"""
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            return True
        except TelegramError as e:
            logger.error(f"Failed to send notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")
            return False
    
    async def notify_bot_start(self, admin_id, free_trial_days, upi_id):
        """Notify when bot starts"""
        message = f"""
🚀 *BOT STARTED SUCCESSFULLY!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ *Start Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

📊 *Bot Configuration:*
• Admin ID: `{admin_id}`
• Free Trial: {free_trial_days} days
• Payment: UPI `{upi_id}`

✅ *Status:* All systems operational
✅ *Database:* Connected
✅ *Payment:* Active
✅ *Notifications:* Enabled

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 Bot is now running!
        """
        await self.send_notification(message)
    
    async def notify_bot_stop(self, reason="Manual stop"):
        """Notify when bot stops"""
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600
        
        message = f"""
⚠️ *BOT STOPPED*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ *Stop Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
🕒 *Uptime:* {hours:.2f} hours

💬 *Reason:* {reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Bot is now offline
        """
        await self.send_notification(message)
    
    async def notify_error(self, error_type, error_message, context=""):
        """Notify about errors"""
        message = f"""
❌ *ERROR DETECTED!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
⚠️ *Type:* {error_type}

*Error:*
```
{error_message[:500]}
```

*Context:* {context if context else 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Check logs for details
        """
        await self.send_notification(message)
    
    async def notify_deploy(self, version="latest", status="success"):
        """Notify about deployment"""
        emoji = "✅" if status == "success" else "❌"
        message = f"""
{emoji} *DEPLOYMENT {status.upper()}!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
💻 *Version:* {version}
📊 *Status:* {status.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{emoji} Deployment completed!
        """
        await self.send_notification(message)
    
    async def notify_stats(self, stats):
        """Send statistics update"""
        message = f"""
📊 *SYSTEM STATISTICS*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *Users:* {stats.get('total_users', 0)}
🔑 *API Keys:* {stats.get('active_keys', 0)}/{stats.get('total_keys', 0)}
🎁 *Gift Cards:* {stats.get('active_gifts', 0)}/{stats.get('total_gifts', 0)}
📊 *Requests:* {stats.get('total_requests', 0)}
🎁 *Redemptions:* {stats.get('total_redemptions', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ *Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
        """
        await self.send_notification(message)
    
    async def notify_new_user(self, username, user_id):
        """Notify about new user registration"""
        message = f"""
🎉 *NEW USER REGISTERED!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *Username:* @{username}
🎯 *User ID:* `{user_id}`
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ User successfully registered!
        """
        await self.send_notification(message)
    
    async def notify_payment_received(self, username, user_id, plan, amount, reference):
        """Notify about payment notification"""
        message = f"""
💰 *PAYMENT NOTIFICATION!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *User:* @{username} (`{user_id}`)
🏷️ *Plan:* {plan.upper()}
💵 *Amount:* ₹{amount}
🎯 *Reference:* `{reference}`
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Waiting for admin verification
        """
        await self.send_notification(message)
    
    async def notify_payment_verified(self, username, user_id, plan, amount, api_key):
        """Notify about payment verification"""
        message = f"""
✅ *PAYMENT VERIFIED!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *User:* @{username} (`{user_id}`)
🏷️ *Plan:* {plan.upper()}
💵 *Amount:* ₹{amount}
🔑 *API Key:* `{api_key[:20]}...`
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ API key activated and user notified!
        """
        await self.send_notification(message)
    
    async def notify_gift_generated(self, plan, days, count, admin_id):
        """Notify about gift card generation"""
        message = f"""
🎁 *GIFT CARDS GENERATED!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ *Plan:* {plan.upper()}
📅 *Validity:* {days} days
📊 *Count:* {count} cards
👤 *Generated By:* Admin (`{admin_id}`)
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Gift cards ready for distribution!
        """
        await self.send_notification(message)
    
    async def notify_gift_redeemed(self, username, user_id, plan, code):
        """Notify about gift card redemption"""
        message = f"""
🎁 *GIFT CARD REDEEMED!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *User:* @{username} (`{user_id}`)
🏷️ *Plan:* {plan.upper()}
🎫 *Code:* `{code}`
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ API key activated via gift card!
        """
        await self.send_notification(message)
    
    async def notify_api_created(self, username, user_id, plan, days, admin_id):
        """Notify about admin API creation"""
        message = f"""
🔑 *API KEY CREATED BY ADMIN!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *User:* @{username} (`{user_id}`)
🏷️ *Plan:* {plan.upper()}
📅 *Validity:* {days} days
👑 *Created By:* Admin (`{admin_id}`)
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ API key created and user notified!
        """
        await self.send_notification(message)
    
    async def notify_api_deleted(self, api_key, admin_id):
        """Notify about API deletion"""
        message = f"""
❌ *API KEY DELETED!*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔑 *API Key:* `{api_key[:20]}...`
👑 *Deleted By:* Admin (`{admin_id}`)
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ API key permanently deleted!
        """
        await self.send_notification(message)
    
    async def notify_daily_report(self, stats, new_users_today, new_keys_today):
        """Send daily report"""
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600
        
        message = f"""
📈 *DAILY REPORT*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 *Date:* {datetime.now().strftime('%Y-%m-%d')}
🕒 *Uptime:* {hours:.2f} hours

*📊 Today's Activity:*
• New Users: {new_users_today}
• New API Keys: {new_keys_today}

*📊 Overall Stats:*
• Total Users: {stats.get('total_users', 0)}
• Active Keys: {stats.get('active_keys', 0)}
• Total Requests: {stats.get('total_requests', 0)}
• Gift Cards: {stats.get('active_gifts', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ All systems operational!
        """
        await self.send_notification(message)

# Singleton instance
_monitor_instance = None

def get_system_monitor(bot_token, notification_channel_id):
    """Get or create system monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor(bot_token, notification_channel_id)
    return _monitor_instance

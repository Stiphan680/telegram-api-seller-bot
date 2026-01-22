"""Manual Payment Handler - Simple UPI/Bank Transfer System"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ManualPaymentHandler:
    """
    Simple manual payment system
    Users pay via UPI/Bank Transfer and send screenshot
    Admin verifies and activates API key
    """
    
    def __init__(self):
        # Your payment details - CHANGE THESE!
        self.upi_id = os.getenv('UPI_ID', 'yourname@paytm')
        self.phone = os.getenv('PAYMENT_PHONE', '+91-9876543210')
        self.bank_name = os.getenv('BANK_NAME', 'State Bank of India')
        self.account_holder = os.getenv('ACCOUNT_HOLDER', 'Your Name')
        self.admin_username = os.getenv('ADMIN_USERNAME', '@YourUsername')
        
        # Track pending payments
        self.pending_payments = {}
        
        logger.info("✅ Manual payment system initialized")
    
    def create_payment_request(self, 
                              user_id: int,
                              username: str,
                              plan: str,
                              amount: int) -> Dict:
        """
        Create payment request with instructions
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            plan: Plan name (basic/pro)
            amount: Amount in rupees
        
        Returns:
            Payment instructions
        """
        
        # Generate unique reference
        reference = f"USER_{user_id}_{plan.upper()}"
        timestamp = datetime.now()
        
        # Store pending payment
        self.pending_payments[reference] = {
            'user_id': user_id,
            'username': username,
            'plan': plan,
            'amount': amount,
            'reference': reference,
            'status': 'pending',
            'created_at': timestamp.isoformat()
        }
        
        return {
            'success': True,
            'reference': reference,
            'amount': amount,
            'instructions': self.get_payment_instructions(reference, plan, amount)
        }
    
    def get_payment_instructions(self, 
                                reference: str,
                                plan: str,
                                amount: int) -> str:
        """
        Generate formatted payment instructions
        """
        
        instructions = f"""
💳 *Manual Payment Instructions*

*Plan:* {plan.upper()}
*Amount:* ₹{amount}
*Reference:* `{reference}`

┌─────────────────────

*📱 Method 1: UPI Payment*

1️⃣ Open any UPI app:
   • PhonePe / GPay / Paytm
   
2️⃣ Pay to UPI ID:
   `{self.upi_id}`
   
3️⃣ Amount: ₹{amount}

4️⃣ Add note: `{reference}`

─────────────────────

*📞 Method 2: Phone Payment*

Send money to:
`{self.phone}`

via PhonePe/Paytm/GPay

─────────────────────

*🏦 Method 3: Bank Transfer*

Bank: {self.bank_name}
A/C Holder: {self.account_holder}
(Contact admin for A/C number)

└─────────────────────

*⚠️ IMPORTANT:*

✅ Always add reference: `{reference}`
✅ Take screenshot of payment
✅ Send screenshot to admin
✅ API key activated in 5-10 minutes

*💬 Contact Admin:*
{self.admin_username}

Send message:
"Payment done for {reference}"
+ Screenshot

✨ Thank you for your purchase!
        """
        
        return instructions
    
    def get_payment_qr_text(self, amount: int, reference: str) -> str:
        """
        Generate UPI QR text (can be converted to QR using online tools)
        """
        
        # UPI payment string format
        upi_string = f"upi://pay?pa={self.upi_id}&pn={self.account_holder}&am={amount}&tn={reference}"
        
        return upi_string
    
    def mark_payment_verified(self, reference: str) -> bool:
        """
        Admin marks payment as verified
        """
        
        if reference in self.pending_payments:
            self.pending_payments[reference]['status'] = 'verified'
            self.pending_payments[reference]['verified_at'] = datetime.now().isoformat()
            return True
        return False
    
    def get_pending_payment(self, reference: str) -> Optional[Dict]:
        """
        Get pending payment details
        """
        return self.pending_payments.get(reference)
    
    def get_all_pending_payments(self) -> list:
        """
        Get all pending payments (for admin)
        """
        return [
            payment for payment in self.pending_payments.values()
            if payment['status'] == 'pending'
        ]
    
    def get_payment_summary(self, user_id: int) -> str:
        """
        Get payment summary for user
        """
        
        user_payments = [
            p for p in self.pending_payments.values()
            if p['user_id'] == user_id
        ]
        
        if not user_payments:
            return "❌ No pending payments found."
        
        summary = "📊 *Your Payment Status*\n\n"
        
        for payment in user_payments:
            status_emoji = "⏳" if payment['status'] == 'pending' else "✅"
            summary += f"{status_emoji} {payment['plan'].upper()}\n"
            summary += f"   Amount: ₹{payment['amount']}\n"
            summary += f"   Reference: `{payment['reference']}`\n"
            summary += f"   Status: {payment['status'].title()}\n\n"
        
        return summary
    
    def get_admin_summary(self) -> str:
        """
        Get pending payments summary for admin
        """
        
        pending = self.get_all_pending_payments()
        
        if not pending:
            return "✅ No pending payments."
        
        summary = f"📊 *Pending Payments* ({len(pending)})\n\n"
        
        for idx, payment in enumerate(pending, 1):
            summary += f"{idx}. @{payment['username']} (ID: {payment['user_id']})\n"
            summary += f"   Plan: {payment['plan'].upper()}\n"
            summary += f"   Amount: ₹{payment['amount']}\n"
            summary += f"   Reference: `{payment['reference']}`\n"
            summary += f"   Created: {payment['created_at'][:10]}\n\n"
        
        return summary


# Singleton
_payment_handler = None

def get_manual_payment_handler():
    """Get manual payment handler instance"""
    global _payment_handler
    
    if _payment_handler is None:
        _payment_handler = ManualPaymentHandler()
    
    return _payment_handler


if __name__ == '__main__':
    # Test
    handler = ManualPaymentHandler()
    
    result = handler.create_payment_request(
        user_id=123456,
        username='testuser',
        plan='basic',
        amount=99
    )
    
    print(result['instructions'])

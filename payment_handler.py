"""
Payment Handler - Razorpay Integration
Supports UPI, Cards, Netbanking, Wallets
"""

import os
import razorpay
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PaymentHandler:
    """
    Handle payments via Razorpay
    """
    
    def __init__(self):
        """Initialize Razorpay client"""
        self.key_id = os.getenv('RAZORPAY_KEY_ID', '')
        self.key_secret = os.getenv('RAZORPAY_KEY_SECRET', '')
        
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            self.enabled = True
            logger.info("✅ Razorpay initialized")
        else:
            self.client = None
            self.enabled = False
            logger.warning("⚠️ Razorpay not configured - using manual payment")
        
        # Pending payments tracker
        self.pending_payments = {}
    
    def is_available(self) -> bool:
        """Check if Razorpay is configured"""
        return self.enabled
    
    def create_payment_link(self, 
                           user_id: int,
                           plan: str,
                           amount: int,
                           description: str = None) -> Dict[str, Any]:
        """
        Create Razorpay payment link
        
        Args:
            user_id: Telegram user ID
            plan: Plan name (basic/pro)
            amount: Amount in rupees
            description: Payment description
        
        Returns:
            Dict with payment link and details
        """
        
        if not self.enabled:
            return {
                'success': False,
                'error': 'Payment gateway not configured',
                'manual_payment': True
            }
        
        try:
            # Create payment link
            payment_link = self.client.payment_link.create({
                "amount": amount * 100,  # Convert to paise
                "currency": "INR",
                "description": description or f"{plan.upper()} Plan Subscription",
                "customer": {
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@telegram.bot"
                },
                "notify": {
                    "sms": False,
                    "email": False
                },
                "reminder_enable": False,
                "notes": {
                    "user_id": str(user_id),
                    "plan": plan,
                    "platform": "telegram_bot"
                },
                "callback_url": "https://your-domain.com/payment/callback",
                "callback_method": "get"
            })
            
            # Store pending payment
            payment_id = payment_link['id']
            self.pending_payments[payment_id] = {
                'user_id': user_id,
                'plan': plan,
                'amount': amount,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'payment_id': payment_id,
                'payment_link': payment_link['short_url'],
                'amount': amount,
                'currency': 'INR',
                'expires_at': payment_link.get('expire_by')
            }
            
        except Exception as e:
            logger.error(f"Payment link creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'manual_payment': True
            }
    
    def verify_payment(self, payment_id: str, signature: str = None) -> Dict[str, Any]:
        """
        Verify payment status
        
        Args:
            payment_id: Razorpay payment ID
            signature: Payment signature (for webhook)
        
        Returns:
            Payment verification result
        """
        
        if not self.enabled:
            return {'success': False, 'error': 'Payment gateway not configured'}
        
        try:
            # Fetch payment details
            payment = self.client.payment.fetch(payment_id)
            
            result = {
                'success': True,
                'payment_id': payment_id,
                'status': payment['status'],
                'amount': payment['amount'] / 100,  # Convert from paise
                'method': payment.get('method'),
                'captured': payment.get('captured', False)
            }
            
            # Get user details from notes
            if payment['status'] == 'captured':
                notes = payment.get('notes', {})
                result['user_id'] = int(notes.get('user_id', 0))
                result['plan'] = notes.get('plan', '')
            
            return result
            
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_status(self, payment_id: str) -> str:
        """
        Get simple payment status
        
        Returns: 'paid', 'pending', 'failed', 'unknown'
        """
        
        if not self.enabled:
            return 'unknown'
        
        try:
            payment = self.client.payment.fetch(payment_id)
            status = payment['status']
            
            if status == 'captured':
                return 'paid'
            elif status in ['created', 'authorized']:
                return 'pending'
            else:
                return 'failed'
        except:
            return 'unknown'
    
    def create_qr_payment(self, 
                         user_id: int,
                         plan: str,
                         amount: int) -> Dict[str, Any]:
        """
        Create UPI QR code for payment
        
        Returns:
            QR code image URL and UPI string
        """
        
        if not self.enabled:
            return {
                'success': False,
                'manual_payment': True
            }
        
        try:
            # Create QR code
            qr_code = self.client.qr_code.create({
                "type": "upi_qr",
                "name": f"User_{user_id}_{plan}",
                "usage": "single_use",
                "fixed_amount": True,
                "payment_amount": amount * 100,
                "description": f"{plan.upper()} Plan",
                "notes": {
                    "user_id": str(user_id),
                    "plan": plan
                }
            })
            
            return {
                'success': True,
                'qr_code_id': qr_code['id'],
                'qr_code_url': qr_code['image_url'],
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"QR code creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_manual_payment_info(self, user_id: int, plan: str, amount: int) -> str:
        """
        Get manual payment instructions
        
        Returns:
            Formatted payment instructions
        """
        
        # Replace with your actual payment details
        upi_id = "your-upi-id@paytm"  # Change this
        phone = "+91-XXXXXXXXXX"  # Change this
        
        payment_text = f"""
💳 *Manual Payment Instructions*

*Amount:* ₹{amount}
*Plan:* {plan.upper()}
*Reference:* USER_{user_id}

*Payment Methods:*

1️⃣ *UPI Payment:*
   UPI ID: `{upi_id}`
   
2️⃣ *PhonePe/Paytm/GPay:*
   Phone: `{phone}`
   
3️⃣ *Bank Transfer:*
   Contact admin for bank details

*Important:*
• Add reference: USER_{user_id}
• Send payment screenshot to admin
• API key activated within 5 minutes

*Contact Admin:*
@YourAdminUsername
        """
        
        return payment_text
    
    def refund_payment(self, payment_id: str, amount: int = None) -> Dict[str, Any]:
        """
        Refund a payment
        
        Args:
            payment_id: Payment ID to refund
            amount: Partial refund amount (None for full refund)
        
        Returns:
            Refund result
        """
        
        if not self.enabled:
            return {'success': False, 'error': 'Payment gateway not configured'}
        
        try:
            refund_data = {'payment_id': payment_id}
            if amount:
                refund_data['amount'] = amount * 100  # Convert to paise
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return {
                'success': True,
                'refund_id': refund['id'],
                'status': refund['status'],
                'amount': refund['amount'] / 100
            }
            
        except Exception as e:
            logger.error(f"Refund failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
_payment_handler = None

def get_payment_handler():
    """Get or create payment handler instance"""
    global _payment_handler
    
    if _payment_handler is None:
        _payment_handler = PaymentHandler()
    
    return _payment_handler


# Test function
if __name__ == '__main__':
    handler = get_payment_handler()
    
    if handler.is_available():
        print("✅ Razorpay configured")
        
        # Test payment link creation
        result = handler.create_payment_link(
            user_id=123456,
            plan='basic',
            amount=99,
            description='Basic Plan - Monthly'
        )
        
        print(f"\nPayment Link: {result}")
    else:
        print("⚠️ Razorpay not configured")
        print("\nManual payment info:")
        print(handler.get_manual_payment_info(123456, 'basic', 99))

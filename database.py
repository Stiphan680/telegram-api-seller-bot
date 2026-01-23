import os
import secrets
import random
import string
from datetime import datetime, timedelta
from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DB_NAME]
        self.users = self.db['users']
        self.api_keys = self.db['api_keys']
        self.gift_cards = self.db['gift_cards']
        self.referrals = self.db['referrals']  # New: Referrals collection
        
        # Create indexes
        self.users.create_index('telegram_id', unique=True)
        self.api_keys.create_index('api_key', unique=True)
        self.api_keys.create_index('telegram_id')
        self.gift_cards.create_index('code', unique=True)
        self.referrals.create_index('referrer_id')
        self.referrals.create_index('referred_id', unique=True)
    
    def generate_api_key(self):
        """Generate a unique API key"""
        return f"sk-{secrets.token_urlsafe(32)}"
    
    def generate_gift_code(self):
        """Generate a unique gift card code"""
        parts = []
        for _ in range(3):
            part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            parts.append(part)
        return f"GIFT-{'-'.join(parts)}"
    
    def register_user(self, telegram_id, username):
        """Register user in database"""
        try:
            existing = self.users.find_one({'telegram_id': telegram_id})
            if not existing:
                user_data = {
                    'telegram_id': telegram_id,
                    'username': username,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                self.users.insert_one(user_data)
            else:
                # Update username if changed
                self.users.update_one(
                    {'telegram_id': telegram_id},
                    {'$set': {'username': username, 'updated_at': datetime.now().isoformat()}}
                )
            return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False
    
    def create_user(self, telegram_id, username):
        """Alias for register_user"""
        return self.register_user(telegram_id, username)
    
    # ========== REFERRAL SYSTEM ==========
    
    def add_referral(self, referrer_id, referred_id, referred_username):
        """Add a referral"""
        try:
            # Check if already referred
            existing = self.referrals.find_one({'referred_id': referred_id})
            if existing:
                return False
            
            referral_data = {
                'referrer_id': referrer_id,
                'referred_id': referred_id,
                'referred_username': referred_username,
                'is_used': False,  # Whether used to claim free trial
                'created_at': datetime.now().isoformat()
            }
            self.referrals.insert_one(referral_data)
            return True
        except Exception as e:
            print(f"Error adding referral: {e}")
            return False
    
    def get_referral_count(self, user_id):
        """Get count of referrals for a user"""
        try:
            count = self.referrals.count_documents({'referrer_id': user_id})
            return count
        except Exception as e:
            print(f"Error getting referral count: {e}")
            return 0
    
    def get_user_referrals(self, user_id):
        """Get all referrals made by a user"""
        try:
            referrals = list(self.referrals.find({'referrer_id': user_id}).sort('created_at', -1))
            return referrals
        except Exception as e:
            print(f"Error getting referrals: {e}")
            return []
    
    def mark_referrals_used(self, user_id):
        """Mark referrals as used when claiming free trial"""
        try:
            self.referrals.update_many(
                {'referrer_id': user_id, 'is_used': False},
                {'$set': {'is_used': True}}
            )
            return True
        except Exception as e:
            print(f"Error marking referrals as used: {e}")
            return False
    
    def get_referral_stats(self):
        """Get referral statistics (admin)"""
        try:
            total_users = self.users.count_documents({})
            total_referrals = self.referrals.count_documents({})
            claimed_trials = self.referrals.count_documents({'is_used': True})
            
            # Top referrers
            pipeline = [
                {'$group': {'_id': '$referrer_id', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            top_refs = list(self.referrals.aggregate(pipeline))
            
            # Get usernames
            top_referrers = []
            for ref in top_refs:
                user = self.users.find_one({'telegram_id': ref['_id']})
                top_referrers.append({
                    'telegram_id': ref['_id'],
                    'username': user.get('username', 'Unknown') if user else 'Unknown',
                    'count': ref['count']
                })
            
            return {
                'total_users': total_users,
                'total_referrals': total_referrals,
                'claimed_trials': claimed_trials,
                'top_referrers': top_referrers
            }
        except Exception as e:
            print(f"Error getting referral stats: {e}")
            return {
                'total_users': 0,
                'total_referrals': 0,
                'claimed_trials': 0,
                'top_referrers': []
            }
    
    # ========== API KEYS ==========
    
    def create_api_key(self, telegram_id, username, plan='free', expiry_days=None, created_by_admin=False):
        """Create new API key for user"""
        self.create_user(telegram_id, username)
        
        if not created_by_admin:
            existing_plan_key = self.api_keys.find_one({
                'telegram_id': telegram_id,
                'plan': plan,
                'is_active': True
            })
            
            if existing_plan_key:
                return None
        
        api_key = self.generate_api_key()
        
        expiry_date = None
        if expiry_days and expiry_days > 0:
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()
        
        key_data = {
            'telegram_id': telegram_id,
            'username': username,
            'api_key': api_key,
            'plan': plan,
            'requests_used': 0,
            'is_active': True,
            'expiry_date': expiry_date,
            'created_by_admin': created_by_admin,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            self.api_keys.insert_one(key_data)
            return api_key
        except Exception as e:
            print(f"Error creating API key: {e}")
            return None
    
    def delete_api_key(self, api_key):
        """Delete API key permanently"""
        try:
            result = self.api_keys.delete_one({'api_key': api_key})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False
    
    def delete_api_key_by_telegram_id(self, telegram_id, plan=None):
        """Delete API key by telegram ID and optional plan"""
        try:
            query = {'telegram_id': telegram_id}
            if plan:
                query['plan'] = plan
            result = self.api_keys.delete_many(query)
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting API keys: {e}")
            return 0
    
    # ========== GIFT CARDS ==========
    
    def create_gift_card(self, plan, max_uses, card_expiry_days=None, api_expiry_days=None, created_by=None, note=""):
        """Create a gift card for redeeming API keys"""
        code = self.generate_gift_code()
        
        card_expiry = None
        if card_expiry_days and card_expiry_days > 0:
            card_expiry = (datetime.now() + timedelta(days=card_expiry_days)).isoformat()
        
        if api_expiry_days is None:
            api_expiry_days = 7 if plan == 'free' else None
        elif api_expiry_days == 0:
            api_expiry_days = None
        
        gift_data = {
            'code': code,
            'plan': plan,
            'max_uses': max_uses,
            'used_count': 0,
            'used_by': [],
            'is_active': True,
            'card_expiry': card_expiry,
            'api_expiry_days': api_expiry_days,
            'created_by': created_by,
            'note': note,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            self.gift_cards.insert_one(gift_data)
            return code
        except Exception as e:
            print(f"Error creating gift card: {e}")
            return None
    
    def redeem_gift_card(self, code, telegram_id, username):
        """Redeem a gift card and create API key"""
        try:
            gift = self.gift_cards.find_one({'code': code.upper()})
            
            if not gift:
                return {'success': False, 'error': 'Invalid gift code'}
            
            if not gift.get('is_active'):
                return {'success': False, 'error': 'Gift code is no longer active'}
            
            if gift.get('card_expiry'):
                expiry = datetime.fromisoformat(gift['card_expiry'])
                if datetime.now() > expiry:
                    return {'success': False, 'error': 'Gift code has expired'}
            
            if gift['used_count'] >= gift['max_uses']:
                return {'success': False, 'error': 'Gift code has been fully redeemed'}
            
            if telegram_id in gift.get('used_by', []):
                return {'success': False, 'error': 'You have already used this gift code'}
            
            api_key = self.create_api_key(
                telegram_id=telegram_id,
                username=username,
                plan=gift['plan'],
                expiry_days=gift.get('api_expiry_days'),
                created_by_admin=False
            )
            
            if not api_key:
                return {'success': False, 'error': f'You already have an active {gift["plan"]} plan key'}
            
            self.gift_cards.update_one(
                {'code': code.upper()},
                {
                    '$inc': {'used_count': 1},
                    '$push': {'used_by': telegram_id},
                    '$set': {'updated_at': datetime.now().isoformat()}
                }
            )
            
            return {
                'success': True,
                'api_key': api_key,
                'plan': gift['plan'],
                'expiry_days': gift.get('api_expiry_days')
            }
            
        except Exception as e:
            print(f"Error redeeming gift card: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_gift_card_api_expiry(self, code, api_expiry_days):
        """Update API key expiry days for a gift card"""
        try:
            if api_expiry_days is not None and api_expiry_days <= 0:
                api_expiry_days = None
            
            self.gift_cards.update_one(
                {'code': code.upper()},
                {
                    '$set': {
                        'api_expiry_days': api_expiry_days,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error updating gift card: {e}")
            return False
    
    def get_gift_card(self, code):
        """Get gift card details"""
        try:
            gift = self.gift_cards.find_one({'code': code.upper()})
            return gift
        except Exception as e:
            print(f"Error getting gift card: {e}")
            return None
    
    def get_all_gift_cards(self):
        """Get all gift cards (admin)"""
        try:
            gifts = list(self.gift_cards.find().sort('created_at', -1))
            return gifts
        except Exception as e:
            print(f"Error getting gift cards: {e}")
            return []
    
    def deactivate_gift_card(self, code):
        """Deactivate a gift card"""
        try:
            self.gift_cards.update_one(
                {'code': code.upper()},
                {
                    '$set': {
                        'is_active': False,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error deactivating gift card: {e}")
            return False
    
    def delete_gift_card(self, code):
        """Delete a gift card permanently"""
        try:
            result = self.gift_cards.delete_one({'code': code.upper()})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting gift card: {e}")
            return False
    
    # ========== VALIDATION & QUERIES ==========
    
    def validate_api_key(self, api_key):
        """Validate API key and return key data"""
        try:
            key = self.api_keys.find_one({'api_key': api_key})
            if not key:
                return None
            
            if key.get('expiry_date'):
                expiry = datetime.fromisoformat(key['expiry_date'])
                if datetime.now() > expiry:
                    self.deactivate_api_key(api_key)
                    return None
            
            return key
        except Exception as e:
            print(f"Error validating API key: {e}")
            return None
    
    def get_user_by_telegram_id(self, telegram_id):
        """Get user by Telegram ID"""
        try:
            user = self.users.find_one({'telegram_id': telegram_id})
            return user
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_api_keys(self, telegram_id):
        """Get all API keys for a user"""
        try:
            keys = list(self.api_keys.find({'telegram_id': telegram_id}))
            return keys
        except Exception as e:
            print(f"Error getting API keys: {e}")
            return []
    
    def get_active_api_keys(self, telegram_id):
        """Get only active API keys for a user"""
        try:
            keys = list(self.api_keys.find({
                'telegram_id': telegram_id,
                'is_active': True
            }))
            
            active_keys = []
            for key in keys:
                if key.get('expiry_date'):
                    expiry = datetime.fromisoformat(key['expiry_date'])
                    if datetime.now() > expiry:
                        self.deactivate_api_key(key['api_key'])
                        continue
                active_keys.append(key)
            
            return active_keys
        except Exception as e:
            print(f"Error getting active keys: {e}")
            return []
    
    def has_active_plan(self, telegram_id, plan):
        """Check if user has active key for specific plan"""
        try:
            key = self.api_keys.find_one({
                'telegram_id': telegram_id,
                'plan': plan,
                'is_active': True
            })
            
            if key and key.get('expiry_date'):
                expiry = datetime.fromisoformat(key['expiry_date'])
                if datetime.now() > expiry:
                    return False
            
            return key is not None
        except Exception as e:
            print(f"Error checking plan: {e}")
            return False
    
    def increment_usage(self, api_key):
        """Increment API usage counter"""
        try:
            self.api_keys.update_one(
                {'api_key': api_key},
                {
                    '$inc': {'requests_used': 1},
                    '$set': {'updated_at': datetime.now().isoformat()}
                }
            )
            return True
        except Exception as e:
            print(f"Error incrementing usage: {e}")
            return False
    
    def deactivate_api_key(self, api_key):
        """Deactivate an API key"""
        try:
            self.api_keys.update_one(
                {'api_key': api_key},
                {
                    '$set': {
                        'is_active': False,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error deactivating key: {e}")
            return False
    
    def activate_api_key(self, api_key):
        """Activate an API key"""
        try:
            self.api_keys.update_one(
                {'api_key': api_key},
                {
                    '$set': {
                        'is_active': True,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error activating key: {e}")
            return False
    
    def set_expiry(self, api_key, days):
        """Set expiry date for API key"""
        try:
            if days <= 0:
                return self.remove_expiry(api_key)
            
            expiry_date = (datetime.now() + timedelta(days=days)).isoformat()
            self.api_keys.update_one(
                {'api_key': api_key},
                {
                    '$set': {
                        'expiry_date': expiry_date,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error setting expiry: {e}")
            return False
    
    def remove_expiry(self, api_key):
        """Remove expiry date (make permanent)"""
        try:
            self.api_keys.update_one(
                {'api_key': api_key},
                {
                    '$set': {
                        'expiry_date': None,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error removing expiry: {e}")
            return False
    
    # ========== ADMIN FUNCTIONS ==========
    
    def get_all_users(self):
        """Get all users (admin function)"""
        try:
            users = list(self.users.find())
            return users
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def get_all_api_keys(self):
        """Get all API keys (admin function)"""
        try:
            keys = list(self.api_keys.find())
            return keys
        except Exception as e:
            print(f"Error getting API keys: {e}")
            return []
    
    def get_stats(self):
        """Get system statistics"""
        try:
            total_users = self.users.count_documents({})
            total_keys = self.api_keys.count_documents({})
            active_keys = self.api_keys.count_documents({'is_active': True})
            total_gifts = self.gift_cards.count_documents({})
            active_gifts = self.gift_cards.count_documents({'is_active': True})
            total_referrals = self.referrals.count_documents({})
            
            # Total requests
            pipeline = [
                {'$group': {'_id': None, 'total': {'$sum': '$requests_used'}}}
            ]
            result = list(self.api_keys.aggregate(pipeline))
            total_requests = result[0]['total'] if result else 0
            
            # Total gift redemptions
            gift_pipeline = [
                {'$group': {'_id': None, 'total': {'$sum': '$used_count'}}}
            ]
            gift_result = list(self.gift_cards.aggregate(gift_pipeline))
            total_redemptions = gift_result[0]['total'] if gift_result else 0
            
            return {
                'total_users': total_users,
                'total_keys': total_keys,
                'active_keys': active_keys,
                'total_requests': total_requests,
                'total_gifts': total_gifts,
                'active_gifts': active_gifts,
                'total_redemptions': total_redemptions,
                'total_referrals': total_referrals
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def deactivate_expired_keys(self):
        """Deactivate all expired keys (run periodically)"""
        try:
            all_keys = self.api_keys.find({'is_active': True, 'expiry_date': {'$ne': None}})
            
            count = 0
            for key in all_keys:
                expiry = datetime.fromisoformat(key['expiry_date'])
                if datetime.now() > expiry:
                    self.deactivate_api_key(key['api_key'])
                    count += 1
            
            return count
        except Exception as e:
            print(f"Error deactivating expired keys: {e}")
            return 0

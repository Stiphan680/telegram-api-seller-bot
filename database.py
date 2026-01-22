import os
import secrets
from datetime import datetime, timedelta
from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DB_NAME]
        self.users = self.db['users']
        self.api_keys = self.db['api_keys']  # Separate collection for API keys
        
        # Create indexes
        self.users.create_index('telegram_id', unique=True)
        self.api_keys.create_index('api_key', unique=True)
        self.api_keys.create_index('telegram_id')
    
    def generate_api_key(self):
        """Generate a unique API key"""
        return f"sk-{secrets.token_urlsafe(32)}"
    
    def create_user(self, telegram_id, username):
        """Create user if not exists"""
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
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def create_api_key(self, telegram_id, username, plan='free', expiry_days=None):
        """Create new API key for user (allows multiple keys)"""
        # Create user first if not exists
        self.create_user(telegram_id, username)
        
        # Check if user already has this plan
        existing_plan_key = self.api_keys.find_one({
            'telegram_id': telegram_id,
            'plan': plan,
            'is_active': True
        })
        
        if existing_plan_key:
            return None  # Already has active key for this plan
        
        api_key = self.generate_api_key()
        
        # Calculate expiry date
        expiry_date = None
        if expiry_days:
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()
        
        key_data = {
            'telegram_id': telegram_id,
            'username': username,
            'api_key': api_key,
            'plan': plan,
            'requests_used': 0,
            'is_active': True,
            'expiry_date': expiry_date,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            self.api_keys.insert_one(key_data)
            return api_key
        except Exception as e:
            print(f"Error creating API key: {e}")
            return None
    
    def validate_api_key(self, api_key):
        """Validate API key and return key data"""
        try:
            key = self.api_keys.find_one({'api_key': api_key})
            if not key:
                return None
            
            # Check if expired
            if key.get('expiry_date'):
                expiry = datetime.fromisoformat(key['expiry_date'])
                if datetime.now() > expiry:
                    # Auto-deactivate expired key
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
            
            # Filter out expired keys
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
            
            # Total requests
            pipeline = [
                {'$group': {'_id': None, 'total': {'$sum': '$requests_used'}}}
            ]
            result = list(self.api_keys.aggregate(pipeline))
            total_requests = result[0]['total'] if result else 0
            
            return {
                'total_users': total_users,
                'total_keys': total_keys,
                'active_keys': active_keys,
                'total_requests': total_requests
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def deactivate_expired_keys(self):
        """Deactivate all expired keys (run periodically)"""
        try:
            # Find all expired keys
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
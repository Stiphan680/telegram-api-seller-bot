import os
import secrets
from datetime import datetime
from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DB_NAME]
        self.users = self.db['users']
        
        # Create indexes
        self.users.create_index('telegram_id', unique=True)
        self.users.create_index('api_key', unique=True)
    
    def generate_api_key(self):
        """Generate a unique API key"""
        return f"sk-{secrets.token_urlsafe(32)}"
    
    def create_api_key(self, telegram_id, username, plan='free'):
        """Create new API key for user"""
        api_key = self.generate_api_key()
        
        user_data = {
            'telegram_id': telegram_id,
            'username': username,
            'api_key': api_key,
            'plan': plan,
            'requests_used': 0,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            self.users.insert_one(user_data)
            return api_key
        except Exception as e:
            print(f"Error creating API key: {e}")
            return None
    
    def validate_api_key(self, api_key):
        """Validate API key and return user data"""
        try:
            user = self.users.find_one({'api_key': api_key})
            return user
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
    
    def increment_usage(self, api_key):
        """Increment API usage counter"""
        try:
            self.users.update_one(
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
    
    def update_user_plan(self, telegram_id, plan):
        """Update user's plan"""
        try:
            self.users.update_one(
                {'telegram_id': telegram_id},
                {
                    '$set': {
                        'plan': plan,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error updating plan: {e}")
            return False
    
    def deactivate_api_key(self, api_key):
        """Deactivate an API key"""
        try:
            self.users.update_one(
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
    
    def get_all_users(self):
        """Get all users (admin function)"""
        try:
            users = list(self.users.find())
            return users
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
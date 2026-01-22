import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    
    # MongoDB Connection
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://username:password@cluster.mongodb.net/')
    DB_NAME = os.getenv('DB_NAME', 'api_seller')
    
    # API Gateway Base URL (Your deployed Render URL)
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://your-api.onrender.com')
    
    # Admin Telegram IDs (comma separated)
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',') if os.getenv('ADMIN_IDS') else []
    
    # Payment Gateway (Optional - for future integration)
    PAYMENT_GATEWAY_KEY = os.getenv('PAYMENT_GATEWAY_KEY', '')
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT_FREE = int(os.getenv('RATE_LIMIT_FREE', 10))
    RATE_LIMIT_BASIC = int(os.getenv('RATE_LIMIT_BASIC', 100))
    RATE_LIMIT_PRO = int(os.getenv('RATE_LIMIT_PRO', 1000))
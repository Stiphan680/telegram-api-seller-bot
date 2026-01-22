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
    
    # ===== AI Backend Configuration =====
    
    # Perplexity API (Premium - Optional)
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
    
    # Gemini API (Free)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Groq API (Free)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    
    # Backend Selection
    # Options: 'perplexity', 'gemini', 'groq', 'auto'
    # 'auto' = Use Perplexity if available, else fallback to Gemini/Groq
    AI_BACKEND = os.getenv('AI_BACKEND', 'auto')
    
    @staticmethod
    def get_available_backends():
        """Get list of configured AI backends"""
        backends = []
        
        if Config.PERPLEXITY_API_KEY:
            backends.append('perplexity')
        if Config.GEMINI_API_KEY:
            backends.append('gemini')
        if Config.GROQ_API_KEY:
            backends.append('groq')
        
        return backends
    
    @staticmethod
    def is_perplexity_enabled():
        """Check if Perplexity backend is available"""
        return bool(Config.PERPLEXITY_API_KEY and len(Config.PERPLEXITY_API_KEY) > 20)

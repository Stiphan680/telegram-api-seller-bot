from flask import Flask, request, jsonify
import requests
import json
from database import Database
from config import Config
from datetime import datetime

app = Flask(__name__)
db = Database()

def get_chatbot_response(question):
    """Forward request to main chatbot API"""
    english_instruction = "Please respond in English."
    enhanced_question = f"{english_instruction} {question}"
    
    payload = {
        "messages": [
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": enhanced_question}
        ]
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    url = "https://chatbot-ji1z.onrender.com/chatbot-ji1z"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            api_response = response.json()
            return {
                "success": True,
                "response": api_response['choices'][0]['message']['content']
            }
        else:
            return {
                "success": False,
                "error": f"API returned status code {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }

@app.route('/', methods=['GET'])
def home():
    """API Information"""
    return jsonify({
        "message": "API Seller Gateway",
        "version": "2.0",
        "status": "active",
        "endpoints": {
            "/": "GET - API information",
            "/chat": "POST - Chat with AI (requires API key)",
            "/validate": "POST - Validate API key",
            "/usage": "GET - Check your API usage"
        },
        "note": "API key required in header: X-API-Key"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint with API key validation"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API key required. Add 'X-API-Key' header."
            }), 401
        
        # Validate API key (also checks expiry)
        key_data = db.validate_api_key(api_key)
        if not key_data:
            return jsonify({
                "success": False,
                "error": "Invalid or expired API key"
            }), 401
        
        # Check if key is active
        if not key_data['is_active']:
            return jsonify({
                "success": False,
                "error": "API key is disabled. Contact support."
            }), 403
        
        # Get question from request
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'question' field in request body"
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                "success": False,
                "error": "Question cannot be empty"
            }), 400
        
        # Update usage count
        db.increment_usage(api_key)
        
        # Get chatbot response
        result = get_chatbot_response(question)
        
        # Add usage info to response
        if result['success']:
            result['usage'] = {
                "requests_used": key_data['requests_used'] + 1,
                "plan": key_data['plan']
            }
            
            # Add expiry info if exists
            if key_data.get('expiry_date'):
                try:
                    expiry = datetime.fromisoformat(key_data['expiry_date'])
                    days_left = (expiry - datetime.now()).days
                    result['usage']['expires_in_days'] = max(0, days_left)
                    result['usage']['expiry_date'] = key_data['expiry_date'][:10]
                except:
                    pass
        
        return jsonify(result), 200 if result['success'] else 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/validate', methods=['POST'])
def validate_key():
    """Validate API key"""
    try:
        data = request.get_json()
        api_key = data.get('api_key') or request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                "valid": False,
                "error": "API key required"
            }), 400
        
        key_data = db.validate_api_key(api_key)
        
        if key_data:
            response_data = {
                "valid": True,
                "telegram_id": key_data['telegram_id'],
                "plan": key_data['plan'],
                "requests_used": key_data['requests_used'],
                "is_active": key_data['is_active'],
                "created_at": key_data['created_at']
            }
            
            # Add expiry info if exists
            if key_data.get('expiry_date'):
                try:
                    expiry = datetime.fromisoformat(key_data['expiry_date'])
                    days_left = (expiry - datetime.now()).days
                    response_data['expiry_date'] = key_data['expiry_date'][:10]
                    response_data['expires_in_days'] = max(0, days_left)
                    response_data['is_expired'] = datetime.now() > expiry
                except:
                    pass
            else:
                response_data['expiry_date'] = None
                response_data['expires_in_days'] = None
                response_data['is_expired'] = False
            
            return jsonify(response_data), 200
        else:
            return jsonify({
                "valid": False,
                "error": "Invalid or expired API key"
            }), 401
            
    except Exception as e:
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 500

@app.route('/usage', methods=['GET'])
def get_usage():
    """Get API usage statistics"""
    try:
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API key required in header"
            }), 401
        
        key_data = db.validate_api_key(api_key)
        if not key_data:
            return jsonify({
                "success": False,
                "error": "Invalid or expired API key"
            }), 401
        
        response_data = {
            "success": True,
            "telegram_id": key_data['telegram_id'],
            "plan": key_data['plan'],
            "requests_used": key_data['requests_used'],
            "is_active": key_data['is_active'],
            "created_at": key_data['created_at'],
            "api_key": api_key[:10] + "..." + api_key[-5:]  # Masked key
        }
        
        # Add expiry info if exists
        if key_data.get('expiry_date'):
            try:
                expiry = datetime.fromisoformat(key_data['expiry_date'])
                now = datetime.now()
                days_left = (expiry - now).days
                hours_left = (expiry - now).seconds // 3600
                
                response_data['expiry_date'] = key_data['expiry_date'][:10]
                response_data['expires_in_days'] = max(0, days_left)
                response_data['expires_in_hours'] = max(0, hours_left) if days_left == 0 else None
                response_data['is_expired'] = now > expiry
            except:
                pass
        else:
            response_data['expiry_date'] = None
            response_data['expires_in_days'] = None
            response_data['is_expired'] = False
            response_data['note'] = "No expiry (Permanent until plan renewal)"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "message": "API Gateway is running",
        "version": "2.0",
        "features": [
            "API key validation",
            "Expiry tracking",
            "Multiple keys per user",
            "Usage monitoring"
        ]
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
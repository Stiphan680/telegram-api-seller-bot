from flask import Flask, request, jsonify
import requests
import json
import os
from database import Database
from config import Config
from datetime import datetime
import base64
import io

app = Flask(__name__)
db = Database()

# Premium AI Services Configuration
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY') or os.getenv('CLAUDE_API_KEY', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY', '')
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY') or os.getenv('PERPLEXITY_API_KEY', '')

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

def generate_image_pollinations(prompt):
    """Generate image using Pollinations AI (Free)"""
    try:
        # Pollinations.ai - Free high-quality image generation
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        return {
            "success": True,
            "image_url": image_url,
            "provider": "Pollinations AI",
            "model": "Flux",
            "resolution": "1024x1024",
            "note": "High-quality AI-generated image"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_video_pollinations(prompt, duration=3):
    """Generate video using Pollinations AI (Free)"""
    try:
        # Pollinations.ai video generation
        encoded_prompt = requests.utils.quote(prompt)
        video_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&model=video&duration={duration}"
        
        return {
            "success": True,
            "video_url": video_url,
            "provider": "Pollinations AI",
            "model": "Mochi/AnimateDiff",
            "resolution": "1024x576",
            "duration": f"{duration}s",
            "note": "AI-generated video animation"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def code_expert_claude(question, language="python"):
    """Code expert using Claude Sonnet 3.5 (if available)"""
    try:
        if not CLAUDE_API_KEY:
            # Fallback to Perplexity for code assistance
            if PERPLEXITY_API_KEY:
                return code_expert_perplexity(question, language)
            else:
                return code_expert_fallback(question, language)
        
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        system_prompt = f"""You are an expert {language} programmer and code reviewer.
Provide clean, efficient, and well-documented code.
Explain your solutions clearly.
Follow best practices and modern standards.
Include error handling where appropriate."""
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": question}
            ]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            code_response = result['content'][0]['text']
            
            return {
                "success": True,
                "response": code_response,
                "model": "Claude 3.5 Sonnet",
                "provider": "Anthropic",
                "language": language,
                "tokens_used": result.get('usage', {}).get('output_tokens', 0)
            }
        else:
            # Fallback on error
            return code_expert_fallback(question, language)
            
    except Exception as e:
        return code_expert_fallback(question, language)

def code_expert_perplexity(question, language="python"):
    """Code expert using Perplexity as fallback"""
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": f"You are an expert {language} programmer. Provide clean code with explanations."
                },
                {"role": "user", "content": question}
            ],
            "temperature": 0.3,
            "max_tokens": 2048
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result['choices'][0]['message']['content'],
                "model": "Perplexity Sonar",
                "provider": "Perplexity",
                "language": language
            }
    except:
        pass
    
    return code_expert_fallback(question, language)

def code_expert_fallback(question, language):
    """Fallback code expert using main chatbot"""
    enhanced_question = f"As an expert {language} programmer, {question}. Provide clean, well-documented code with explanations."
    result = get_chatbot_response(enhanced_question)
    
    if result['success']:
        result['model'] = "Gemini/Groq Fallback"
        result['provider'] = "Advanced AI"
        result['language'] = language
    
    return result

@app.route('/', methods=['GET'])
def home():
    """API Information"""
    return jsonify({
        "message": "API Seller Gateway - Premium AI Features",
        "version": "3.0",
        "status": "active",
        "powered_by": "Claude 3.5 Sonnet + Pollinations AI",
        "endpoints": {
            "/": "GET - API information",
            "/chat": "POST - Chat with AI (requires API key)",
            "/image": "POST - Generate images (requires API key)",
            "/video": "POST - Generate videos (requires API key)",
            "/code": "POST - Code expert assistant (requires API key)",
            "/validate": "POST - Validate API key",
            "/usage": "GET - Check your API usage"
        },
        "features": [
            "🤖 Claude 3.5 Sonnet AI Chat",
            "🎨 AI Image Generation",
            "🎬 AI Video Generation",
            "💻 Code Expert Assistant",
            "🔐 API Key Authentication",
            "📊 Usage Tracking"
        ],
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

@app.route('/image', methods=['POST'])
def generate_image():
    """Generate AI images"""
    try:
        # Validate API key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API key required"
            }), 401
        
        key_data = db.validate_api_key(api_key)
        if not key_data or not key_data['is_active']:
            return jsonify({
                "success": False,
                "error": "Invalid or expired API key"
            }), 401
        
        # Get prompt
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'prompt' field"
            }), 400
        
        prompt = data['prompt'].strip()
        if not prompt:
            return jsonify({
                "success": False,
                "error": "Prompt cannot be empty"
            }), 400
        
        # Update usage
        db.increment_usage(api_key)
        
        # Generate image
        result = generate_image_pollinations(prompt)
        
        if result['success']:
            result['usage'] = {
                "requests_used": key_data['requests_used'] + 1,
                "plan": key_data['plan']
            }
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/video', methods=['POST'])
def generate_video():
    """Generate AI videos"""
    try:
        # Validate API key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API key required"
            }), 401
        
        key_data = db.validate_api_key(api_key)
        if not key_data or not key_data['is_active']:
            return jsonify({
                "success": False,
                "error": "Invalid or expired API key"
            }), 401
        
        # Get prompt and duration
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'prompt' field"
            }), 400
        
        prompt = data['prompt'].strip()
        duration = data.get('duration', 3)  # Default 3 seconds
        
        if not prompt:
            return jsonify({
                "success": False,
                "error": "Prompt cannot be empty"
            }), 400
        
        # Validate duration
        if not isinstance(duration, (int, float)) or duration < 1 or duration > 10:
            duration = 3
        
        # Update usage
        db.increment_usage(api_key)
        
        # Generate video
        result = generate_video_pollinations(prompt, duration)
        
        if result['success']:
            result['usage'] = {
                "requests_used": key_data['requests_used'] + 1,
                "plan": key_data['plan']
            }
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/code', methods=['POST'])
def code_expert():
    """Code expert assistant powered by Claude 3.5 Sonnet"""
    try:
        # Validate API key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API key required"
            }), 401
        
        key_data = db.validate_api_key(api_key)
        if not key_data or not key_data['is_active']:
            return jsonify({
                "success": False,
                "error": "Invalid or expired API key"
            }), 401
        
        # Get question and language
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'question' field"
            }), 400
        
        question = data['question'].strip()
        language = data.get('language', 'python').lower()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "Question cannot be empty"
            }), 400
        
        # Update usage
        db.increment_usage(api_key)
        
        # Get code expert response
        result = code_expert_claude(question, language)
        
        if result['success']:
            result['usage'] = {
                "requests_used": key_data['requests_used'] + 1,
                "plan": key_data['plan']
            }
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
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
                "created_at": key_data['created_at'],
                "features": [
                    "AI Chat",
                    "Image Generation",
                    "Video Generation",
                    "Code Expert"
                ]
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
            "api_key": api_key[:10] + "..." + api_key[-5:],  # Masked key
            "available_features": [
                "AI Chat (Claude 3.5 Sonnet)",
                "Image Generation (Flux)",
                "Video Generation (Mochi)",
                "Code Expert (Claude)"
            ]
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
        "version": "3.0",
        "powered_by": "Claude 3.5 Sonnet + Pollinations AI",
        "features": [
            "🤖 AI Chat",
            "🎨 Image Generation",
            "🎬 Video Generation",
            "💻 Code Expert",
            "🔐 API Key Validation",
            "⏱️ Expiry Tracking",
            "📊 Usage Monitoring"
        ],
        "services": {
            "claude_api": "available" if CLAUDE_API_KEY else "fallback",
            "perplexity_api": "available" if PERPLEXITY_API_KEY else "disabled",
            "pollinations_ai": "available",
            "gemini_groq": "available"
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
Advanced AI Backend - Claude Sonnet 4.5 Level Features
Uses Multiple Free AI APIs for Premium Experience
"""

import os
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, List, Any
from flask import Flask, request, jsonify, Response, stream_with_context
import google.generativeai as genai
from groq import Groq
import random

class AdvancedAIBackend:
    def __init__(self):
        """Initialize multiple AI providers for redundancy and features"""
        
        # Configure Gemini (Free, High Quality)
        gemini_key = os.getenv('GEMINI_API_KEY', '')
        if gemini_key:
            genai.configure(api_key=gemini_key)
        
        # Configure Groq (Free, Ultra Fast) - FIX: Remove self._client parameter
        groq_key = os.getenv('GROQ_API_KEY', '')
        if groq_key:
            self.groq_client = Groq(api_key=groq_key)  # Fixed: removed invalid parameter
        else:
            self.groq_client = None
        
        # Configure HuggingFace (Free)
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        
        # Models configuration
        self.models = {
            'gemini': {
                'name': 'gemini-2.0-flash-exp',
                'provider': 'google',
                'speed': 'fast',
                'quality': 'high',
                'context': 1000000,  # 1M tokens
                'features': ['chat', 'code', 'analysis', 'vision', 'long_context']
            },
            'groq': {
                'name': 'llama-3.3-70b-versatile',
                'provider': 'groq',
                'speed': 'ultra_fast',
                'quality': 'high',
                'context': 32000,
                'features': ['chat', 'code', 'fast_response']
            },
            'mixtral': {
                'name': 'mixtral-8x7b-32768',
                'provider': 'groq',
                'speed': 'fast',
                'quality': 'medium',
                'context': 32768,
                'features': ['chat', 'multilingual']
            }
        }
        
        # Conversation memory (in-memory, use Redis in production)
        self.conversations = {}
        self.max_history = 20  # Keep last 20 messages
        
        # System prompts for different modes
        self.system_prompts = {
            'default': "You are a highly intelligent AI assistant. Be helpful, accurate, and concise.",
            'creative': "You are a creative AI assistant with imagination and flair. Be innovative and think outside the box.",
            'professional': "You are a professional AI assistant. Provide formal, well-structured responses suitable for business contexts.",
            'casual': "You are a friendly AI assistant. Use casual language and be conversational.",
            'educational': "You are an educational AI tutor. Explain concepts clearly with examples and step-by-step guidance.",
            'code': "You are an expert programming assistant. Provide clean, efficient code with explanations.",
            'analyst': "You are a data analyst. Provide detailed analysis with insights and actionable recommendations."
        }
        
    async def get_response(self, 
                          question: str,
                          user_id: str = None,
                          language: str = 'english',
                          tone: str = 'default',
                          include_context: bool = False,
                          max_tokens: int = 4096,
                          temperature: float = 0.7,
                          stream: bool = False) -> Dict[str, Any]:
        """
        Get AI response with advanced features
        Mimics Claude Sonnet 4.5 capabilities using free APIs
        """
        
        try:
            # Get conversation history if context enabled
            history = []
            if include_context and user_id:
                history = self.conversations.get(user_id, [])
            
            # Select best model based on request
            model = self._select_best_model(question, tone)
            
            # Build enhanced prompt
            enhanced_prompt = self._build_enhanced_prompt(
                question, tone, language, history
            )
            
            # Get response from selected model
            if stream:
                return await self._stream_response(model, enhanced_prompt, temperature, max_tokens)
            else:
                response_data = await self._get_model_response(
                    model, enhanced_prompt, temperature, max_tokens
                )
                
                # Save to conversation history
                if include_context and user_id:
                    self._update_conversation(user_id, question, response_data['response'])
                
                return response_data
                
        except Exception as e:
            print(f"Error in get_response: {e}")
            return await self._fallback_response(question, language)
    
    def _select_best_model(self, question: str, tone: str) -> str:
        """Select best model based on query characteristics"""
        
        # For code-related queries, prefer Groq (faster)
        code_keywords = ['code', 'python', 'javascript', 'function', 'class', 'api', 'debug']
        if any(kw in question.lower() for kw in code_keywords) and self.groq_client:
            return 'groq'
        
        # For creative tasks, use Gemini
        creative_keywords = ['story', 'poem', 'creative', 'imagine', 'design']
        if any(kw in question.lower() for kw in creative_keywords) or tone == 'creative':
            return 'gemini'
        
        # For long context, use Gemini (1M tokens)
        if len(question) > 2000:
            return 'gemini'
        
        # Default: Use Gemini (best quality)
        return 'gemini'
    
    def _build_enhanced_prompt(self, question: str, tone: str, language: str, history: List) -> str:
        """Build enhanced prompt with system instructions"""
        
        system_prompt = self.system_prompts.get(tone, self.system_prompts['default'])
        
        # Add language instruction
        if language.lower() != 'english':
            lang_map = {
                'hindi': 'हिंदी',
                'spanish': 'Español',
                'french': 'Français',
                'german': 'Deutsch',
                'chinese': '中文',
                'japanese': '日本語',
                'arabic': 'العربية'
            }
            lang_name = lang_map.get(language.lower(), language)
            system_prompt += f"\n\nIMPORTANT: Respond in {lang_name} language."
        
        # Build full prompt with context
        if history:
            context_text = "\n\nPrevious conversation:\n"
            for msg in history[-6:]:  # Last 3 exchanges
                context_text += f"User: {msg['user']}\nAssistant: {msg['assistant']}\n"
            full_prompt = f"{system_prompt}\n{context_text}\n\nUser: {question}\nAssistant:"
        else:
            full_prompt = f"{system_prompt}\n\nUser: {question}\nAssistant:"
        
        return full_prompt
    
    async def _get_model_response(self, model_name: str, prompt: str, 
                                   temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Get response from specific model"""
        
        start_time = time.time()
        
        try:
            if model_name == 'gemini':
                response = await self._gemini_response(prompt, temperature, max_tokens)
            elif model_name in ['groq', 'mixtral']:
                response = await self._groq_response(model_name, prompt, temperature, max_tokens)
            else:
                response = await self._gemini_response(prompt, temperature, max_tokens)
            
            latency = time.time() - start_time
            
            return {
                'success': True,
                'response': response,
                'model': model_name,
                'latency': round(latency, 2),
                'tokens': len(response.split()),  # Approximate
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error with {model_name}: {e}")
            # Try fallback
            if model_name != 'gemini':
                return await self._get_model_response('gemini', prompt, temperature, max_tokens)
            raise
    
    async def _gemini_response(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Get response from Gemini (Google)"""
        
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens,
                'top_p': 0.95,
                'top_k': 40
            }
        )
        
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    
    async def _groq_response(self, model_name: str, prompt: str, 
                            temperature: float, max_tokens: int) -> str:
        """Get response from Groq (Ultra Fast)"""
        
        if not self.groq_client:
            # Fallback to Gemini if Groq not available
            return await self._gemini_response(prompt, temperature, max_tokens)
        
        model_map = {
            'groq': 'llama-3.3-70b-versatile',
            'mixtral': 'mixtral-8x7b-32768'
        }
        
        response = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model=model_map.get(model_name, 'llama-3.3-70b-versatile'),
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95
        )
        
        return response.choices[0].message.content
    
    async def _stream_response(self, model_name: str, prompt: str,
                               temperature: float, max_tokens: int):
        """Stream response for real-time output"""
        
        try:
            if model_name == 'gemini':
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = model.generate_content(prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
            
            elif model_name in ['groq', 'mixtral'] and self.groq_client:
                model_map = {
                    'groq': 'llama-3.3-70b-versatile',
                    'mixtral': 'mixtral-8x7b-32768'
                }
                
                stream = self.groq_client.chat.completions.create(
                    model=model_map[model_name],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'text': chunk.choices[0].delta.content})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    async def _fallback_response(self, question: str, language: str) -> Dict[str, Any]:
        """Fallback response if all models fail"""
        
        fallback_text = {
            'english': "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
            'hindi': "क्षमा करें, मुझे तकनीकी समस्या हो रही है। कृपया थोड़ी देर बाद पुनः प्रयास करें।"
        }
        
        return {
            'success': False,
            'response': fallback_text.get(language, fallback_text['english']),
            'error': 'All models unavailable',
            'timestamp': datetime.now().isoformat(),
            'fallback_needed': True
        }
    
    def _update_conversation(self, user_id: str, user_msg: str, assistant_msg: str):
        """Update conversation history"""
        
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            'user': user_msg,
            'assistant': assistant_msg,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent messages
        if len(self.conversations[user_id]) > self.max_history:
            self.conversations[user_id] = self.conversations[user_id][-self.max_history:]
    
    def clear_conversation(self, user_id: str):
        """Clear conversation history for user"""
        if user_id in self.conversations:
            del self.conversations[user_id]
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text - simplified without complex parsing"""
        
        analysis_prompt = f"Analyze this text briefly: sentiment, main topics, and tone.\n\nText: {text}"
        
        try:
            response = await self._gemini_response(analysis_prompt, 0.3, 512)
            
            return {
                'success': True,
                'analysis': response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def summarize_content(self, content: str, style: str = 'concise') -> Dict[str, Any]:
        """Summarize content in different styles"""
        
        style_prompts = {
            'concise': "Summarize in 2-3 clear, concise sentences:",
            'bullet': "Summarize in 5-7 bullet points covering key information:",
            'detailed': "Provide a detailed, comprehensive summary covering all major points:"
        }
        
        prompt = f"{style_prompts.get(style, style_prompts['concise'])}\n\n{content}"
        
        try:
            summary = await self._gemini_response(prompt, 0.3, 2048)
            
            return {
                'success': True,
                'summary': summary,
                'style': style,
                'original_length': len(content),
                'summary_length': len(summary),
                'compression_ratio': round(len(summary) / len(content), 2)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def code_assistance(self, code: str = None, task: str = None, 
                             language: str = 'python') -> Dict[str, Any]:
        """Advanced code assistance"""
        
        if code:
            prompt = f"Analyze this {language} code: explain, find bugs, suggest improvements.\n\n```{language}\n{code}\n```"
        elif task:
            prompt = f"Generate clean {language} code for: {task}\n\nInclude: code with comments, usage example."
        else:
            return {'success': False, 'error': 'Provide either code or task'}
        
        try:
            # Use Groq if available for code tasks (faster)
            if self.groq_client:
                response = await self._groq_response('groq', prompt, 0.2, 3000)
            else:
                response = await self._gemini_response(prompt, 0.2, 3000)
            
            return {
                'success': True,
                'response': response,
                'language': language,
                'type': 'debug' if code else 'generate'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Flask App
app = Flask(__name__)
ai_backend = AdvancedAIBackend()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'Advanced AI API',
        'version': '2.0',
        'status': 'active',
        'models': ['Gemini 2.0 Flash', 'Groq Llama 3.3', 'Mixtral 8x7B'],
        'features': ['Multi-language', 'Conversation context', 'Code assistance', 'Streaming', '100% FREE']
    })

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.json
        question = data.get('question', '')
        if not question:
            return jsonify({'success': False, 'error': 'Question required'}), 400
        
        response = await ai_backend.get_response(
            question=question,
            user_id=data.get('user_id', 'anonymous'),
            language=data.get('language', 'english'),
            tone=data.get('tone', 'default'),
            include_context=data.get('include_context', False),
            max_tokens=data.get('max_tokens', 4096),
            temperature=data.get('temperature', 0.7)
        )
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stream', methods=['POST'])
async def stream_chat():
    try:
        data = request.json
        question = data.get('question', '')
        if not question:
            return jsonify({'error': 'Question required'}), 400
        
        model = ai_backend._select_best_model(question, data.get('tone', 'default'))
        prompt = ai_backend._build_enhanced_prompt(
            question, 
            data.get('tone', 'default'), 
            data.get('language', 'english'), 
            []
        )
        
        return Response(
            stream_with_context(
                ai_backend._stream_response(
                    model, prompt, 
                    data.get('temperature', 0.7), 
                    data.get('max_tokens', 4096)
                )
            ),
            mimetype='text/event-stream'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
async def analyze():
    try:
        text = request.json.get('text', '')
        if not text:
            return jsonify({'error': 'Text required'}), 400
        result = await ai_backend.analyze_text(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/summarize', methods=['POST'])
async def summarize():
    try:
        content = request.json.get('content', '')
        if not content:
            return jsonify({'error': 'Content required'}), 400
        result = await ai_backend.summarize_content(
            content, 
            request.json.get('style', 'concise')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/code', methods=['POST'])
async def code_assist():
    try:
        result = await ai_backend.code_assistance(
            request.json.get('code'),
            request.json.get('task'),
            request.json.get('language', 'python')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_history():
    try:
        user_id = request.json.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        ai_backend.clear_conversation(user_id)
        return jsonify({'success': True, 'message': 'Conversation cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models': ['gemini', 'groq', 'mixtral'],
        'version': '2.0'
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

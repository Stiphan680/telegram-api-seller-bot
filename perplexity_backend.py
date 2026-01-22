"""
Perplexity AI Backend - Premium Search + AI
Easily switchable - can be enabled/disabled without affecting other backends
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any

class PerplexityBackend:
    def __init__(self, api_key: str = None):
        """Initialize Perplexity AI client"""
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY', '')
        self.base_url = "https://api.perplexity.ai"
        self.chat_endpoint = f"{self.base_url}/chat/completions"
        
        # Available Perplexity models
        self.models = {
            'sonar': 'sonar',  # Best for search + reasoning
            'sonar-pro': 'sonar-pro',  # Premium model
            'sonar-reasoning': 'sonar-reasoning',  # Deep reasoning
        }
        
        # Default model
        self.default_model = 'sonar'
        
        # Conversation memory
        self.conversations = {}
        self.max_history = 10
        
        if self.api_key:
            print(f"✅ Perplexity Backend initialized with API key: {self.api_key[:10]}...")
        else:
            print("⚠️ Perplexity API key not configured")
    
    def is_available(self) -> bool:
        """Check if Perplexity API is available"""
        return bool(self.api_key and len(self.api_key) > 20)
    
    def get_response(self, 
                    question: str,
                    user_id: str = None,
                    model: str = None,
                    temperature: float = 0.7,
                    max_tokens: int = 4096,
                    include_context: bool = False,
                    search_mode: bool = True) -> Dict[str, Any]:
        """
        Get AI response from Perplexity
        
        Args:
            question: User question
            user_id: User ID for conversation tracking
            model: Model name (sonar, sonar-pro, sonar-reasoning)
            temperature: Creativity (0-1)
            max_tokens: Max response length
            include_context: Include conversation history
            search_mode: Use internet search (recommended for Perplexity)
        
        Returns:
            Dict with response and metadata
        """
        
        if not self.is_available():
            return {
                'success': False,
                'error': 'Perplexity API key not configured',
                'fallback': True
            }
        
        try:
            # Get conversation history if context enabled
            messages = []
            
            if include_context and user_id and user_id in self.conversations:
                # Add conversation history
                history = self.conversations[user_id][-6:]  # Last 3 exchanges
                for msg in history:
                    messages.append({"role": "user", "content": msg['user']})
                    messages.append({"role": "assistant", "content": msg['assistant']})
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model or self.default_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.9,
                "stream": False,
                "search_domain_filter": [],  # Empty = search all domains
                "return_images": False,
                "return_related_questions": False,
                "search_recency_filter": "month",  # month, week, day
                "top_k": 0,
                "presence_penalty": 0,
                "frequency_penalty": 1
            }
            
            # Make API call
            start_time = time.time()
            response = requests.post(
                self.chat_endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            latency = time.time() - start_time
            
            # Check response
            if response.status_code != 200:
                error_msg = f"Perplexity API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
                
                return {
                    'success': False,
                    'error': error_msg,
                    'fallback': True,
                    'status_code': response.status_code
                }
            
            # Parse response
            data = response.json()
            
            ai_response = data['choices'][0]['message']['content']
            
            # Extract citations if available
            citations = []
            if 'citations' in data:
                citations = data['citations']
            
            # Update conversation history
            if include_context and user_id:
                self._update_conversation(user_id, question, ai_response)
            
            return {
                'success': True,
                'response': ai_response,
                'model': data.get('model', model or self.default_model),
                'citations': citations,
                'usage': data.get('usage', {}),
                'latency': round(latency, 2),
                'timestamp': datetime.now().isoformat(),
                'backend': 'perplexity'
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Perplexity API timeout',
                'fallback': True
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'fallback': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Perplexity error: {str(e)}',
                'fallback': True
            }
    
    def search(self, query: str, recency: str = "month") -> Dict[str, Any]:
        """
        Perplexity-optimized search with AI reasoning
        
        Args:
            query: Search query
            recency: Time filter (month, week, day)
        
        Returns:
            Search results with AI summary
        """
        
        # Enhance query for better search results
        search_prompt = f"Search and provide detailed information about: {query}"
        
        return self.get_response(
            question=search_prompt,
            model='sonar',  # Best for search
            search_mode=True,
            temperature=0.5  # Lower for factual responses
        )
    
    def reasoning(self, question: str, depth: str = "normal") -> Dict[str, Any]:
        """
        Deep reasoning mode for complex questions
        
        Args:
            question: Complex question requiring reasoning
            depth: Reasoning depth (normal, deep)
        
        Returns:
            Detailed reasoning response
        """
        
        model = 'sonar-reasoning' if depth == 'deep' else 'sonar'
        
        reasoning_prompt = f"""Think step-by-step and provide detailed reasoning:

Question: {question}

Provide:
1. Analysis
2. Step-by-step reasoning
3. Conclusion"""
        
        return self.get_response(
            question=reasoning_prompt,
            model=model,
            temperature=0.4,
            max_tokens=6000
        )
    
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
        """Clear conversation history"""
        if user_id in self.conversations:
            del self.conversations[user_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return {
            'backend': 'perplexity',
            'available': self.is_available(),
            'models': list(self.models.keys()),
            'default_model': self.default_model,
            'active_conversations': len(self.conversations),
            'api_key_configured': bool(self.api_key)
        }


# Standalone testing
if __name__ == "__main__":
    # Test with environment variable
    backend = PerplexityBackend()
    
    print("\n=== Testing Perplexity Backend ===")
    print(f"Available: {backend.is_available()}")
    print(f"Stats: {json.dumps(backend.get_stats(), indent=2)}")
    
    if backend.is_available():
        # Test query
        print("\n=== Test Query ===")
        result = backend.get_response(
            question="What are the latest AI developments in 2026?",
            user_id="test_user"
        )
        
        if result['success']:
            print(f"✅ Response: {result['response'][:200]}...")
            print(f"Model: {result['model']}")
            print(f"Latency: {result['latency']}s")
            if result.get('citations'):
                print(f"Citations: {len(result['citations'])}")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("⚠️ Set PERPLEXITY_API_KEY environment variable to test")

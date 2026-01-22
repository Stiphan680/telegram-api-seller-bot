"""
Perplexity API Backend
Separate module for Perplexity integration - Easy to enable/disable
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any

class PerplexityBackend:
    def __init__(self, api_key: str = None):
        """
        Initialize Perplexity API
        
        Args:
            api_key: Perplexity API key (default from env PERPLEXITY_API_KEY)
        """
        # Load from environment if not provided
        self.api_key = api_key or os.environ.get('PERPLEXITY_API_KEY') or os.getenv('PERPLEXITY_API_KEY')
        
        # Clean the key (remove spaces/newlines)
        if self.api_key:
            self.api_key = self.api_key.strip()
        
        self.api_url = 'https://api.perplexity.ai/chat/completions'
        
        # Available models
        self.models = {
            'sonar': 'llama-3.1-sonar-small-128k-online',  # Fast, online search
            'sonar-pro': 'llama-3.1-sonar-large-128k-online',  # Better quality
            'sonar-huge': 'llama-3.1-sonar-huge-128k-online',  # Best quality
            'chat': 'llama-3.1-8b-instruct',  # Fast chat without search
            'chat-large': 'llama-3.1-70b-instruct'  # Better chat without search
        }
        
        # Conversation memory
        self.conversations = {}
        self.max_history = 10
        
        # System prompts
        self.system_prompts = {
            'default': "You are a helpful AI assistant powered by Perplexity. Be accurate, concise, and cite sources when available.",
            'search': "You are a search assistant. Provide accurate information with sources and links.",
            'creative': "You are a creative AI assistant. Be imaginative and engaging.",
            'professional': "You are a professional AI assistant. Provide formal, well-structured responses.",
            'code': "You are a coding assistant. Provide clean code with explanations."
        }
        
        # Debug log
        if self.api_key:
            print(f"✅ Perplexity API key loaded: {self.api_key[:10]}...{self.api_key[-4:]}")
            print(f"✅ Key length: {len(self.api_key)} chars")
            print(f"✅ Key starts with 'pplx-': {self.api_key.startswith('pplx-')}")
        else:
            print("❌ Perplexity API key not found in environment")
    
    def is_available(self) -> bool:
        """Check if Perplexity API is configured and available"""
        if not self.api_key:
            print("❌ Perplexity: No API key")
            return False
        
        if not self.api_key.startswith('pplx-'):
            print(f"❌ Perplexity: Invalid key format (must start with 'pplx-')")
            print(f"   Current key starts with: {self.api_key[:10]}...")
            return False
        
        if len(self.api_key) < 30:
            print(f"❌ Perplexity: Key too short ({len(self.api_key)} chars, need 30+)")
            return False
        
        print("✅ Perplexity: API key valid and available")
        return True
    
    async def get_response(
        self,
        question: str,
        user_id: str = None,
        model: str = 'sonar',  # Default: Fast online search
        temperature: float = 0.7,
        max_tokens: int = 2048,
        include_context: bool = False,
        search_online: bool = True,
        tone: str = 'default'
    ) -> Dict[str, Any]:
        """
        Get response from Perplexity API
        
        Args:
            question: User's question
            user_id: For conversation context
            model: Model to use (sonar/sonar-pro/chat)
            temperature: 0.0-1.0 (creativity)
            max_tokens: Max response length
            include_context: Include conversation history
            search_online: Use online search (sonar models)
            tone: Response tone
        
        Returns:
            Dict with response and metadata
        """
        
        if not self.is_available():
            return {
                'success': False,
                'error': 'Perplexity API not configured',
                'fallback_needed': True
            }
        
        try:
            start_time = time.time()
            
            # Build messages
            messages = self._build_messages(
                question, user_id, include_context, tone
            )
            
            # Select model
            model_name = self.models.get(model, self.models['sonar'])
            
            # If online search not needed, use chat models
            if not search_online:
                model_name = self.models['chat']
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model_name,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': 0.9,
                'return_citations': search_online,  # Get sources
                'search_recency_filter': 'month',  # Recent results
                'stream': False
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f'API error: {response.status_code}'
                try:
                    error_detail = response.json()
                    error_msg = f'{error_msg} - {error_detail}'
                except:
                    pass
                
                print(f"❌ Perplexity API error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'fallback_needed': True
                }
            
            result = response.json()
            
            # Extract response
            assistant_message = result['choices'][0]['message']['content']
            
            # Extract citations if available
            citations = []
            if 'citations' in result:
                citations = result['citations']
            
            # Calculate latency
            latency = time.time() - start_time
            
            # Save to conversation history
            if include_context and user_id:
                self._update_conversation(user_id, question, assistant_message)
            
            print(f"✅ Perplexity response: {len(assistant_message)} chars, {latency:.2f}s")
            
            return {
                'success': True,
                'response': assistant_message,
                'citations': citations,
                'model': model_name,
                'latency': round(latency, 2),
                'tokens_used': result.get('usage', {}).get('total_tokens', 0),
                'online_search': search_online,
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.Timeout:
            print("❌ Perplexity: Request timeout")
            return {
                'success': False,
                'error': 'Request timeout',
                'fallback_needed': True
            }
        except Exception as e:
            print(f"❌ Perplexity error: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_needed': True
            }
    
    def _build_messages(
        self,
        question: str,
        user_id: str,
        include_context: bool,
        tone: str
    ) -> List[Dict[str, str]]:
        """Build message array for API"""
        
        messages = []
        
        # Add system prompt
        system_prompt = self.system_prompts.get(tone, self.system_prompts['default'])
        messages.append({
            'role': 'system',
            'content': system_prompt
        })
        
        # Add conversation history if enabled
        if include_context and user_id:
            history = self.conversations.get(user_id, [])
            for msg in history[-6:]:  # Last 3 exchanges
                messages.append({'role': 'user', 'content': msg['user']})
                messages.append({'role': 'assistant', 'content': msg['assistant']})
        
        # Add current question
        messages.append({
            'role': 'user',
            'content': question
        })
        
        return messages
    
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
    
    async def search(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Quick search with Perplexity"""
        
        search_prompt = f"Search and summarize: {query}\n\nProvide concise summary with key points and sources."
        
        return await self.get_response(
            question=search_prompt,
            model='sonar',
            search_online=True,
            temperature=0.3
        )
    
    async def analyze_with_sources(
        self,
        topic: str,
        depth: str = 'medium'
    ) -> Dict[str, Any]:
        """Detailed analysis with citations"""
        
        depth_map = {
            'quick': 'Brief summary in 2-3 sentences',
            'medium': 'Detailed analysis in 5-7 points',
            'deep': 'Comprehensive analysis with all aspects'
        }
        
        prompt = f"{depth_map.get(depth, depth_map['medium'])}\n\nTopic: {topic}\n\nInclude sources and citations."
        
        return await self.get_response(
            question=prompt,
            model='sonar-pro',
            search_online=True,
            temperature=0.2
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return {
            'backend': 'Perplexity',
            'api_configured': self.is_available(),
            'active_conversations': len(self.conversations),
            'available_models': list(self.models.keys()),
            'features': [
                'Online Search',
                'Citations',
                'Multi-model',
                'Conversation Context',
                'Recent Data (2024+)'
            ]
        }


# Singleton instance
_perplexity_backend = None

def get_perplexity_backend(api_key: str = None) -> PerplexityBackend:
    """Get or create Perplexity backend instance"""
    global _perplexity_backend
    
    if _perplexity_backend is None:
        _perplexity_backend = PerplexityBackend(api_key)
    
    return _perplexity_backend


# Quick test function
async def test_perplexity():
    """Test Perplexity API"""
    backend = get_perplexity_backend()
    
    print("\n🔍 Testing Perplexity Backend...\n")
    
    if not backend.is_available():
        print("❌ Perplexity API not configured or invalid")
        return
    
    print("✅ Perplexity API configured")
    print(f"📊 Stats: {backend.get_stats()}")
    
    # Test query
    print("\n📝 Testing query...")
    result = await backend.get_response(
        "What's the latest news about AI?",
        model='sonar',
        search_online=True
    )
    
    if result['success']:
        print(f"\n✅ Response: {result['response'][:200]}...")
        print(f"⏱️ Latency: {result['latency']}s")
        if result.get('citations'):
            print(f"📚 Citations: {len(result['citations'])} sources")
    else:
        print(f"❌ Error: {result['error']}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_perplexity())

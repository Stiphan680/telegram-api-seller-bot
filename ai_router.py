"""
AI Router - Intelligent Backend Selection
Automatically selects best available AI backend with fallback support
"""

import os
from typing import Dict, Any, Optional
from config import Config

class AIRouter:
    def __init__(self):
        """Initialize AI Router with all available backends"""
        
        self.backends = {}
        self.primary_backend = None
        self.fallback_order = []
        
        # Try to initialize Perplexity (if configured)
        if Config.is_perplexity_enabled():
            try:
                from perplexity_backend import PerplexityBackend
                self.backends['perplexity'] = PerplexityBackend(Config.PERPLEXITY_API_KEY)
                print("✅ Perplexity backend loaded")
            except Exception as e:
                print(f"⚠️ Could not load Perplexity backend: {e}")
        
        # Always load free backends as fallback
        try:
            # Import your existing AI backend (Gemini + Groq)
            # Assuming you have it in advanced_ai_backend.py
            from advanced_ai_backend import AdvancedAIBackend
            self.backends['gemini'] = AdvancedAIBackend()
            print("✅ Gemini/Groq backend loaded")
        except Exception as e:
            print(f"⚠️ Could not load Gemini backend: {e}")
        
        # Set primary backend based on config
        self._configure_backend_priority()
        
        print(f"\n🤖 AI Router initialized")
        print(f"Available backends: {list(self.backends.keys())}")
        print(f"Primary backend: {self.primary_backend}")
        print(f"Fallback order: {self.fallback_order}\n")
    
    def _configure_backend_priority(self):
        """Configure backend selection priority"""
        
        ai_backend_pref = Config.AI_BACKEND.lower()
        
        if ai_backend_pref == 'auto':
            # Auto mode: Prefer Perplexity, fallback to Gemini
            if 'perplexity' in self.backends:
                self.primary_backend = 'perplexity'
                self.fallback_order = ['gemini'] if 'gemini' in self.backends else []
            elif 'gemini' in self.backends:
                self.primary_backend = 'gemini'
                self.fallback_order = []
        
        elif ai_backend_pref == 'perplexity':
            # Force Perplexity (no fallback)
            if 'perplexity' in self.backends:
                self.primary_backend = 'perplexity'
                self.fallback_order = ['gemini'] if 'gemini' in self.backends else []
            else:
                print("⚠️ Perplexity requested but not available, using Gemini")
                self.primary_backend = 'gemini' if 'gemini' in self.backends else None
                self.fallback_order = []
        
        elif ai_backend_pref in ['gemini', 'groq']:
            # Force free backend
            if 'gemini' in self.backends:
                self.primary_backend = 'gemini'
                self.fallback_order = []
        
        else:
            # Default to first available
            if 'perplexity' in self.backends:
                self.primary_backend = 'perplexity'
                self.fallback_order = ['gemini'] if 'gemini' in self.backends else []
            elif 'gemini' in self.backends:
                self.primary_backend = 'gemini'
                self.fallback_order = []
    
    async def get_response(self, 
                          question: str,
                          user_id: str = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Get AI response with automatic backend selection and fallback
        
        Args:
            question: User question
            user_id: User ID
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Response dict with backend info
        """
        
        # Try primary backend first
        if self.primary_backend and self.primary_backend in self.backends:
            result = await self._try_backend(self.primary_backend, question, user_id, **kwargs)
            
            if result['success']:
                return result
            
            # Check if fallback is needed
            if not result.get('fallback', False):
                return result  # Hard error, don't fallback
        
        # Try fallback backends
        for backend_name in self.fallback_order:
            if backend_name in self.backends:
                print(f"♻️ Falling back to {backend_name}")
                result = await self._try_backend(backend_name, question, user_id, **kwargs)
                
                if result['success']:
                    return result
        
        # All backends failed
        return {
            'success': False,
            'error': 'All AI backends unavailable',
            'response': 'Sorry, AI service is temporarily unavailable. Please try again later.',
            'backend': 'none'
        }
    
    async def _try_backend(self, backend_name: str, question: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Try to get response from specific backend"""
        
        try:
            backend = self.backends[backend_name]
            
            # Call backend's get_response method
            if backend_name == 'perplexity':
                # Perplexity backend (sync)
                result = backend.get_response(
                    question=question,
                    user_id=user_id,
                    **kwargs
                )
            else:
                # Advanced AI backend (async)
                result = await backend.get_response(
                    question=question,
                    user_id=user_id,
                    **kwargs
                )
            
            # Add backend info if not present
            if 'backend' not in result:
                result['backend'] = backend_name
            
            return result
            
        except Exception as e:
            print(f"❌ Error with {backend_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': True,
                'backend': backend_name
            }
    
    def get_backend_stats(self) -> Dict[str, Any]:
        """Get statistics about available backends"""
        
        stats = {
            'primary_backend': self.primary_backend,
            'fallback_backends': self.fallback_order,
            'available_backends': list(self.backends.keys()),
            'perplexity_enabled': 'perplexity' in self.backends,
            'total_backends': len(self.backends)
        }
        
        # Get individual backend stats
        for name, backend in self.backends.items():
            if hasattr(backend, 'get_stats'):
                stats[f'{name}_stats'] = backend.get_stats()
        
        return stats
    
    def switch_backend(self, backend_name: str) -> bool:
        """
        Manually switch primary backend
        
        Args:
            backend_name: 'perplexity' or 'gemini'
        
        Returns:
            True if switched, False if not available
        """
        
        if backend_name in self.backends:
            self.primary_backend = backend_name
            print(f"✅ Switched to {backend_name} backend")
            return True
        else:
            print(f"❌ {backend_name} backend not available")
            return False
    
    def is_perplexity_active(self) -> bool:
        """Check if Perplexity is currently active"""
        return self.primary_backend == 'perplexity'


# Global AI Router instance (singleton)
_ai_router_instance = None

def get_ai_router() -> AIRouter:
    """Get global AI Router instance"""
    global _ai_router_instance
    
    if _ai_router_instance is None:
        _ai_router_instance = AIRouter()
    
    return _ai_router_instance


# Testing
if __name__ == "__main__":
    import asyncio
    
    async def test_router():
        router = get_ai_router()
        
        print("\n=== Backend Stats ===")
        print(router.get_backend_stats())
        
        print("\n=== Test Query ===")
        result = await router.get_response(
            question="What is the capital of India?",
            user_id="test_user"
        )
        
        print(f"\nBackend used: {result.get('backend')}")
        print(f"Success: {result.get('success')}")
        print(f"Response: {result.get('response', result.get('error'))[:200]}...")
    
    asyncio.run(test_router())

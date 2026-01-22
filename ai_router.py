"""
AI Router - Smart Backend Selection
Automatically routes to best available AI backend with fallback
"""

import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import all available backends
try:
    from perplexity_backend import get_perplexity_backend
    PERPLEXITY_AVAILABLE = True
except ImportError:
    PERPLEXITY_AVAILABLE = False

try:
    from advanced_ai_backend import AdvancedAIBackend
    ADVANCED_AI_AVAILABLE = True
except ImportError:
    ADVANCED_AI_AVAILABLE = False


class AIRouter:
    """
    Smart AI Router
    - Priority 1: Perplexity (if configured)
    - Priority 2: Advanced AI (Gemini + Groq)
    - Auto fallback on errors
    """
    
    def __init__(self):
        """Initialize all available backends"""
        self.backends = {}
        self.backend_priority = []
        
        # Initialize Perplexity
        if PERPLEXITY_AVAILABLE:
            try:
                perplexity = get_perplexity_backend()
                if perplexity.is_available():
                    self.backends['perplexity'] = perplexity
                    self.backend_priority.append('perplexity')
                    print("✅ Perplexity backend initialized")
            except Exception as e:
                print(f"⚠️ Perplexity init failed: {e}")
        
        # Initialize Advanced AI
        if ADVANCED_AI_AVAILABLE:
            try:
                self.backends['advanced_ai'] = AdvancedAIBackend()
                self.backend_priority.append('advanced_ai')
                print("✅ Advanced AI backend initialized")
            except Exception as e:
                print(f"⚠️ Advanced AI init failed: {e}")
        
        # Set default backend
        self.default_backend = self.backend_priority[0] if self.backend_priority else None
        
        if not self.default_backend:
            print("❌ No AI backends available!")
    
    def is_available(self) -> bool:
        """Check if any backend is available"""
        return bool(self.backends)
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get status of all backends"""
        return {
            'available_backends': list(self.backends.keys()),
            'priority_order': self.backend_priority,
            'default': self.default_backend,
            'perplexity_enabled': 'perplexity' in self.backends,
            'advanced_ai_enabled': 'advanced_ai' in self.backends
        }
    
    async def get_response(
        self,
        question: str,
        user_id: str = None,
        language: str = 'english',
        tone: str = 'default',
        prefer_backend: str = None,
        search_online: bool = False,
        include_context: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get AI response with automatic backend selection and fallback
        
        Args:
            question: User question
            user_id: For conversation context
            language: Response language
            tone: Response tone
            prefer_backend: Preferred backend ('perplexity' or 'advanced_ai')
            search_online: Use online search (Perplexity feature)
            include_context: Include conversation history
            **kwargs: Additional backend-specific parameters
        
        Returns:
            Dict with response and metadata
        """
        
        if not self.is_available():
            return {
                'success': False,
                'error': 'No AI backends available',
                'response': 'AI service is currently unavailable. Please try again later.'
            }
        
        # Determine backend order
        if prefer_backend and prefer_backend in self.backends:
            # Try preferred backend first
            backend_order = [prefer_backend] + [b for b in self.backend_priority if b != prefer_backend]
        else:
            # Use default priority
            backend_order = self.backend_priority.copy()
        
        # If online search requested, prioritize Perplexity
        if search_online and 'perplexity' in self.backends:
            backend_order = ['perplexity'] + [b for b in backend_order if b != 'perplexity']
        
        # Try each backend in order
        for backend_name in backend_order:
            try:
                result = await self._try_backend(
                    backend_name,
                    question,
                    user_id,
                    language,
                    tone,
                    search_online,
                    include_context,
                    **kwargs
                )
                
                if result['success']:
                    result['backend_used'] = backend_name
                    return result
                
                # If backend returned fallback_needed, try next
                if result.get('fallback_needed'):
                    print(f"⚠️ {backend_name} failed, trying fallback...")
                    continue
                
            except Exception as e:
                print(f"❌ Error with {backend_name}: {e}")
                continue
        
        # All backends failed
        return {
            'success': False,
            'error': 'All AI backends failed',
            'response': 'I apologize, but I\'m unable to process your request right now. Please try again in a moment.',
            'backends_tried': backend_order
        }
    
    async def _try_backend(
        self,
        backend_name: str,
        question: str,
        user_id: str,
        language: str,
        tone: str,
        search_online: bool,
        include_context: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Try specific backend"""
        
        backend = self.backends[backend_name]
        
        if backend_name == 'perplexity':
            # Perplexity API call
            return await backend.get_response(
                question=question,
                user_id=user_id,
                model=kwargs.get('model', 'sonar'),
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2048),
                include_context=include_context,
                search_online=search_online,
                tone=tone
            )
        
        elif backend_name == 'advanced_ai':
            # Advanced AI (Gemini/Groq) call
            return await backend.get_response(
                question=question,
                user_id=user_id,
                language=language,
                tone=tone,
                include_context=include_context,
                max_tokens=kwargs.get('max_tokens', 4096),
                temperature=kwargs.get('temperature', 0.7),
                stream=False
            )
        
        return {'success': False, 'error': f'Unknown backend: {backend_name}'}
    
    async def search(self, query: str) -> Dict[str, Any]:
        """Quick search - uses Perplexity if available, else Advanced AI"""
        
        if 'perplexity' in self.backends:
            return await self.backends['perplexity'].search(query)
        elif 'advanced_ai' in self.backends:
            return await self.backends['advanced_ai'].get_response(
                question=f"Search and provide information about: {query}",
                temperature=0.3
            )
        
        return {'success': False, 'error': 'No search backend available'}
    
    def enable_backend(self, backend_name: str) -> bool:
        """Enable specific backend"""
        if backend_name == 'perplexity' and PERPLEXITY_AVAILABLE:
            try:
                perplexity = get_perplexity_backend()
                if perplexity.is_available():
                    self.backends['perplexity'] = perplexity
                    if 'perplexity' not in self.backend_priority:
                        self.backend_priority.insert(0, 'perplexity')
                    return True
            except:
                pass
        return False
    
    def disable_backend(self, backend_name: str) -> bool:
        """Disable specific backend"""
        if backend_name in self.backends:
            del self.backends[backend_name]
            if backend_name in self.backend_priority:
                self.backend_priority.remove(backend_name)
            return True
        return False
    
    def set_default_backend(self, backend_name: str) -> bool:
        """Set default backend"""
        if backend_name in self.backends:
            self.default_backend = backend_name
            # Move to front of priority
            self.backend_priority = [backend_name] + [
                b for b in self.backend_priority if b != backend_name
            ]
            return True
        return False


# Singleton instance
_ai_router = None

def get_ai_router() -> AIRouter:
    """Get or create AI router instance"""
    global _ai_router
    
    if _ai_router is None:
        _ai_router = AIRouter()
    
    return _ai_router


# Test function
async def test_router():
    """Test AI router"""
    router = get_ai_router()
    
    print("\n🤖 AI Router Status:")
    print(router.get_backend_status())
    
    if not router.is_available():
        print("\n❌ No backends available")
        return
    
    # Test 1: Normal query
    print("\n📝 Test 1: Normal Query")
    result = await router.get_response(
        "What is Python?",
        user_id="test_user",
        language="english"
    )
    print(f"Backend: {result.get('backend_used')}")
    print(f"Response: {result['response'][:100]}...")
    
    # Test 2: Search query (Perplexity preferred)
    print("\n🔍 Test 2: Search Query")
    result = await router.get_response(
        "Latest AI news",
        search_online=True
    )
    print(f"Backend: {result.get('backend_used')}")
    if result.get('citations'):
        print(f"Citations: {len(result['citations'])} sources")
    
    print("\n✅ Tests completed")


if __name__ == '__main__':
    asyncio.run(test_router())

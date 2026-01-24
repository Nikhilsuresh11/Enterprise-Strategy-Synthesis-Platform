"""LLM service with Groq (primary) and OpenRouter (fallback) support."""

import asyncio
from typing import Optional, Dict, Any
from groq import AsyncGroq
from openai import AsyncOpenAI
from app.services.cache_service import CacheService
from app.services.rate_limiter import MultiProviderRateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    LLM service with smart model selection, caching, and rate limiting.
    
    Features:
    - Primary: Groq (free tier: 14K RPM, 7K RPD)
    - Fallback: OpenRouter (free models)
    - Aggressive caching to minimize API calls
    - Smart model selection based on task complexity
    - Rate limiting to prevent 429 errors
    """
    
    def __init__(
        self,
        groq_key: str,
        openrouter_key: Optional[str],
        cache: CacheService,
        default_model: str = "llama-3.3-70b-versatile",
        fast_model: str = "llama-3.1-8b-instant",
        fallback_model: str = "tngtech/deepseek-r1t2-chimera:free",
        rate_limiter: Optional[MultiProviderRateLimiter] = None
    ):
        self.groq = AsyncGroq(api_key=groq_key)
        self.openrouter = None
        if openrouter_key:
            self.openrouter = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key
            )
        
        self.cache = cache
        self.default_model = default_model
        self.fast_model = fast_model
        self.fallback_model = fallback_model
        
        # Initialize rate limiter
        self.rate_limiter = rate_limiter or MultiProviderRateLimiter()
        
        # Token usage tracking
        self.total_tokens = 0
        self.request_count = 0
        
        logger.info("llm_service_initialized", default_model=default_model)
    
    def select_model(
        self,
        task_type: str = "general",
        model: Optional[str] = None
    ) -> str:
        """
        Smart model selection based on task type.
        
        Args:
            task_type: Type of task (extraction, reasoning, synthesis, formatting)
            model: Override model selection
        
        Returns:
            Model name to use
        """
        if model:
            return model
        
        # Use fast model for simple tasks
        if task_type in ["extraction", "formatting", "simple"]:
            return self.fast_model
        
        # Use quality model for complex tasks
        elif task_type in ["reasoning", "synthesis", "analysis"]:
            return self.default_model
        
        # Default
        return self.default_model
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        task_type: str = "general",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: str = "text"
    ) -> str:
        """
        Generate LLM response with caching and fallback.
        
        Args:
            prompt: Input prompt
            model: Model to use (auto-selected if None)
            task_type: Task type for model selection
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: "text" or "json"
        
        Returns:
            Generated text response
        """
        # Select model
        selected_model = self.select_model(task_type, model)
        
        # Check cache first
        cached = await self.cache.get_llm_response(prompt, selected_model)
        if cached:
            logger.info(
                "llm_cache_hit",
                model=selected_model,
                prompt_length=len(prompt)
            )
            return cached
        
        # Generate response
        try:
            # Acquire rate limit permission before calling Groq
            await self.rate_limiter.acquire("groq")
            
            response = await self._call_groq(
                prompt=prompt,
                model=selected_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Cache response
            await self.cache.cache_llm_response(prompt, selected_model, response)
            
            # Track usage
            self.request_count += 1
            
            logger.info(
                "llm_generation_success",
                model=selected_model,
                prompt_length=len(prompt),
                response_length=len(response),
                request_count=self.request_count
            )
            
            return response
            
        except Exception as e:
            logger.warning(
                "groq_failed_attempting_fallback",
                error=str(e),
                model=selected_model
            )
            
            # Fallback to OpenRouter
            if self.openrouter:
                try:
                    # Acquire rate limit permission for OpenRouter
                    await self.rate_limiter.acquire("openrouter")
                    
                    response = await self._call_openrouter(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Cache fallback response
                    await self.cache.cache_llm_response(
                        prompt,
                        "openrouter_fallback",
                        response
                    )
                    
                    logger.info("openrouter_fallback_success")
                    return response
                    
                except Exception as fallback_error:
                    logger.error(
                        "all_llm_providers_failed",
                        groq_error=str(e),
                        openrouter_error=str(fallback_error)
                    )
                    raise
            else:
                logger.error("groq_failed_no_fallback", error=str(e))
                raise
    
    async def _call_groq(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call Groq API."""
        response = await self.groq.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def _call_openrouter(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call OpenRouter API with free model."""
        response = await self.openrouter.chat.completions.create(
            model=self.fallback_model,  # Use configured fallback model
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics including rate limiter stats."""
        return {
            "total_requests": self.request_count,
            "total_tokens": self.total_tokens,
            "rate_limits": self.rate_limiter.get_all_stats()
        }

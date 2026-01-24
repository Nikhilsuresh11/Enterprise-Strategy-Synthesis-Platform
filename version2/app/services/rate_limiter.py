"""Rate limiter service to prevent API rate limit errors."""

import asyncio
import time
from typing import Dict, Optional
from collections import deque
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Prevents 429 errors by enforcing rate limits:
    - Groq: 14,400 requests/minute (240 req/sec)
    - OpenRouter: Varies by model, conservative default
    """
    
    def __init__(
        self,
        requests_per_minute: int = 240,  # Conservative: 240/min instead of 14,400
        requests_per_day: Optional[int] = None
    ):
        self.rpm_limit = requests_per_minute
        self.rpd_limit = requests_per_day
        
        # Sliding window for RPM tracking
        self.minute_window = deque()
        
        # Daily counter
        self.daily_count = 0
        self.daily_reset_time = time.time() + 86400  # 24 hours
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        logger.info(
            "rate_limiter_initialized",
            rpm_limit=requests_per_minute,
            rpd_limit=requests_per_day
        )
    
    async def acquire(self, provider: str = "groq") -> bool:
        """
        Acquire permission to make an API call.
        
        Blocks until rate limit allows the request.
        
        Args:
            provider: API provider name (for logging)
        
        Returns:
            True when request is allowed
        """
        async with self.lock:
            current_time = time.time()
            
            # Reset daily counter if needed
            if current_time >= self.daily_reset_time:
                self.daily_count = 0
                self.daily_reset_time = current_time + 86400
                logger.info("daily_rate_limit_reset")
            
            # Check daily limit
            if self.rpd_limit and self.daily_count >= self.rpd_limit:
                logger.error(
                    "daily_rate_limit_exceeded",
                    provider=provider,
                    count=self.daily_count,
                    limit=self.rpd_limit
                )
                raise Exception(f"Daily rate limit exceeded for {provider}")
            
            # Remove requests older than 1 minute
            cutoff_time = current_time - 60
            while self.minute_window and self.minute_window[0] < cutoff_time:
                self.minute_window.popleft()
            
            # Check if we need to wait
            if len(self.minute_window) >= self.rpm_limit:
                # Calculate wait time
                oldest_request = self.minute_window[0]
                wait_time = 60 - (current_time - oldest_request) + 0.1  # Add buffer
                
                if wait_time > 0:
                    logger.warning(
                        "rate_limit_throttling",
                        provider=provider,
                        wait_seconds=wait_time,
                        current_rpm=len(self.minute_window)
                    )
                    await asyncio.sleep(wait_time)
                    
                    # Recalculate after waiting
                    current_time = time.time()
                    cutoff_time = current_time - 60
                    while self.minute_window and self.minute_window[0] < cutoff_time:
                        self.minute_window.popleft()
            
            # Add current request
            self.minute_window.append(current_time)
            self.daily_count += 1
            
            logger.debug(
                "rate_limit_acquired",
                provider=provider,
                current_rpm=len(self.minute_window),
                daily_count=self.daily_count
            )
            
            return True
    
    def get_stats(self) -> Dict[str, int]:
        """Get current rate limiter statistics."""
        return {
            "requests_last_minute": len(self.minute_window),
            "requests_today": self.daily_count,
            "rpm_limit": self.rpm_limit,
            "rpd_limit": self.rpd_limit or 0
        }


class MultiProviderRateLimiter:
    """
    Manages rate limiters for multiple API providers.
    
    Each provider has its own rate limiter with appropriate limits.
    """
    
    def __init__(self):
        # Groq limits: 14,400 RPM, 7,000 RPD
        # Use conservative limits to avoid hitting edges
        self.limiters = {
            "groq": RateLimiter(
                requests_per_minute=200,  # Conservative: ~12K/hour
                requests_per_day=6500     # Leave buffer
            ),
            "openrouter": RateLimiter(
                requests_per_minute=60,   # Conservative for free tier
                requests_per_day=None     # No daily limit
            )
        }
        
        logger.info("multi_provider_rate_limiter_initialized")
    
    async def acquire(self, provider: str) -> bool:
        """
        Acquire permission for specific provider.
        
        Args:
            provider: Provider name (groq, openrouter)
        
        Returns:
            True when request is allowed
        """
        if provider not in self.limiters:
            logger.warning(f"unknown_provider_{provider}_no_rate_limiting")
            return True
        
        return await self.limiters[provider].acquire(provider)
    
    def get_stats(self, provider: str) -> Dict[str, int]:
        """Get stats for specific provider."""
        if provider in self.limiters:
            return self.limiters[provider].get_stats()
        return {}
    
    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """Get stats for all providers."""
        return {
            provider: limiter.get_stats()
            for provider, limiter in self.limiters.items()
        }

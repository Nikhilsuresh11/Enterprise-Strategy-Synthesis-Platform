"""Rate limiter for LLM API calls to respect free tier limits."""

import asyncio
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter to prevent exceeding API rate limits.
    
    Tracks calls in a sliding window and enforces delays when necessary.
    """
    
    def __init__(
        self,
        calls_per_minute: int = 10,
        tokens_per_minute: int = 14400,  # Groq free tier TPM limit
        min_delay_seconds: float = 5.0   # Increased from 3.0 for safety
    ):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum calls allowed per minute (RPM)
            tokens_per_minute: Maximum tokens allowed per minute (TPM)
            min_delay_seconds: Minimum delay between calls
        """
        self.calls_per_minute = calls_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.min_delay_seconds = min_delay_seconds
        self.calls = deque()  # (timestamp, estimated_tokens)
        self.last_call_time: Optional[datetime] = None
        
        logger.info(
            "rate_limiter_initialized",
            calls_per_minute=calls_per_minute,
            tokens_per_minute=tokens_per_minute,
            min_delay=min_delay_seconds
        )
    
    def _estimate_tokens(self, prompt_length: int = 1000) -> int:
        """
        Estimate tokens for a request.
        
        Conservative estimate: ~1 token per 4 characters
        Default assumes 1000 char prompt = ~250 tokens
        Plus ~500 tokens for response = ~750 tokens total per call
        
        Args:
            prompt_length: Length of prompt in characters
            
        Returns:
            Estimated total tokens (prompt + response)
        """
        prompt_tokens = prompt_length // 4
        response_tokens = 500  # Conservative estimate for response
        return prompt_tokens + response_tokens
    
    async def acquire(self, estimated_prompt_length: int = 1000) -> None:
        """
        Acquire permission to make an API call.
        
        Waits if necessary to respect both RPM and TPM limits.
        
        Args:
            estimated_prompt_length: Estimated length of prompt in characters
        """
        now = datetime.now()
        estimated_tokens = self._estimate_tokens(estimated_prompt_length)
        
        # Enforce minimum delay between calls
        if self.last_call_time:
            time_since_last = (now - self.last_call_time).total_seconds()
            if time_since_last < self.min_delay_seconds:
                wait_time = self.min_delay_seconds - time_since_last
                logger.info(
                    "rate_limit_min_delay",
                    wait_seconds=round(wait_time, 2)
                )
                await asyncio.sleep(wait_time)
                now = datetime.now()
        
        # Remove calls older than 1 minute from sliding window
        cutoff_time = now - timedelta(minutes=1)
        while self.calls and self.calls[0][0] < cutoff_time:
            self.calls.popleft()
        
        # Calculate current usage
        current_calls = len(self.calls)
        current_tokens = sum(tokens for _, tokens in self.calls)
        
        # Check if at RPM limit
        if current_calls >= self.calls_per_minute:
            oldest_call_time = self.calls[0][0]
            wait_until = oldest_call_time + timedelta(minutes=1)
            sleep_time = (wait_until - now).total_seconds() + 0.5
            
            if sleep_time > 0:
                logger.warning(
                    "rate_limit_rpm_waiting",
                    wait_seconds=round(sleep_time, 2),
                    calls_in_window=current_calls,
                    rpm_limit=self.calls_per_minute
                )
                await asyncio.sleep(sleep_time)
                now = datetime.now()
                # Recalculate after waiting
                cutoff_time = now - timedelta(minutes=1)
                while self.calls and self.calls[0][0] < cutoff_time:
                    self.calls.popleft()
                current_tokens = sum(tokens for _, tokens in self.calls)
        
        # Check if adding this call would exceed TPM limit
        if current_tokens + estimated_tokens > self.tokens_per_minute:
            # Need to wait for tokens to expire
            oldest_call_time = self.calls[0][0]
            wait_until = oldest_call_time + timedelta(minutes=1)
            sleep_time = (wait_until - now).total_seconds() + 1.0  # +1s buffer
            
            if sleep_time > 0:
                logger.warning(
                    "rate_limit_tpm_waiting",
                    wait_seconds=round(sleep_time, 2),
                    current_tokens=current_tokens,
                    estimated_tokens=estimated_tokens,
                    tpm_limit=self.tokens_per_minute
                )
                await asyncio.sleep(sleep_time)
                now = datetime.now()
        
        # Record this call with token estimate
        self.calls.append((now, estimated_tokens))
        self.last_call_time = now
        
        logger.debug(
            "rate_limit_acquired",
            calls_in_last_minute=len(self.calls),
            tokens_in_last_minute=sum(t for _, t in self.calls),
            estimated_tokens=estimated_tokens
        )
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=1)
        
        # Clean old calls
        while self.calls and self.calls[0] < cutoff_time:
            self.calls.popleft()
        
        return {
            "calls_in_last_minute": len(self.calls),
            "calls_per_minute_limit": self.calls_per_minute,
            "min_delay_seconds": self.min_delay_seconds,
            "utilization_percent": (len(self.calls) / self.calls_per_minute) * 100
        }

"""Caching utilities for Stratagem AI - Enhanced with TTL support."""

from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import json
from cachetools import TTLCache
import time


# Global caches with TTL
llm_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour
rag_cache = TTLCache(maxsize=500, ttl=7200)   # 2 hours
research_cache = TTLCache(maxsize=100, ttl=86400)  # 24 hours


class CacheManager:
    """
    Enhanced in-memory cache manager with TTL support.
    """
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600) -> None:
        """Initialize cache manager with TTL."""
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        self._cache[key] = value
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
            "ttl": self._cache.ttl
        }


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = json.dumps({"args": str(args), "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def async_cache(cache: TTLCache):
    """Decorator for async function caching."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            if key in cache:
                return cache[key]
            
            result = await func(*args, **kwargs)
            cache[key] = result
            return result
        
        return wrapper
    return decorator


def get_all_cache_stats() -> dict:
    """Get statistics for all caches."""
    return {
        "llm_cache": {"size": len(llm_cache), "maxsize": llm_cache.maxsize},
        "rag_cache": {"size": len(rag_cache), "maxsize": rag_cache.maxsize},
        "research_cache": {"size": len(research_cache), "maxsize": research_cache.maxsize}
    }

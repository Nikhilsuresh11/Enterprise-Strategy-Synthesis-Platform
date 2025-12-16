"""Caching utilities for Stratagem AI."""

from typing import Any, Optional


class CacheManager:
    """
    Simple in-memory cache manager.
    
    This will be enhanced in future sprints with Redis support.
    """
    
    def __init__(self) -> None:
        """Initialize cache manager."""
        self._cache: dict[str, Any] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (not implemented yet)
        """
        self._cache[key] = value
    
    async def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

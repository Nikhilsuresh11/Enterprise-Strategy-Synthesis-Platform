"""Caching utilities for Stratagem AI - Enhanced with TTL support."""

import hashlib
import json
from cachetools import TTLCache


# Global caches with TTL
llm_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour
rag_cache = TTLCache(maxsize=500, ttl=7200)   # 2 hours
research_cache = TTLCache(maxsize=100, ttl=86400)  # 24 hours


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = json.dumps({"args": str(args), "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def get_all_cache_stats() -> dict:
    """Get statistics for all caches."""
    return {
        "llm_cache": {"size": len(llm_cache), "maxsize": llm_cache.maxsize},
        "rag_cache": {"size": len(rag_cache), "maxsize": rag_cache.maxsize},
        "research_cache": {"size": len(research_cache), "maxsize": research_cache.maxsize}
    }

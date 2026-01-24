"""MongoDB-based caching service for API responses and LLM outputs."""

import hashlib
import json
from typing import Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """MongoDB-based caching with TTL support."""
    
    def __init__(self, mongo_uri: str, database: str = "stratagem"):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[database]
        self.cache = self.db["cache"]
        
        logger.info("cache_service_initialized")
    
    async def initialize(self):
        """Create indexes for cache collection."""
        # TTL index for automatic expiration
        await self.cache.create_index("expires_at", expireAfterSeconds=0)
        # Index for faster lookups
        await self.cache.create_index("key")
        logger.info("cache_indexes_created")
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate deterministic cache key from data."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value by key."""
        try:
            doc = await self.cache.find_one({"key": key})
            if doc:
                logger.info("cache_hit", key=key)
                return doc["value"]
            logger.info("cache_miss", key=key)
            return None
        except Exception as e:
            logger.error("cache_get_failed", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Store value in cache with optional TTL (seconds)."""
        try:
            doc = {
                "key": key,
                "value": value,
                "created_at": datetime.utcnow()
            }
            
            if ttl:
                doc["expires_at"] = datetime.utcnow() + timedelta(seconds=ttl)
            
            await self.cache.replace_one(
                {"key": key},
                doc,
                upsert=True
            )
            logger.info("cache_set", key=key, ttl=ttl)
        except Exception as e:
            logger.error("cache_set_failed", key=key, error=str(e))
    
    async def cache_llm_response(
        self,
        prompt: str,
        model: str,
        response: str
    ):
        """Cache LLM response (no TTL - permanent cache)."""
        key = self._generate_key("llm", {"prompt": prompt, "model": model})
        await self.set(key, response, ttl=None)
    
    async def get_llm_response(
        self,
        prompt: str,
        model: str
    ) -> Optional[str]:
        """Retrieve cached LLM response."""
        key = self._generate_key("llm", {"prompt": prompt, "model": model})
        return await self.get(key)
    
    async def cache_api_response(
        self,
        api_name: str,
        params: dict,
        response: Any,
        ttl: int = 3600
    ):
        """Cache external API response with TTL."""
        key = self._generate_key(f"api:{api_name}", params)
        await self.set(key, response, ttl=ttl)
    
    async def get_api_response(
        self,
        api_name: str,
        params: dict
    ) -> Optional[Any]:
        """Retrieve cached API response."""
        key = self._generate_key(f"api:{api_name}", params)
        return await self.get(key)
    
    async def cache_rag_query(
        self,
        query: str,
        results: Any,
        ttl: int = 604800  # 7 days
    ):
        """Cache RAG query results."""
        key = self._generate_key("rag", {"query": query})
        await self.set(key, results, ttl=ttl)
    
    async def get_rag_query(self, query: str) -> Optional[Any]:
        """Retrieve cached RAG results."""
        key = self._generate_key("rag", {"query": query})
        return await self.get(key)
    
    async def close(self):
        """Close MongoDB connection."""
        self.client.close()
        logger.info("cache_service_closed")

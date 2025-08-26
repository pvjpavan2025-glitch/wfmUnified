"""Redis client for caching and state management."""

import json
from typing import Any, Optional
import redis.asyncio as redis
from .config import settings


class RedisClient:
    """Async Redis client wrapper."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if not self.redis:
            self.redis = redis.from_url(
                settings.redis_url,
                db=settings.redis_db,
                decode_responses=True,
                encoding="utf-8",
            )
            await self.redis.ping()
    
    async def ping(self) -> bool:
        """Ping Redis server."""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.redis:
            await self.connect()
        
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        if not self.redis:
            await self.connect()
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, (str, int, float, bool)) else value
            await self.redis.set(key, serialized_value, ex=expire)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.redis:
            await self.connect()
        
        try:
            return bool(await self.redis.exists(key))
        except Exception:
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        if not self.redis:
            await self.connect()
        
        try:
            return bool(await self.redis.expire(key, seconds))
        except Exception:
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value."""
        if not self.redis:
            await self.connect()
        
        value = await self.redis.hget(name, key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field value."""
        if not self.redis:
            await self.connect()
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, (str, int, float, bool)) else value
            await self.redis.hset(name, key, serialized_value)
            return True
        except Exception:
            return False
    
    async def hgetall(self, name: str) -> dict[str, Any]:
        """Get all hash fields."""
        if not self.redis:
            await self.connect()
        
        try:
            hash_data = await self.redis.hgetall(name)
            result = {}
            for key, value in hash_data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            return result
        except Exception:
            return {}


# Global Redis client instance
redis_client = RedisClient()

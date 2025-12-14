import logging
from typing import Optional, Any
import json
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client with fallback to in-memory cache."""
    
    def __init__(self, url: Optional[str] = None):
        self.url = url
        self._client = None
        self._in_memory_cache = {}
        self._connected = False
        
        if url and url.strip():
            self.connect()
    
    def connect(self):
        """Connect to Redis if available."""
        if not self.url or not self.url.strip():
            logger.warning("No Redis URL, using in-memory cache")
            return
        
        try:
            import redis
            self._client = redis.from_url(self.url, decode_responses=True)
            self._client.ping()
            self._connected = True
            logger.info("Redis connected")
        except ImportError:
            logger.warning("Redis package not installed, using in-memory")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory")
    
    def set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set cache with TTL."""
        if self._connected and self._client:
            try:
                serialized = json.dumps(value)
                self._client.setex(key, timedelta(seconds=ttl), serialized)
            except Exception as e:
                logger.error(f"Redis set failed: {e}")
                self._in_memory_cache[key] = value
        else:
            self._in_memory_cache[key] = value
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value."""
        if self._connected and self._client:
            try:
                value = self._client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
        
        return self._in_memory_cache.get(key)
    
    def is_connected(self) -> bool:
        return self._connected

# Global instance - empty URL means in-memory only
redis_client = RedisClient("")

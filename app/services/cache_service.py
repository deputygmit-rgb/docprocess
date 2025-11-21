import redis
import json
from typing import Any, Optional
from app.core.config import get_settings

settings = get_settings()


class CacheService:
    def __init__(self):
        self.enabled = False
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            self.redis_client.ping()
            self.enabled = True
            print("Redis connected successfully")
        except Exception as e:
            # Silently disable caching if Redis unavailable
            self.redis_client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str):
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str):
        if not self.enabled:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return False

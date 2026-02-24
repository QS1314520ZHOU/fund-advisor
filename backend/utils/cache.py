# backend/utils/cache.py
import json
import logging
import os
import time
from typing import Any, Optional
try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

class CacheManager:
    """
    统一缓存管理器：支持 Redis + 本地内存兜底
    """
    def __init__(self, redis_url: str = None, expire: int = 3600):
        self.redis_url = redis_url or os.environ.get("REDIS_URL")
        self.default_expire = expire
        self.client = None
        self.local_cache = {} # 内存兜底
        
        if self.redis_url:
            try:
                self.client = redis.from_url(self.redis_url, decode_responses=True)
                self.client.ping()
                logger.info(f"Redis 缓存连接成功: {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis 连接失败，切换至本地内存模式: {e}")
                self.client = None

    def get(self, key: str) -> Optional[Any]:
        if self.client:
            try:
                val = self.client.get(key)
                return json.loads(val) if val else None
            except Exception as e:
                logger.error(f"Redis GET 异常: {e}")
        
        # 本地内存模式
        if key in self.local_cache:
            entry = self.local_cache[key]
            if entry['expire'] > time.time():
                return entry['val']
            else:
                del self.local_cache[key]
        return None

    def set(self, key: str, value: Any, expire: int = None):
        exp = expire or self.default_expire
        if self.client:
            try:
                self.client.set(key, json.dumps(value, ensure_ascii=False), ex=exp)
                return
            except Exception as e:
                logger.error(f"Redis SET 异常: {e}")
        
        # 本地内存模式
        self.local_cache[key] = {
            'val': value,
            'expire': time.time() + exp
        }

    def delete(self, key: str):
        if self.client:
            try:
                self.client.delete(key)
            except Exception:
                pass
        if key in self.local_cache:
            del self.local_cache[key]

_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

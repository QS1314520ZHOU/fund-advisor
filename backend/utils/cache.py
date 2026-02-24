# backend/utils/cache.py
import json
import logging
import os
import time
from typing import Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

class CacheManager:
    """
    统一缓存管理器：本地内存模式 (带 LRU 淘汰)
    """
    def __init__(self, expire: int = 3600, max_items: int = 1000):
        self.default_expire = expire
        self.max_items = max_items
        self.local_cache = OrderedDict() # 内存缓存，使用 OrderedDict 实现 LRU
        
    def get(self, key: str) -> Optional[Any]:
        # 本地内存模式
        if key in self.local_cache:
            entry = self.local_cache[key]
            # 移动到末尾表示最近使用
            self.local_cache.move_to_end(key)
            
            if entry['expire'] > time.time():
                return entry['val']
            else:
                del self.local_cache[key]
        return None

    def set(self, key: str, value: Any, expire: int = None):
        exp = expire or self.default_expire
        
        # 淘汰最旧的项
        if key not in self.local_cache and len(self.local_cache) >= self.max_items:
            self.local_cache.popitem(last=False)
            
        self.local_cache[key] = {
            'val': value,
            'expire': time.time() + exp
        }
        self.local_cache.move_to_end(key)

    def delete(self, key: str):
        if key in self.local_cache:
            del self.local_cache[key]

_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

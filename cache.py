# cache.py
from functools import lru_cache
from typing import Dict, Any
import time

class Cache:
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            cache_data = self.cache[key]
            if time.time() - cache_data['timestamp'] < self.ttl:
                return cache_data['value']
            else:
                del self.cache[key]
        return None
    
    def delete(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        self.cache.clear()

# ایجاد نمونه از کلاس Cache
cache = Cache()

# دکوراتور برای کش کردن توابع
def cached(ttl: int = 3600):
    def decorator(func):
        @lru_cache(maxsize=128)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            result = cache.get(cache_key)
            
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

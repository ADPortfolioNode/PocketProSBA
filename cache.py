import redis
from config import Config
from utils.errors import CacheError, handle_errors

cache = redis.from_url(Config.REDIS_URL)

@handle_errors
def set_cache(key, value, ttl=3600):
    cache.setex(key, ttl, value)

@handle_errors
def get_cache(key):
    value = cache.get(key)
    if value:
        return value.decode('utf-8')
    return None

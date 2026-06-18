import redis
from .config.config import setting

redis_client = redis.from_url(setting.redis_url, decode_responses=True)
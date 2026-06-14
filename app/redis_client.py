"""import redis
import os 
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST","localhost"),
    port=6379,
    db=1,
    decode_responses=True
)
"""

import redis
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1") 
redis_client = redis.from_url(redis_url, decode_responses=True)
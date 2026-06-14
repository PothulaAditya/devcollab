import redis
import os 
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST","localhost"),
    port=6379,
    db=1,
    decode_responses=True
)
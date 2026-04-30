"""
app/core/redis_client.py
------------------------
Singleton Redis connection used across the application.

Reads REDIS_URL from environment (set in docker-compose).
Defaults to redis://localhost:6379/0 for local dev without Docker.
"""

import os
import redis

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """
    Return the module-level Redis client, creating it on first call.

    redis.Redis is thread-safe: a single instance is safe to share
    across FastAPI's async workers (which run in a thread pool).
    decode_responses=False because we store binary (base64 bytes).
    """
    global _redis_client
    if _redis_client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.Redis.from_url(url, decode_responses=False)
    return _redis_client
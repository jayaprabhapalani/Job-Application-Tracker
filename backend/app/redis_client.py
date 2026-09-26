import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None


async def init_redis():
    global _redis
    _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis():
    if _redis:
        await _redis.aclose()


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() on startup.")
    return _redis

import json
import logging
from typing import Optional, Any
from redis.asyncio import Redis
from backend.app.config import settings

logger = logging.getLogger("faultline.cache")

_redis_client: Optional[Redis] = None
_in_memory_key_cache: dict[str, dict[str, Any]] = {}

async def get_redis() -> Optional[Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.ping()
            _redis_client = client
            logger.info("Connected to Redis cache.")
        except Exception as e:
            if settings.USE_MEMORY_QUEUE_IF_NO_REDIS:
                logger.warning(f"Could not connect to Redis ({e}). Using in-memory cache/queue fallback.")
                _redis_client = None
            else:
                raise e
    return _redis_client

async def get_cached_project(api_key: str) -> Optional[dict[str, Any]]:
    """Retrieve project metadata from Redis cache or local in-memory cache."""
    # 1. Fast local in-memory cache check (sub-millisecond)
    if api_key in _in_memory_key_cache:
        return _in_memory_key_cache[api_key]

    # 2. Redis cache check
    redis = await get_redis()
    if redis:
        try:
            val = await redis.get(f"faultline:project_key:{api_key}")
            if val:
                data = json.loads(val)
                _in_memory_key_cache[api_key] = data
                return data
        except Exception as e:
            logger.error(f"Redis get error: {e}")

    return None

async def set_cached_project(api_key: str, project_data: dict[str, Any], ttl_seconds: int = 3600):
    """Store project metadata in cache."""
    _in_memory_key_cache[api_key] = project_data
    redis = await get_redis()
    if redis:
        try:
            await redis.set(
                f"faultline:project_key:{api_key}",
                json.dumps(project_data),
                ex=ttl_seconds
            )
        except Exception as e:
            logger.error(f"Redis set error: {e}")

async def invalidate_cached_project(api_key: str):
    """Invalidate project cache on update or deletion."""
    _in_memory_key_cache.pop(api_key, None)
    redis = await get_redis()
    if redis:
        try:
            await redis.delete(f"faultline:project_key:{api_key}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

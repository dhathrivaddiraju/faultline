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
        except Exception as exc:
            if settings.USE_MEMORY_QUEUE_IF_NO_REDIS:
                _redis_client = None
            else:
                raise exc
    return _redis_client


async def get_cached_project(api_key: str) -> Optional[dict[str, Any]]:
    if api_key in _in_memory_key_cache:
        return _in_memory_key_cache[api_key]

    redis = await get_redis()
    if redis:
        try:
            payload = await redis.get(f"faultline:project_key:{api_key}")
            if payload:
                record = json.loads(payload)
                _in_memory_key_cache[api_key] = record
                return record
        except Exception as exc:
            logger.warning(f"Failed to query Redis cache: {exc}")

    return None


async def set_cached_project(api_key: str, project_data: dict[str, Any], ttl_seconds: int = 3600) -> None:
    _in_memory_key_cache[api_key] = project_data
    redis = await get_redis()
    if redis:
        try:
            await redis.set(
                f"faultline:project_key:{api_key}",
                json.dumps(project_data),
                ex=ttl_seconds
            )
        except Exception as exc:
            logger.warning(f"Failed to set Redis cache: {exc}")


async def invalidate_cached_project(api_key: str) -> None:
    _in_memory_key_cache.pop(api_key, None)
    redis = await get_redis()
    if redis:
        try:
            await redis.delete(f"faultline:project_key:{api_key}")
        except Exception as exc:
            logger.warning(f"Failed to invalidate Redis cache: {exc}")

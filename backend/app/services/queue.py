import asyncio
import json
import logging
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.cache import get_redis

logger = logging.getLogger("faultline.queue")

_memory_queue: asyncio.Queue = asyncio.Queue(maxsize=100000)


async def enqueue_event(event_dict: dict[str, Any]) -> bool:
    redis = await get_redis()
    serialized = json.dumps(event_dict, default=str)

    if redis:
        try:
            await redis.lpush(settings.REDIS_QUEUE_KEY, serialized)
            return True
        except Exception as exc:
            logger.warning(f"Redis enqueue failed: {exc}. Using fallback queue.")

    try:
        _memory_queue.put_nowait(event_dict)
        return True
    except asyncio.QueueFull:
        logger.error("Event buffer exhausted. Dropping telemetry item.")
        return False


async def fetch_batch(batch_size: int = 50, timeout_seconds: float = 0.2) -> list[dict[str, Any]]:
    batch = []
    redis = await get_redis()

    if redis:
        try:
            pipeline = redis.pipeline()
            for _ in range(batch_size):
                pipeline.rpop(settings.REDIS_QUEUE_KEY)
            results = await pipeline.execute()

            for item in results:
                if item:
                    try:
                        batch.append(json.loads(item))
                    except Exception:
                        pass
            if batch:
                return batch
        except Exception as exc:
            logger.warning(f"Redis batch pop error: {exc}")

    try:
        if _memory_queue.empty():
            try:
                first = await asyncio.wait_for(_memory_queue.get(), timeout=timeout_seconds)
                batch.append(first)
                _memory_queue.task_done()
            except asyncio.TimeoutError:
                return []

        while len(batch) < batch_size and not _memory_queue.empty():
            item = _memory_queue.get_nowait()
            batch.append(item)
            _memory_queue.task_done()

    except Exception as exc:
        logger.warning(f"Buffer dequeue error: {exc}")

    return batch


async def get_queue_size() -> int:
    redis = await get_redis()
    if redis:
        try:
            return await redis.llen(settings.REDIS_QUEUE_KEY)
        except Exception:
            pass
    return _memory_queue.qsize()

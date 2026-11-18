import json
import asyncio
import logging
from typing import Any, Optional
from backend.app.config import settings
from backend.app.services.cache import get_redis

logger = logging.getLogger("faultline.queue")

# In-memory queue fallback if Redis is not running
_memory_queue: asyncio.Queue = asyncio.Queue(maxsize=100000)

async def enqueue_event(event_dict: dict[str, Any]) -> bool:
    """
    Push incoming raw error event payload to Redis List / Stream for sub-15ms response.
    Falls back to async in-memory queue if Redis is unavailable.
    """
    redis = await get_redis()
    serialized = json.dumps(event_dict, default=str)
    
    if redis:
        try:
            # LPUSH to Redis queue list for batch pop
            await redis.lpush(settings.REDIS_QUEUE_KEY, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis enqueue failed ({e}), falling back to memory queue")
            
    try:
        _memory_queue.put_nowait(event_dict)
        return True
    except asyncio.QueueFull:
        logger.error("In-memory event queue is full! Dropping event.")
        return False

async def fetch_batch(batch_size: int = 50, timeout_seconds: float = 0.2) -> list[dict[str, Any]]:
    """
    Fetch a batch of events from Redis or in-memory queue.
    """
    events = []
    redis = await get_redis()
    
    if redis:
        try:
            # Pipeline RPOP to fetch multiple items efficiently
            pipe = redis.pipeline()
            for _ in range(batch_size):
                pipe.rpop(settings.REDIS_QUEUE_KEY)
            results = await pipe.execute()
            
            for item in results:
                if item:
                    try:
                        events.append(json.loads(item))
                    except Exception as e:
                        logger.error(f"Failed to decode queued event: {e}")
            if events:
                return events
        except Exception as e:
            logger.error(f"Redis batch pop error: {e}")

    # Fallback to in-memory queue
    try:
        # First item with timeout
        if _memory_queue.empty():
            try:
                first = await asyncio.wait_for(_memory_queue.get(), timeout=timeout_seconds)
                events.append(first)
                _memory_queue.task_done()
            except asyncio.TimeoutError:
                return []
        
        # Drain remaining up to batch_size
        while len(events) < batch_size and not _memory_queue.empty():
            item = _memory_queue.get_nowait()
            events.append(item)
            _memory_queue.task_done()
            
    except Exception as e:
        logger.error(f"Memory queue fetch error: {e}")

    return events

async def get_queue_size() -> int:
    redis = await get_redis()
    if redis:
        try:
            return await redis.llen(settings.REDIS_QUEUE_KEY)
        except Exception:
            pass
    return _memory_queue.qsize()

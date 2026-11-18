import asyncio
import logging

from backend.app.config import settings
from backend.app.database import get_session_maker, create_tables
from backend.app.services.queue import fetch_batch, get_queue_size
from backend.app.services.storage import process_events_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("faultline.worker")

_worker_running = True


async def run_worker():
    global _worker_running
    logger.info("Ingestion worker started.")

    session_maker = get_session_maker()

    while _worker_running:
        try:
            batch = await fetch_batch(
                batch_size=settings.INGESTION_BATCH_SIZE,
                timeout_seconds=0.2
            )

            if batch:
                async with session_maker() as session:
                    processed = await process_events_batch(batch, session)
                    queue_depth = await get_queue_size()
                    logger.debug(f"Batch processed: {processed} items. Queue depth: {queue_depth}")
            else:
                await asyncio.sleep(0.05)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"Worker iteration error: {exc}", exc_info=True)
            await asyncio.sleep(1.0)


def stop_worker():
    global _worker_running
    _worker_running = False


if __name__ == "__main__":
    async def main():
        await create_tables()
        await run_worker()

    asyncio.run(main())

import gzip
import json
import logging
import queue
import threading
import time
from typing import Any, Optional
import httpx

logger = logging.getLogger("faultline.transport")

class HttpTransport:
    """
    High-performance, non-blocking asynchronous event transport.
    Events are placed on an in-memory queue and dispatched by a background daemon thread
    over HTTP with gzip compression.
    """
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        batch_size: int = 20,
        flush_interval_seconds: float = 0.5,
        compress: bool = True
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval_seconds
        self.compress = compress
        
        self._queue = queue.Queue(maxsize=10000)
        self._client = httpx.Client(timeout=5.0)
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True, name="faultline-worker")
        self._worker_thread.start()

    def send(self, event: dict[str, Any]):
        """Non-blocking send: returns in <0.05ms."""
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.warning("Faultline client buffer full. Dropping event.")

    def _worker_loop(self):
        while self._running:
            self._flush_batch()
            time.sleep(self.flush_interval)

    def _flush_batch(self):
        items = []
        try:
            while len(items) < self.batch_size and not self._queue.empty():
                items.append(self._queue.get_nowait())
        except queue.Empty:
            pass

        for item in items:
            self._post_single(item)
            self._queue.task_done()

    def _post_single(self, event: dict[str, Any]):
        url = f"{self.endpoint}/api/v1/capture"
        headers = {
            "Content-Type": "application/json",
            "X-Project-Key": self.api_key,
            "User-Agent": "faultline-python/1.0.0"
        }

        try:
            payload_bytes = json.dumps(event, default=str).encode("utf-8")
            if self.compress and len(payload_bytes) > 1024:
                headers["Content-Encoding"] = "gzip"
                payload_bytes = gzip.compress(payload_bytes)

            resp = self._client.post(url, content=payload_bytes, headers=headers)
            if resp.status_code not in (200, 201, 202):
                logger.warning(f"Faultline ingestion rejected event ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.debug(f"Failed to transmit event to Faultline ({e})")

    def flush_and_close(self, timeout_seconds: float = 2.0):
        """Called on atexit to ensure remaining pending events are transmitted."""
        self._running = False
        start = time.time()
        while not self._queue.empty() and (time.time() - start) < timeout_seconds:
            self._flush_batch()
            time.sleep(0.05)
        try:
            self._client.close()
        except Exception:
            pass

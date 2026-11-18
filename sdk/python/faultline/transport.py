import gzip
import json
import logging
import queue
import threading
import time
from typing import Any
import httpx

logger = logging.getLogger("faultline.transport")


class HttpTransport:
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
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="faultline-transport-worker"
        )
        self._worker_thread.start()

    def send(self, event_payload: dict[str, Any]) -> None:
        try:
            self._queue.put_nowait(event_payload)
        except queue.Full:
            logger.warning("Local event buffer full. Dropping event.")

    def _worker_loop(self) -> None:
        while self._running:
            self._flush_batch()
            time.sleep(self.flush_interval)

    def _flush_batch(self) -> None:
        items = []
        try:
            while len(items) < self.batch_size and not self._queue.empty():
                items.append(self._queue.get_nowait())
        except queue.Empty:
            pass

        for item in items:
            self._dispatch_event(item)
            self._queue.task_done()

    def _dispatch_event(self, event_payload: dict[str, Any]) -> None:
        url = f"{self.endpoint}/api/v1/capture"
        headers = {
            "Content-Type": "application/json",
            "X-Project-Key": self.api_key,
            "User-Agent": "faultline-python/1.0.0"
        }

        try:
            payload_bytes = json.dumps(event_payload, default=str).encode("utf-8")
            if self.compress and len(payload_bytes) > 1024:
                headers["Content-Encoding"] = "gzip"
                payload_bytes = gzip.compress(payload_bytes)

            response = self._client.post(url, content=payload_bytes, headers=headers)
            if response.status_code not in (200, 201, 202):
                logger.warning(f"Ingestion rejected event ({response.status_code}): {response.text}")
        except Exception as exc:
            logger.debug(f"Event delivery error: {exc}")

    def flush_and_close(self, timeout_seconds: float = 2.0) -> None:
        self._running = False
        deadline = time.time() + timeout_seconds
        while not self._queue.empty() and time.time() < deadline:
            self._flush_batch()
            time.sleep(0.05)
        try:
            self._client.close()
        except Exception:
            pass

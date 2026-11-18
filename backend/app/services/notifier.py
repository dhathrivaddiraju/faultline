import json
import logging
from collections import deque
from typing import Any, Optional
import httpx
from fastapi import WebSocket

logger = logging.getLogger("faultline.notifier")


class LatencyTracker:
    def __init__(self, sample_size: int = 1000):
        self._samples: deque[float] = deque(maxlen=sample_size)

    def record(self, latency_ms: float) -> None:
        self._samples.append(latency_ms)

    def get_p99(self) -> float:
        if not self._samples:
            return 0.0
        sorted_samples = sorted(self._samples)
        index = int(len(sorted_samples) * 0.99)
        index = min(index, len(sorted_samples) - 1)
        return round(sorted_samples[index], 2)


latency_tracker = LatencyTracker()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self.active_connections:
            return

        payload = json.dumps(message, default=str)
        stale_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)


ws_manager = ConnectionManager()


async def dispatch_incident_webhook(
    webhook_url: str,
    incident_data: dict[str, Any]
) -> None:
    if not webhook_url:
        return

    payload = {
        "event": "incident.created",
        "incident": {
            "id": incident_data.get("id"),
            "title": incident_data.get("title"),
            "culprit": incident_data.get("culprit"),
            "severity": incident_data.get("severity"),
            "events_count": incident_data.get("events_count", 1),
            "status": incident_data.get("status"),
        }
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code >= 400:
                logger.warning(
                    f"Webhook target {webhook_url} responded with status {response.status_code}"
                )
    except Exception as exc:
        logger.warning(f"Failed to deliver incident alert to {webhook_url}: {exc}")

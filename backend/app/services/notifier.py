import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("faultline.notifier")

class ConnectionManager:
    """Manages active WebSocket connections for live error stream."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast event to all connected dashboard clients."""
        if not self.active_connections:
            return
            
        data_str = json.dumps(message, default=str)
        dead_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(data_str)
            except Exception as e:
                logger.warning(f"Error sending to WebSocket client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

ws_manager = ConnectionManager()

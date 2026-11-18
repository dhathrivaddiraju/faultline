import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.notifier import ws_manager

logger = logging.getLogger("faultline.websockets")
router = APIRouter()


@router.websocket("/live-stream")
async def websocket_live_stream(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning(f"WebSocket client error: {exc}")
        ws_manager.disconnect(websocket)

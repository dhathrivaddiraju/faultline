import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.notifier import ws_manager

logger = logging.getLogger("faultline.websockets")
router = APIRouter()

@router.websocket("/live-stream")
async def websocket_live_stream(websocket: WebSocket):
    """Real-time live error stream over WebSocket."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive heartbeat / client ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)

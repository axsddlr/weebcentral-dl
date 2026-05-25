"""WebSocket handlers for real-time updates"""
import os
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for a given channel."""

    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.add(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.discard(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.discard(ws)


class ConnectionManagers:
    def __init__(self):
        self.progress = ConnectionManager()
        self.queue = ConnectionManager()
        self.logs = ConnectionManager()


async def _verify_ws_token(websocket: WebSocket) -> bool:
    """Check API_TOKEN via httpOnly cookie (sent automatically on handshake)."""
    expected = os.getenv("API_TOKEN")
    if not expected:
        return True
    return websocket.cookies.get("api_token") == expected


async def _ws_handler(websocket: WebSocket, mgr: ConnectionManager):
    if not await _verify_ws_token(websocket):
        await websocket.close(code=4001)
        return
    await mgr.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        mgr.disconnect(websocket)


@ws_router.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket):
    await _ws_handler(websocket, websocket.app.state.ws.progress)


@ws_router.websocket("/ws/queue")
async def ws_queue(websocket: WebSocket):
    await _ws_handler(websocket, websocket.app.state.ws.queue)


@ws_router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await _ws_handler(websocket, websocket.app.state.ws.logs)

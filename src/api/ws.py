"""WebSocket handlers for real-time updates"""
import asyncio
import json
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


progress_manager = ConnectionManager()
queue_manager_ws = ConnectionManager()
logs_manager = ConnectionManager()


@ws_router.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket):
    await progress_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        progress_manager.disconnect(websocket)


@ws_router.websocket("/ws/queue")
async def ws_queue(websocket: WebSocket):
    await queue_manager_ws.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        queue_manager_ws.disconnect(websocket)


@ws_router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await logs_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logs_manager.disconnect(websocket)

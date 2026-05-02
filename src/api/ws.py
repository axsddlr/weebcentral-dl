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


class ConnectionManagers:
    def __init__(self):
        self.progress = ConnectionManager()
        self.queue = ConnectionManager()
        self.logs = ConnectionManager()


@ws_router.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket):
    mgrs = websocket.app.state.ws
    await mgrs.progress.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        mgrs.progress.disconnect(websocket)


@ws_router.websocket("/ws/queue")
async def ws_queue(websocket: WebSocket):
    mgrs = websocket.app.state.ws
    await mgrs.queue.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        mgrs.queue.disconnect(websocket)


@ws_router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    mgrs = websocket.app.state.ws
    await mgrs.logs.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        mgrs.logs.disconnect(websocket)

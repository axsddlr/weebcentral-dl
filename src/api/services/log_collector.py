"""Log collector: captures loguru output into a ring buffer and broadcasts via WebSocket."""
import asyncio
import uuid
from collections import deque
from typing import Optional

from src.logging_utils import logger


class LogCollector:
    """Custom loguru sink that stores logs and broadcasts to WebSocket clients."""

    def __init__(self, max_entries: int = 500, ws_managers=None):
        self.entries: deque = deque(maxlen=max_entries)
        self._sink_id: Optional[int] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.ws = ws_managers

    def install(self):
        """Install as a loguru sink."""
        self._sink_id = logger.add(self._sink, format="{message}", level="DEBUG")
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def uninstall(self):
        """Remove the loguru sink."""
        if self._sink_id is not None:
            logger.remove(self._sink_id)
            self._sink_id = None

    def _sink(self, message):
        """Loguru sink function."""
        record = message.record
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name.lower(),
            "message": record["message"],
            "source": record["name"],
        }
        self.entries.append(entry)

        # Broadcast to WebSocket clients
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                lambda e=entry: asyncio.ensure_future(self._broadcast(e))
            )

    async def _broadcast(self, entry: dict):
        if self.ws:
            await self.ws.logs.broadcast({"type": "log", "data": entry})

    def get_logs(self) -> list:
        return list(self.entries)

    def clear(self):
        self.entries.clear()

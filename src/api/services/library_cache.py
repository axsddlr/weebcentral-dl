"""Library cache: async wrappers with TTL caching for expensive filesystem/archive scans."""
import os
import time
import asyncio

from src.api.services.library_scanner import scan_library, scan_chapters


def _get_dir_size(path: str) -> int:
    total = 0
    if not os.path.exists(path):
        return 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


class LibraryCache:
    def __init__(self, output_dir: str):
        self._output_dir = output_dir
        self._library_ttl = 30
        self._chapters_ttl = 60
        self._size_ttl = 60

        self._library_data = None
        self._library_time: float = 0

        self._chapters_cache: dict[str, tuple[list[dict], float]] = {}

        self._size_data: int | None = None
        self._size_time: float = 0

    def invalidate_all(self):
        self._library_data = None
        self._chapters_cache.clear()
        self._size_data = None

    def set_output_dir(self, output_dir: str):
        if self._output_dir != output_dir:
            self._output_dir = output_dir
            self.invalidate_all()

    async def get_library(self) -> list[dict]:
        now = time.time()
        if self._library_data is not None and now - self._library_time < self._library_ttl:
            return self._library_data
        self._library_data = await asyncio.to_thread(scan_library, self._output_dir)
        self._library_time = now
        return self._library_data

    async def get_chapters(self, series_dir: str) -> list[dict]:
        now = time.time()
        cached = self._chapters_cache.get(series_dir)
        if cached is not None and now - cached[1] < self._chapters_ttl:
            return cached[0]
        data = await asyncio.to_thread(scan_chapters, self._output_dir, series_dir)
        self._chapters_cache[series_dir] = (data, now)
        return data

    async def get_dir_size(self) -> int:
        now = time.time()
        if self._size_data is not None and now - self._size_time < self._size_ttl:
            return self._size_data
        self._size_data = await asyncio.to_thread(_get_dir_size, self._output_dir)
        self._size_time = now
        return self._size_data

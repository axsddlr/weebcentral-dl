"""Library cache: async wrappers with TTL caching for expensive filesystem/archive scans."""
import os
import time
import asyncio

from src.api.services.library_scanner import scan_library, scan_chapters, _resolve_display_path


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


def _get_total_size(dirs: list[str]) -> int:
    return sum(_get_dir_size(d) for d in dirs)


class LibraryCache:
    def __init__(self, output_dir: str, library_paths: list[str] | None = None):
        self._default_dir = os.path.abspath(output_dir)
        self._library_paths = library_paths or []
        self._all_dirs = [self._default_dir] + [os.path.abspath(p) for p in self._library_paths]
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

    def set_output_dir(self, output_dir: str, library_paths: list[str] | None = None):
        new_default = os.path.abspath(output_dir)
        paths = library_paths or []
        new_all = [new_default] + [os.path.abspath(p) for p in paths]
        if self._default_dir != new_default or self._library_paths != paths:
            self._default_dir = new_default
            self._library_paths = paths
            self._all_dirs = new_all
            self.invalidate_all()

    def resolve_path(self, display_path: str) -> tuple[str, str]:
        """Convert display path to (root_dir, series_dir)."""
        return _resolve_display_path(self._all_dirs, display_path)

    async def get_library(self) -> list[dict]:
        now = time.time()
        if self._library_data is not None and now - self._library_time < self._library_ttl:
            return self._library_data
        self._library_data = await asyncio.to_thread(scan_library, self._all_dirs)
        self._library_time = now
        return self._library_data

    async def get_chapters(self, series_dir: str) -> list[dict]:
        now = time.time()
        cached = self._chapters_cache.get(series_dir)
        if cached is not None and now - cached[1] < self._chapters_ttl:
            return cached[0]
        root_dir, entry = self.resolve_path(series_dir)
        data = await asyncio.to_thread(scan_chapters, root_dir, entry)
        self._chapters_cache[series_dir] = (data, now)
        return data

    async def get_recent_chapters(self, limit: int = 20) -> list[dict]:
        """Get most recently downloaded chapters across all library dirs."""
        library = await self.get_library()
        recent = []
        for series in library:
            chapters = await self.get_chapters(series["path"])
            for ch in chapters:
                ch["series_title"] = series["title"]
                ch["series_path"] = series["path"]
                ch["cover_url"] = series.get("coverUrl")
                recent.append(ch)
        recent.sort(key=lambda c: c.get("mtime", 0), reverse=True)
        return recent[:limit]

    async def get_dir_size(self) -> int:
        now = time.time()
        if self._size_data is not None and now - self._size_time < self._size_ttl:
            return self._size_data
        self._size_data = await asyncio.to_thread(_get_total_size, self._all_dirs)
        self._size_time = now
        return self._size_data

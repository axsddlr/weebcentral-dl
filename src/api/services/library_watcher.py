"""File system watcher for library directories: auto-refresh cache on changes."""
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class LibraryFileHandler(FileSystemEventHandler):
    def __init__(self, invalidate_cb):
        self._invalidate = invalidate_cb
        self._debounce: float = 0

    def on_any_event(self, event):
        if event.is_directory:
            return
        ext = os.path.splitext(event.src_path)[1].lower()
        if ext not in ('.cbz', '.zip', '.cbr', '.epub', '.pdf'):
            return
        now = time.time()
        if now - self._debounce > 2:
            self._debounce = now
            self._invalidate()


class LibraryWatcher:
    def __init__(self, directories: list[str], invalidate_cb):
        self._directories = [d for d in directories if os.path.isdir(d)]
        self._observer = Observer()
        self._handler = LibraryFileHandler(invalidate_cb)

    def start(self):
        for d in self._directories:
            self._observer.schedule(self._handler, d, recursive=True)
        if self._directories:
            self._observer.start()

    def stop(self):
        if self._directories:
            self._observer.stop()
            self._observer.join()

    def is_alive(self):
        return self._observer.is_alive() if self._directories else False

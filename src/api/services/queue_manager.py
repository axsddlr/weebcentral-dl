"""Download queue manager: background task processing with progress tracking."""
import asyncio
import uuid
from datetime import datetime
from typing import Optional

from loguru import logger

from src.config import DownloaderConfig
from src.downloader import WeebCentralDownloader
from src.api.services.library_cache import LibraryCache
from src.api.services.log_collector import LogCollector


class DownloadTask:
    def __init__(self, manga_id: str, manga_title: str, chapter_id: str, chapter_number: str, chapter_type: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.manga_id = manga_id
        self.manga_title = manga_title
        self.chapter_id = chapter_id
        self.chapter_number = chapter_number
        self.chapter_type = chapter_type
        self.status = "pending"
        self.progress = 0.0
        self.total_pages = 0
        self.downloaded_pages = 0
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "mangaId": self.manga_id,
            "mangaTitle": self.manga_title,
            "chapterId": self.chapter_id,
            "chapterNumber": self.chapter_number,
            "status": self.status,
            "progress": self.progress,
            "totalPages": self.total_pages,
            "downloadedPages": self.downloaded_pages,
            "error": self.error,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


class QueueManager:
    def __init__(self, downloader: WeebCentralDownloader, config: DownloaderConfig, log_collector: LogCollector, library_cache: LibraryCache, ws_managers):
        self.downloader = downloader
        self.config = config
        self.log_collector = log_collector
        self.library_cache = library_cache
        self.ws = ws_managers
        self.tasks: list[DownloadTask] = []
        self.is_running = True
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self):
        self._worker_task = asyncio.create_task(self._worker())

    async def stop(self):
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    def add_tasks(self, manga_id: str, manga_title: str, chapters: list[dict]) -> list[DownloadTask]:
        """Add download tasks to the queue.

        Args:
            manga_id: Series ID
            manga_title: Series title
            chapters: List of dicts with 'id', 'number', and optionally 'type'
        """
        new_tasks = []
        for ch in chapters:
            task = DownloadTask(
                manga_id=manga_id,
                manga_title=manga_title,
                chapter_id=ch["id"],
                chapter_number=ch["number"],
                chapter_type=ch.get("type", ""),
            )
            self.tasks.append(task)
            new_tasks.append(task)
        asyncio.ensure_future(self._broadcast_queue_update())
        return new_tasks

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def remove_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task and task.status != "downloading":
            self.tasks.remove(task)
            asyncio.ensure_future(self._broadcast_queue_update())
            return True
        return False

    def retry_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task and task.status == "failed":
            task.status = "pending"
            task.error = None
            task.progress = 0
            task.downloaded_pages = 0
            task.updated_at = datetime.now()
            asyncio.ensure_future(self._broadcast_queue_update())
            return True
        return False

    def retry_all_failed(self):
        for task in self.tasks:
            if task.status == "failed":
                task.status = "pending"
                task.error = None
                task.progress = 0
                task.downloaded_pages = 0
                task.updated_at = datetime.now()
        asyncio.ensure_future(self._broadcast_queue_update())

    def clear_completed(self):
        self.tasks = [t for t in self.tasks if t.status != "completed"]
        asyncio.ensure_future(self._broadcast_queue_update())

    def pause(self):
        self.is_running = False
        asyncio.ensure_future(self._broadcast_queue_update())

    def resume(self):
        self.is_running = True
        asyncio.ensure_future(self._broadcast_queue_update())

    def get_queue_state(self) -> dict:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "isRunning": self.is_running,
            "totalTasks": len(self.tasks),
            "completedTasks": sum(1 for t in self.tasks if t.status == "completed"),
            "failedTasks": sum(1 for t in self.tasks if t.status == "failed"),
        }

    async def _worker(self):
        """Background worker: process one task at a time with circuit breaker."""
        consecutive_failures = 0
        while True:
            try:
                if self.is_running:
                    pending = next((t for t in self.tasks if t.status == "pending"), None)
                    if pending:
                        await self._process_task(pending)
                        consecutive_failures = 0
                    else:
                        await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_failures += 1
                backoff = min(5 * (2 ** consecutive_failures), 300)
                logger.error(
                    f"Queue worker error (failure #{consecutive_failures}, "
                    f"backoff {backoff}s): {e}"
                )
                await asyncio.sleep(backoff)

    async def _process_task(self, task: DownloadTask):
        """Process a single download task."""
        task.status = "downloading"
        task.updated_at = datetime.now()
        await self._broadcast_queue_update()
        await self._broadcast_progress(task)

        try:
            # Download cover first
            await asyncio.to_thread(
                self.downloader.download_cover_image_and_convert,
                task.manga_id,
                task.manga_title,
            )

            # Download chapter images
            import tempfile
            import shutil
            import os
            from src.utils import get_vol_and_chapter_names

            _, chapter_dir_name = get_vol_and_chapter_names(task.chapter_number)
            temp_dir = tempfile.mkdtemp(prefix=f"{task.manga_title}-{task.chapter_number}_")

            try:
                chapter_dir = await asyncio.to_thread(
                    self.downloader.download_chapter_images,
                    task.chapter_id,
                    task.chapter_number,
                    temp_dir,
                    chapter_dir_name,
                )

                if chapter_dir and os.path.exists(chapter_dir):
                    # Count images for progress
                    image_count = sum(
                        1 for f in os.listdir(chapter_dir)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))
                    )
                    
                    if image_count == 0:
                        task.status = "failed"
                        task.error = "All image downloads failed for this chapter"
                        logger.error(f"Failed: {task.manga_title} Ch.{task.chapter_number}: No images downloaded")
                    else:
                        task.total_pages = image_count
                        task.downloaded_pages = image_count
                        task.progress = 100
                        task.updated_at = datetime.now()
                        await self._broadcast_progress(task)

                        # Determine chapter type
                        ct = "" if task.chapter_type in ["Chapter", "#", ""] else task.chapter_type

                        # Archive
                        await asyncio.to_thread(
                            self.downloader.archive_chapter,
                            chapter_dir,
                            task.manga_title,
                            task.chapter_number,
                            ct,
                        )

                        task.status = "completed"
                        logger.info(f"Completed: {task.manga_title} Ch.{task.chapter_number}")
                else:
                    task.status = "failed"
                    task.error = "No images found in chapter"
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Failed: {task.manga_title} Ch.{task.chapter_number}: {e}")

        task.updated_at = datetime.now()
        self.library_cache.invalidate_all()
        await self._broadcast_queue_update()
        await self._broadcast_progress(task)

    async def _broadcast_queue_update(self):
        await self.ws.queue.broadcast({
            "type": "queue_update",
            "data": self.get_queue_state(),
        })

    async def _broadcast_progress(self, task: DownloadTask):
        await self.ws.progress.broadcast({
            "type": "progress",
            "data": task.to_dict(),
        })

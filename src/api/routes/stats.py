"""Dashboard statistics routes"""
import asyncio
import os

from fastapi import APIRouter, Request

router = APIRouter(tags=["stats"])


def _format_size(total_bytes: int) -> str:
    """Format bytes to human-readable string."""
    if total_bytes < 1024:
        return f"{total_bytes} B"
    elif total_bytes < 1024 ** 2:
        return f"{total_bytes / 1024:.1f} KB"
    elif total_bytes < 1024 ** 3:
        return f"{total_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{total_bytes / (1024 ** 3):.1f} GB"


@router.get("/stats")
async def get_stats(request: Request):
    """Get dashboard statistics."""
    config = request.app.state.config
    qm = request.app.state.queue_manager
    cache = request.app.state.library_cache

    cache.set_output_dir(os.path.abspath(config.output_dir))

    library, storage_bytes = await asyncio.gather(
        cache.get_library(),
        cache.get_dir_size(),
    )

    total_series = len(library)
    total_chapters = sum(s["totalChapters"] for s in library)

    queue_state = qm.get_queue_state()

    return {
        "totalSeries": total_series,
        "totalChapters": total_chapters,
        "storageUsed": _format_size(storage_bytes),
        "queueActive": sum(
            1 for t in qm.tasks if t.status in ("pending", "downloading")
        ),
        "queueCompleted": queue_state["completedTasks"],
        "queueFailed": queue_state["failedTasks"],
    }

"""Dashboard statistics routes"""
import os

from fastapi import APIRouter, Request

from src.api.services.library_scanner import scan_library

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


def _get_dir_size(path: str) -> int:
    """Calculate total size of a directory recursively."""
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


@router.get("/stats")
async def get_stats(request: Request):
    """Get dashboard statistics."""
    config = request.app.state.config
    output_dir = os.path.abspath(config.output_dir)
    qm = request.app.state.queue_manager

    # Library stats
    library = scan_library(output_dir)
    total_series = len(library)
    total_chapters = sum(s["totalChapters"] for s in library)
    storage_bytes = _get_dir_size(output_dir)

    # Queue stats
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

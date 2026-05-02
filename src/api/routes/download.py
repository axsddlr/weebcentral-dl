"""Download queue routes"""
import asyncio

from fastapi import APIRouter, Request, HTTPException
from src.api.models import AddToQueueRequest

router = APIRouter(tags=["queue"])


@router.get("/queue")
async def get_queue(request: Request):
    """Get current queue state."""
    qm = request.app.state.queue_manager
    return qm.get_queue_state()


@router.post("/queue/add")
async def add_to_queue(request: Request, body: AddToQueueRequest):
    """Add chapters to the download queue."""
    qm = request.app.state.queue_manager
    downloader = request.app.state.downloader

    try:
        chapters_list = await asyncio.to_thread(downloader.fetch_chapter_list, body.seriesId)
        series_title = await asyncio.to_thread(downloader.get_series_title_by_id, body.seriesId)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch series data from WeebCentral: {e}")

    if not chapters_list:
        raise HTTPException(status_code=404, detail="No chapters found for this series")

    chapter_map = {chap_id: (chap_type, chap_num) for chap_type, chap_num, chap_id in chapters_list}

    chapters_to_add = []
    for chapter_id in body.chapters:
        if chapter_id in chapter_map:
            chap_type, chap_num = chapter_map[chapter_id]
            chapters_to_add.append({
                "id": chapter_id,
                "number": chap_num,
                "type": chap_type,
            })

    if not chapters_to_add:
        raise HTTPException(status_code=400, detail="No valid chapters found")

    tasks = qm.add_tasks(body.seriesId, series_title, chapters_to_add)
    return {"added": len(tasks), "tasks": [t.to_dict() for t in tasks]}


@router.post("/queue/pause")
async def pause_queue(request: Request):
    """Pause the download queue."""
    qm = request.app.state.queue_manager
    qm.pause()
    return {"isRunning": False}


@router.post("/queue/resume")
async def resume_queue(request: Request):
    """Resume the download queue."""
    qm = request.app.state.queue_manager
    qm.resume()
    return {"isRunning": True}


@router.delete("/queue/{task_id}")
async def remove_task(request: Request, task_id: str):
    """Remove a task from the queue."""
    qm = request.app.state.queue_manager
    if not qm.remove_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found or currently downloading")
    return {"removed": True}


@router.post("/queue/{task_id}/retry")
async def retry_task(request: Request, task_id: str):
    """Retry a failed task."""
    qm = request.app.state.queue_manager
    if not qm.retry_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found or not failed")
    return {"retried": True}


@router.delete("/queue/completed")
async def clear_completed(request: Request):
    """Clear all completed tasks."""
    qm = request.app.state.queue_manager
    qm.clear_completed()
    return {"cleared": True}


@router.post("/queue/retry-failed")
async def retry_all_failed(request: Request):
    """Retry all failed tasks."""
    qm = request.app.state.queue_manager
    qm.retry_all_failed()
    return {"retried": True}

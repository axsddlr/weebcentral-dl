"""Tracked manga routes"""
import asyncio

from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

from src.cli import process_tracked_mode
from src.database import (
    get_all_tracked, add_tracked, remove_tracked, count_tracked,
    import_from_file, update_cover_url, get_tracked_without_covers,
    update_tracked_status, save_series_metadata, get_series_metadata,
)

router = APIRouter(tags=["tracked"])


class AddTrackedRequest(BaseModel):
    seriesId: str
    title: str
    coverUrl: str | None = None
    status: str = "reading"


async def _scrape_and_save_metadata(downloader, series_id: str):
    """Fetch metadata from WeebCentral and save to DB."""
    try:
        meta = await asyncio.to_thread(downloader.get_series_metadata, series_id)
        if meta.get("coverUrl"):
            update_cover_url(series_id, meta["coverUrl"])
        save_series_metadata(series_id, meta)
    except Exception:
        pass


async def _scrape_missing(downloader):
    """Scrape covers and metadata for entries that lack them."""
    for entry in get_tracked_without_covers():
        await _scrape_and_save_metadata(downloader, entry["series_id"])


@router.get("/tracked")
async def list_tracked(request: Request, status: str = Query(None, description="Filter by status")):
    return {"series": get_all_tracked(status), "total": count_tracked()}


@router.post("/tracked")
async def add_tracked_manga(request: Request, body: AddTrackedRequest):
    if not add_tracked(body.seriesId, body.title, body.coverUrl, body.status):
        raise HTTPException(status_code=400, detail="Failed to add series")
    asyncio.create_task(_scrape_and_save_metadata(request.app.state.downloader, body.seriesId))
    return {"added": True}


@router.put("/tracked/{series_id}/status")
async def set_tracked_status(request: Request, series_id: str, status: str = Query(..., description="New status")):
    if status not in ("reading", "downloading", "complete"):
        raise HTTPException(status_code=400, detail="Invalid status")
    if not update_tracked_status(series_id, status):
        raise HTTPException(status_code=404, detail="Series not found")
    return {"updated": True}


@router.get("/tracked/{series_id}/metadata")
async def tracked_metadata(request: Request, series_id: str):
    meta = get_series_metadata(series_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return meta


@router.delete("/tracked/{series_id}")
async def remove_tracked_manga(request: Request, series_id: str):
    if not remove_tracked(series_id):
        raise HTTPException(status_code=404, detail="Series not found")
    return {"removed": True}


@router.post("/tracked/check")
async def check_tracked(request: Request):
    """Check all tracked manga for new chapters (background)."""
    downloader = request.app.state.downloader

    async def _run_check():
        await asyncio.to_thread(process_tracked_mode, downloader, None)

    asyncio.create_task(_run_check())
    return {"status": "check_started"}


@router.post("/tracked/import")
async def import_tracked(request: Request):
    """Import from manga_list.txt (or MANGA_LIST env) into tracked DB."""
    import os
    filepath = os.getenv("MANGA_LIST") or os.path.join(os.getcwd(), "manga_list.txt")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"{os.path.basename(filepath)} not found")
    added, skipped = import_from_file(filepath)
    asyncio.create_task(_scrape_missing(request.app.state.downloader))
    return {"added": added, "skipped": skipped}

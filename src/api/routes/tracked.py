"""Tracked manga routes"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.database import (
    get_all_tracked, add_tracked, remove_tracked, count_tracked, import_from_file,
)

router = APIRouter(tags=["tracked"])


class AddTrackedRequest(BaseModel):
    seriesId: str
    title: str


@router.get("/tracked")
async def list_tracked(request: Request):
    return {"series": get_all_tracked(), "total": count_tracked()}


@router.post("/tracked")
async def add_tracked_manga(request: Request, body: AddTrackedRequest):
    if not add_tracked(body.seriesId, body.title):
        raise HTTPException(status_code=400, detail="Failed to add series")
    return {"added": True}


@router.delete("/tracked/{series_id}")
async def remove_tracked_manga(request: Request, series_id: str):
    if not remove_tracked(series_id):
        raise HTTPException(status_code=404, detail="Series not found")
    return {"removed": True}


@router.post("/tracked/import")
async def import_tracked(request: Request):
    """Import from manga_list.txt (or MANGA_LIST env) into tracked DB."""
    import os
    filepath = os.getenv("MANGA_LIST") or os.path.join(os.getcwd(), "manga_list.txt")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"{os.path.basename(filepath)} not found")
    added, skipped = import_from_file(filepath)
    return {"added": added, "skipped": skipped}

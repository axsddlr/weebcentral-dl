"""Library routes: list and manage downloaded manga."""
import os
import shutil
import asyncio

from fastapi import APIRouter, Request, HTTPException

from src.utils import resolve_safe_path

router = APIRouter(tags=["library"])


@router.get("/library")
async def list_library(request: Request):
    """List all downloaded manga series."""
    cache = request.app.state.library_cache
    return {"series": await cache.get_library()}


@router.get("/library/{series_dir}/chapters")
async def list_chapters(request: Request, series_dir: str):
    """List chapters in a series."""
    cache = request.app.state.library_cache
    chapters = await cache.get_chapters(series_dir)
    if not chapters:
        root_dir, entry = cache.resolve_path(series_dir)
        if not os.path.exists(os.path.join(root_dir, entry)):
            raise HTTPException(status_code=404, detail="Series not found")
    return {"chapters": chapters}


@router.delete("/library/{series_dir}")
async def delete_series(request: Request, series_dir: str):
    """Delete an entire series directory."""
    cache = request.app.state.library_cache
    root_dir, entry = cache.resolve_path(series_dir)
    try:
        series_path = resolve_safe_path(root_dir, entry)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not os.path.exists(series_path):
        raise HTTPException(status_code=404, detail="Series not found")

    await asyncio.to_thread(shutil.rmtree, series_path)
    cache.invalidate_all()
    return {"deleted": True}

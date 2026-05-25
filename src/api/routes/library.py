"""Library routes: list and manage downloaded manga."""
import os
import shutil
import asyncio
import traceback

from fastapi import APIRouter, Request, HTTPException

from src.utils import resolve_safe_path
from src.manga_utils import add_covers_to_archives_command, migrate_covers_command
from src.logging_utils import logger

router = APIRouter(tags=["library"])


@router.get("/library")
async def list_library(request: Request):
    """List all downloaded manga series."""
    cache = request.app.state.library_cache
    return {"series": await cache.get_library()}


@router.post("/library/refresh")
async def refresh_library(request: Request):
    """Invalidate library cache and trigger a fresh scan."""
    cache = request.app.state.library_cache
    cache.invalidate_all()
    return {"series": await cache.get_library()}


@router.get("/library/recent")
async def recent_chapters(request: Request):
    """Get most recently downloaded chapters across all series."""
    limit = request.query_params.get("limit", 20)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 20
    cache = request.app.state.library_cache
    return {"chapters": await cache.get_recent_chapters(limit)}


@router.get("/library/{series_dir}/chapters")
async def list_chapters(request: Request, series_dir: str):
    """List chapters in a series."""
    try:
        cache = request.app.state.library_cache
        chapters = await cache.get_chapters(series_dir)
        if not chapters:
            root_dir, entry = cache.resolve_path(series_dir)
            if not os.path.exists(os.path.join(root_dir, entry)):
                raise HTTPException(status_code=404, detail="Series not found")
        return {"chapters": chapters}
    except HTTPException:
        raise
    except Exception:
        logger.error(f"list_chapters failed for series_dir={series_dir}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to list chapters")


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


@router.post("/library/maintenance/add-covers")
async def add_covers(request: Request, dry_run: bool = False):
    """Add covers to all archives under the configured output directory."""
    output_dir = request.app.state.config.output_dir
    result = await asyncio.to_thread(add_covers_to_archives_command, output_dir, dry_run, False)
    return result


@router.post("/library/maintenance/migrate-covers")
async def migrate_covers(request: Request, dry_run: bool = False):
    """Rename legacy cover filenames to the explicit naming scheme."""
    output_dir = request.app.state.config.output_dir
    result = await asyncio.to_thread(migrate_covers_command, output_dir, dry_run, False)
    return result

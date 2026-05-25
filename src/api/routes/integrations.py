"""External media server integration routes (Komga, Kavita, etc.)"""
import os
import asyncio

from fastapi import APIRouter, Request, HTTPException

from src.config import load_external_server_config
from src.integrations import import_chapter

router = APIRouter(tags=["integrations"])


@router.get("/integrations/server")
async def get_external_config(request: Request):
    config = load_external_server_config(request.app.state.config_path)
    return {"url": config.url, "apiKey": config.api_key, "libraryId": config.library_id}


@router.post("/integrations/server/import/{series_path:path}")
async def import_series_to_external_server(request: Request, series_path: str):
    """Import all chapters of a series into the external media server."""
    config = load_external_server_config(request.app.state.config_path)
    if not config.url or not config.api_key:
        raise HTTPException(status_code=400, detail="External server not configured")

    cache = request.app.state.library_cache
    root_dir, entry = cache.resolve_path(series_path)
    chapters = await cache.get_chapters(series_path)
    library = await cache.get_library()

    series_title = series_path
    for s in library:
        if s["path"] == series_path:
            series_title = s["title"]
            break

    async def _run_import():
        imported = 0
        for ch in chapters:
            filepath = os.path.join(root_dir, entry, ch["filename"])
            if await asyncio.to_thread(import_chapter, config, filepath, series_title):
                imported += 1
        return imported

    count = await _run_import()
    return {"imported": count}

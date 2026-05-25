"""Reader routes: serve manga pages from archives."""
import os
import asyncio
import mimetypes
import traceback

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response

from src.api.services.library_scanner import get_archive_pages, read_page_by_index, get_cover_path, read_cover_bytes
from src.logging_utils import logger

router = APIRouter(tags=["reader"])


@router.get("/reader/{series_dir}/{archive}/pages")
async def list_pages(request: Request, series_dir: str, archive: str):
    """List page filenames in an archive."""
    try:
        cache = request.app.state.library_cache
        root_dir, entry = cache.resolve_path(series_dir)
        pages = await asyncio.to_thread(get_archive_pages, root_dir, entry, archive)
        return {"pages": pages, "totalPages": len(pages)}
    except Exception:
        logger.error(f"list_pages failed for series_dir={series_dir}, archive={archive}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to list pages")


@router.get("/reader/{series_dir}/{archive}/page/{page_index}")
async def get_page(request: Request, series_dir: str, archive: str, page_index: int):
    """Serve a page image from an archive by index (0-based)."""
    try:
        cache = request.app.state.library_cache
        root_dir, entry = cache.resolve_path(series_dir)
        pages, data = await asyncio.to_thread(read_page_by_index, root_dir, entry, archive, page_index)

        if data is None:
            raise HTTPException(status_code=404, detail="Page not found")

        page_name = pages[page_index]
        content_type = mimetypes.guess_type(page_name)[0] or "image/jpeg"
        return Response(content=data, media_type=content_type)
    except HTTPException:
        raise
    except Exception:
        logger.error(f"get_page failed for series_dir={series_dir}, archive={archive}, index={page_index}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to read page")


@router.get("/reader/{series_dir}/cover")
async def get_cover(request: Request, series_dir: str):
    """Serve the cover image for a series."""
    try:
        cache = request.app.state.library_cache
        root_dir, entry = cache.resolve_path(series_dir)
        cover_path = await asyncio.to_thread(get_cover_path, root_dir, entry)

        if not cover_path or not os.path.exists(cover_path):
            raise HTTPException(status_code=404, detail="Cover not found")

        content_type = mimetypes.guess_type(cover_path)[0] or "image/jpeg"
        data = await asyncio.to_thread(read_cover_bytes, cover_path)
        if data is None:
            raise HTTPException(status_code=404, detail="Failed to read cover")
        return Response(content=data, media_type=content_type)
    except HTTPException:
        raise
    except Exception:
        logger.error(f"get_cover failed for series_dir={series_dir}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to serve cover")

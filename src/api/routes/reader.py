"""Reader routes: serve manga pages from archives."""
import os
import mimetypes

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response

from src.api.services.library_scanner import get_archive_pages, read_page_from_archive, get_cover_path

router = APIRouter(tags=["reader"])


@router.get("/reader/{series_dir}/{archive}/pages")
async def list_pages(request: Request, series_dir: str, archive: str):
    """List page filenames in an archive."""
    output_dir = os.path.abspath(request.app.state.config.output_dir)
    pages = get_archive_pages(output_dir, series_dir, archive)
    return {"pages": pages, "totalPages": len(pages)}


@router.get("/reader/{series_dir}/{archive}/page/{page_index}")
async def get_page(request: Request, series_dir: str, archive: str, page_index: int):
    """Serve a page image from an archive by index (0-based)."""
    output_dir = os.path.abspath(request.app.state.config.output_dir)
    pages = get_archive_pages(output_dir, series_dir, archive)

    if page_index < 0 or page_index >= len(pages):
        raise HTTPException(status_code=404, detail="Page not found")

    page_name = pages[page_index]
    data = read_page_from_archive(output_dir, series_dir, archive, page_name)
    if data is None:
        raise HTTPException(status_code=404, detail="Failed to read page")

    content_type = mimetypes.guess_type(page_name)[0] or "image/jpeg"
    return Response(content=data, media_type=content_type)


@router.get("/reader/{series_dir}/cover")
async def get_cover(request: Request, series_dir: str):
    """Serve the cover image for a series."""
    output_dir = os.path.abspath(request.app.state.config.output_dir)
    cover_path = get_cover_path(output_dir, series_dir)

    if not cover_path or not os.path.exists(cover_path):
        raise HTTPException(status_code=404, detail="Cover not found")

    content_type = mimetypes.guess_type(cover_path)[0] or "image/jpeg"
    with open(cover_path, "rb") as f:
        data = f.read()
    return Response(content=data, media_type=content_type)

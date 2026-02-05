"""Search and series routes"""
import asyncio
import re
import html as html_mod

from fastapi import APIRouter, Query, Request, HTTPException

router = APIRouter(tags=["search"])


@router.get("/search")
async def search_manga(request: Request, q: str = Query(..., min_length=1)):
    """Search for manga on WeebCentral."""
    downloader = request.app.state.downloader

    # Run blocking scraper call in thread
    result = await asyncio.to_thread(downloader.get_series_id_from_query, q)

    if not result or not result[0]:
        return {"results": []}

    series_id, series_title = result

    # Fetch metadata for the result
    metadata = await asyncio.to_thread(downloader.get_series_metadata, series_id)

    # Extract cover URL from series page
    cover_url = None
    try:
        resp = await asyncio.to_thread(
            downloader.scraper.get,
            f"https://weebcentral.com/series/{series_id}",
        )
        m = re.search(r'<source srcset="([^"]+)"', resp.text)
        if m:
            cover_url = m.group(1)
    except Exception:
        pass

    return {
        "results": [
            {
                "id": series_id,
                "title": metadata.get("title", series_title),
                "englishTitle": series_title,
                "coverUrl": cover_url,
                "description": metadata.get("description", ""),
                "author": metadata.get("authors", []),
                "tags": metadata.get("tags", []),
            }
        ]
    }


@router.get("/series/{series_id}")
async def get_series(request: Request, series_id: str):
    """Get series metadata."""
    downloader = request.app.state.downloader
    metadata = await asyncio.to_thread(downloader.get_series_metadata, series_id)

    # Get cover URL
    cover_url = None
    try:
        resp = await asyncio.to_thread(
            downloader.scraper.get,
            f"https://weebcentral.com/series/{series_id}",
        )
        m = re.search(r'<source srcset="([^"]+)"', resp.text)
        if m:
            cover_url = m.group(1)
    except Exception:
        pass

    return {
        "id": series_id,
        "title": metadata.get("title", ""),
        "coverUrl": cover_url,
        "description": metadata.get("description", ""),
        "author": metadata.get("authors", []),
        "tags": metadata.get("tags", []),
    }


@router.get("/series/{series_id}/chapters")
async def get_chapters(request: Request, series_id: str):
    """List all chapters for a series."""
    downloader = request.app.state.downloader
    chapters = await asyncio.to_thread(downloader.fetch_chapter_list, series_id)

    return {
        "seriesId": series_id,
        "chapters": [
            {"id": chap_id, "number": chap_num, "type": chap_type}
            for chap_type, chap_num, chap_id in chapters
        ],
    }

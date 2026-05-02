"""Search and series routes"""
import asyncio

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["search"])


@router.get("/search")
async def search_manga(request: Request, q: str = Query(..., min_length=1)):
    """Search for manga on WeebCentral."""
    downloader = request.app.state.downloader

    result = await asyncio.to_thread(downloader.get_series_id_from_query, q)

    if not result or not result[0]:
        return {"results": []}

    series_id, series_title = result

    metadata = await asyncio.to_thread(downloader.get_series_metadata, series_id)

    return {
        "results": [
            {
                "id": series_id,
                "title": metadata.get("title", series_title),
                "englishTitle": series_title,
                "coverUrl": metadata.get("coverUrl"),
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

    return {
        "id": series_id,
        "title": metadata.get("title", ""),
        "coverUrl": metadata.get("coverUrl"),
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

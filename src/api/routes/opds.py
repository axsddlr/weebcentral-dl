"""OPDS catalog feed routes (OPDS 1.2)"""
import os
import asyncio
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter(tags=["opds"])

OPDS_NAV = "application/atom+xml;profile=opds-catalog;kind=navigation"
OPDS_ACQ = "application/atom+xml;profile=opds-catalog;kind=acquisition"


def _atom_id(*parts: str) -> str:
    return f"urn:uuid:weebcentral-dl:" + ":".join(parts)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _feed_xml(title: str, feed_id: str, updated: str, self_href: str,
              self_type: str, entries: list[str], start_href: str = "/api/opds") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog"
      xmlns:dc="http://purl.org/dc/terms/">
  <id>{escape(feed_id)}</id>
  <title>{escape(title)}</title>
  <updated>{updated}</updated>
  <link rel="self" href="{escape(self_href)}" type="{escape(self_type)}"/>
  <link rel="start" href="{escape(start_href)}" type="{OPDS_NAV}"/>
{chr(10).join(entries)}
</feed>"""


def _nav_entry(title: str, href: str, updated: str, entry_id: str,
               summary: str = "") -> str:
    return f"""  <entry>
    <title>{escape(title)}</title>
    <link rel="subsection" href="{escape(href)}" type="{OPDS_ACQ}"/>
    <updated>{updated}</updated>
    <id>{escape(entry_id)}</id>
    <content type="text">{escape(summary or title)}</content>
  </entry>"""


def _acq_entry(title: str, href: str, link_type: str, updated: str,
               entry_id: str, summary: str = "",
               image_href: str | None = None) -> str:
    img = ""
    if image_href:
        img = f'    <link rel="http://opds-spec.org/image" href="{escape(image_href)}" type="image/jpeg"/>\n'
    return f"""  <entry>
    <title>{escape(title)}</title>
{img}    <link rel="http://opds-spec.org/acquisition" href="{escape(href)}" type="{escape(link_type)}"/>
    <updated>{updated}</updated>
    <id>{escape(entry_id)}</id>
    <content type="text">{escape(summary or title)}</content>
  </entry>"""


@router.get("/opds")
async def opds_root(request: Request):
    """OPDS root navigation catalog."""
    updated = _iso_now()
    entries = [
        _nav_entry("All Series", "/api/opds/series", updated,
                   _atom_id("nav", "series"), "Browse all series in your library"),
        _nav_entry("Recently Added", "/api/opds/recent", updated,
                   _atom_id("nav", "recent"), "Recently added chapters"),
    ]
    xml = _feed_xml("WeebCentral Downloader", _atom_id("root"), updated,
                    "/api/opds", OPDS_NAV, entries)
    return Response(content=xml, media_type=OPDS_NAV)


@router.get("/opds/series")
async def opds_series(request: Request):
    """OPDS acquisition feed listing all series."""
    cache = request.app.state.library_cache
    library = await cache.get_library()
    updated = _iso_now()

    entries = []
    for s in library:
        entries.append(_nav_entry(
            s["title"],
            f"/api/opds/series/{s['path']}",
            updated,
            _atom_id("series", s["path"]),
            f"{s['totalChapters']} chapters",
        ))

    xml = _feed_xml("All Series", _atom_id("series-catalog"), updated,
                    "/api/opds/series", OPDS_ACQ, entries)
    return Response(content=xml, media_type=OPDS_ACQ)


@router.get("/opds/recent")
async def opds_recent(request: Request):
    """OPDS acquisition feed listing recently added chapters."""
    cache = request.app.state.library_cache
    recent = await cache.get_recent_chapters(30)
    updated = _iso_now()

    entries = []
    for ch in recent:
        series_path = ch["series_path"]
        chapter_file = ch["filename"]
        ext = os.path.splitext(chapter_file)[1].lower()
        mime = "application/vnd.comicbook+zip" if ext == ".cbz" else "application/zip"
        image_href = f"/api/reader/{series_path}/cover" if ch.get("cover_url") else None
        href = f"/api/reader/{series_path}/{chapter_file}"

        title = f"{ch['series_title']} — Ch. {ch['number']}"
        summary = f"Chapter {ch['number']} — {ch['totalPages']} pages"

        entries.append(_acq_entry(
            title, href, mime, updated,
            _atom_id("chapter", series_path, chapter_file),
            summary, image_href,
        ))

    xml = _feed_xml("Recently Added", _atom_id("recent-catalog"), updated,
                    "/api/opds/recent", OPDS_ACQ, entries)
    return Response(content=xml, media_type=OPDS_ACQ)


@router.get("/opds/series/{series_path:path}")
async def opds_series_chapters(request: Request, series_path: str):
    """OPDS acquisition feed listing chapters for a series."""
    cache = request.app.state.library_cache
    chapters = await cache.get_chapters(series_path)
    library = await cache.get_library()

    series_title = series_path
    cover_url = None
    for s in library:
        if s["path"] == series_path:
            series_title = s["title"]
            cover_url = s.get("coverUrl")
            break

    updated = _iso_now()
    entries = []

    for ch in chapters:
        ext = os.path.splitext(ch["filename"])[1].lower()
        mime = "application/vnd.comicbook+zip" if ext == ".cbz" else "application/zip"
        href = f"/api/reader/{series_path}/{ch['filename']}"
        image_href = f"/api/reader/{series_path}/cover" if cover_url else None
        summary = f"Chapter {ch['number']} — {ch['totalPages']} pages"

        entries.append(_acq_entry(
            f"Chapter {ch['number']}",
            href, mime, updated,
            _atom_id("chapter", series_path, ch["filename"]),
            summary, image_href,
        ))

    xml = _feed_xml(f"{series_title} — Chapters",
                    _atom_id("series-chapters", series_path),
                    updated, f"/api/opds/series/{series_path}",
                    OPDS_ACQ, entries)
    return Response(content=xml, media_type=OPDS_ACQ)

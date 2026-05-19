"""ComicInfo.xml helpers for downloaded manga archives."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import List, Optional
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class SeriesMetadata:
    """Structured metadata parsed from a WeebCentral series page."""

    series_id: str
    series_title: str
    source_url: str
    description: str = ""
    authors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


def _extract_h1_title(page_html: str) -> str:
    match = re.search(r"<h1[^>]*>([^<]+)</h1>", page_html)
    return html.unescape(match.group(1).strip()) if match else ""


def _extract_list_after_label(page_html: str, label: str) -> list[str]:
    section = re.search(
        rf"<strong[^>]*>[^<]*{re.escape(label)}[^<]*</strong>(.*?)(?=<strong|$)",
        page_html,
        re.IGNORECASE | re.DOTALL,
    )
    if not section:
        return []

    return [
        html.unescape(item.strip())
        for item in re.findall(r"<a[^>]*>([^<]+)</a>", section.group(1))
        if item.strip()
    ]


def _extract_description(page_html: str) -> str:
    match = re.search(
        r'<strong[^>]*>[^<]*Description[^<]*</strong>\s*\+?\s*<p[^>]*>([^<]+)</p>',
        page_html,
        re.IGNORECASE,
    )
    return html.unescape(match.group(1).strip()) if match else ""


def extract_series_metadata(page_html: str, series_id: str, source_url: str) -> SeriesMetadata:
    """Extract structured series metadata from a WeebCentral series page."""
    return SeriesMetadata(
        series_id=series_id,
        series_title=_extract_h1_title(page_html),
        source_url=source_url,
        description=_extract_description(page_html),
        authors=_extract_list_after_label(page_html, "Author"),
        tags=_extract_list_after_label(page_html, "Tags"),
    )


def build_comicinfo_xml(
    metadata: SeriesMetadata,
    chapter_title: str,
    chapter_number: str,
    language_iso: str = "en",
) -> str:
    """Build a ComicInfo.xml payload for a chapter archive."""
    root = ET.Element("ComicInfo", Version="1.0")

    def add_text(tag: str, value: Optional[str]) -> None:
        if value:
            el = ET.SubElement(root, tag)
            el.text = value

    add_text("Series", metadata.series_title)
    add_text("Title", chapter_title)
    add_text("Number", chapter_number)
    add_text("Summary", metadata.description)
    add_text("Writer", ", ".join(metadata.authors))
    add_text("Genre", ", ".join(metadata.tags))
    add_text("Web", metadata.source_url)
    add_text("LanguageISO", language_iso)
    add_text("Manga", "Yes")

    return ET.tostring(root, encoding="unicode")

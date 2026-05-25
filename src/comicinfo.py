"""ComicInfo.xml generation helpers."""

from __future__ import annotations

from xml.etree import ElementTree as ET


def build_comicinfo_xml(
    series_title: str,
    series_id: str,
    chapter_num: str,
    chapter_type: str,
    metadata: dict,
    source_url: str,
) -> str:
    """Build ComicInfo.xml content from series metadata."""
    root = ET.Element("ComicInfo", Version="2.0")

    def add(tag: str, value):
        if value:
            el = ET.SubElement(root, tag)
            el.text = str(value)

    chapter_title = f"{chapter_type} {chapter_num}".strip() if chapter_type else chapter_num
    add("Series", series_title)
    add("Title", chapter_title)
    add("Number", chapter_num)
    add("Summary", metadata.get("description", ""))
    add("Writer", ", ".join(metadata.get("authors", [])))
    add("Genre", ", ".join(metadata.get("tags", [])))
    add("Web", source_url)
    add("Manga", "YesAndRightToLeft")
    add("LanguageISO", "en")
    add("Notes", f"Series ID: {series_id}")

    add("Status", metadata.get("status", "").capitalize())
    add("Count", metadata.get("total_chapters", ""))
    add("AgeRating", "Adult" if metadata.get("adult") else "Unknown")
    add("Year", metadata.get("release_year", ""))
    add("Publisher", "Webcomic" if metadata.get("type") == "Webcomic" else metadata.get("publisher", ""))

    if metadata.get("anime_adaptation"):
        ET.SubElement(root, "CommunityRating").text = "5"
        ET.SubElement(root, "UserRating").text = "5"

    return ET.tostring(root, encoding="unicode")

"""Library scanner: scan manga_downloads/ directory for downloaded series and chapters."""
import os
import re
import zipfile
from pathlib import Path
from typing import Optional


def scan_library(output_dir: str) -> list[dict]:
    """Scan the output directory for downloaded manga series.

    Returns:
        List of series dicts with title, chapter count, cover URL, and path.
    """
    if not os.path.exists(output_dir):
        return []

    series_list = []
    for entry in sorted(os.listdir(output_dir)):
        series_path = os.path.join(output_dir, entry)
        if not os.path.isdir(series_path):
            continue

        # Count archives (.cbz and .zip)
        archives = [
            f for f in os.listdir(series_path)
            if f.lower().endswith(('.cbz', '.zip'))
        ]

        # Find cover image (26-char basename = WeebCentral series ID)
        cover_file = _find_cover(series_path)

        series_list.append({
            "id": entry,
            "title": entry.replace("-", " "),
            "coverUrl": f"/api/reader/{entry}/cover" if cover_file else None,
            "totalChapters": len(archives),
            "path": entry,
        })

    return series_list


def scan_chapters(output_dir: str, series_dir: str) -> list[dict]:
    """List chapters (archives) in a series directory.

    Returns:
        List of chapter dicts sorted by chapter number.
    """
    series_path = os.path.join(output_dir, series_dir)
    if not os.path.exists(series_path):
        return []

    chapters = []
    for f in sorted(os.listdir(series_path)):
        if not f.lower().endswith(('.cbz', '.zip')):
            continue

        chapter_num = _extract_chapter_number(f, series_dir)
        page_count = _count_pages_in_archive(os.path.join(series_path, f))

        chapters.append({
            "id": f,
            "number": chapter_num,
            "filename": f,
            "totalPages": page_count,
            "path": f,
        })

    # Sort by chapter number
    chapters.sort(key=lambda c: float(c["number"]) if c["number"] else 0, reverse=True)
    return chapters


def get_archive_pages(output_dir: str, series_dir: str, archive: str) -> list[str]:
    """List image filenames inside an archive.

    Returns:
        Sorted list of image filenames.
    """
    archive_path = os.path.join(output_dir, series_dir, archive)
    if not os.path.exists(archive_path):
        return []

    image_exts = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            pages = [
                name for name in zf.namelist()
                if name.lower().endswith(image_exts) and not name.startswith('__MACOSX')
            ]
            return sorted(pages)
    except zipfile.BadZipFile:
        return []


def read_page_from_archive(output_dir: str, series_dir: str, archive: str, page_name: str) -> Optional[bytes]:
    """Read a single page image from an archive.

    Returns:
        Image bytes, or None if not found.
    """
    archive_path = os.path.join(output_dir, series_dir, archive)
    if not os.path.exists(archive_path):
        return None

    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            return zf.read(page_name)
    except (zipfile.BadZipFile, KeyError):
        return None


def get_cover_path(output_dir: str, series_dir: str) -> Optional[str]:
    """Find cover image file in series directory."""
    series_path = os.path.join(output_dir, series_dir)
    return _find_cover(series_path)


def _find_cover(series_path: str) -> Optional[str]:
    """Find cover image: file with 26-char base name (WeebCentral ID pattern)."""
    if not os.path.exists(series_path):
        return None
    for f in os.listdir(series_path):
        if f.endswith(('.jpg', '.webp')) and len(f.split('.')[0]) == 26:
            return os.path.join(series_path, f)
    return None


def _extract_chapter_number(filename: str, series_dir: str) -> str:
    """Extract chapter number from archive filename."""
    # CBZ format: series-title-N.cbz or series-title-N-Type.cbz
    cbz_match = re.search(rf'{re.escape(series_dir)}-(\d+(?:\.\d+)?)', filename)
    if cbz_match:
        return cbz_match.group(1)

    # ZIP format: vol_NNN.zip or vol_N-N.zip
    vol_match = re.search(r'vol_0*(\d+)(?:-(\d+))?\.zip$', filename)
    if vol_match:
        if vol_match.group(2):
            return f"{vol_match.group(1)}.{vol_match.group(2)}"
        return vol_match.group(1)

    return "0"


def _count_pages_in_archive(archive_path: str) -> int:
    """Count image files in an archive."""
    image_exts = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            return sum(
                1 for name in zf.namelist()
                if name.lower().endswith(image_exts)
                and not name.startswith('__MACOSX')
                and not name.startswith('000-cover')
            )
    except zipfile.BadZipFile:
        return 0

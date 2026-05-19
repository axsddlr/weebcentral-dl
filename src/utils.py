import os
import re
import unicodedata
from pathlib import Path
from typing import Optional, Sequence, Tuple

COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
LEGACY_COVER_STEM = re.compile(r"^[A-Za-z0-9]{26}$")


def sanitize_title(title: str) -> str:
    """Sanitizes a title to be used as a valid directory name."""
    title = title.replace(" ", "-")
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    title = re.sub(r"[^A-Za-z0-9\-_]", "", title)
    return re.sub(r"-+", "-", title).strip("-")


def get_vol_and_chapter_names(chap_num: str) -> Tuple[str, str]:
    """Generates volume and chapter directory names from a chapter number."""
    base = int(float(chap_num))
    dec = None
    if "." in str(chap_num):
        dec = str(chap_num).split(".")[-1]
        if dec != "0":
            return f"vol_{base}-{dec}", f"chapter_{base}-{dec}"
    return f"vol_{base:03d}", f"chapter_{base:03d}"


def has_images(folder: str) -> bool:
    """Checks if a directory contains any image files."""
    exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
    if not os.path.exists(folder):
        return False
    for f in os.listdir(folder):
        if f.lower().endswith(exts):
            return True
    return False


def build_cover_filename(series_id: str, ext: str) -> str:
    """Build the on-disk cover filename for a series."""
    ext = ext if ext.startswith(".") else f".{ext}"
    return f"{series_id}-cover{ext.lower()}"


def extract_series_id_from_cover_filename(filename: str) -> Optional[str]:
    """Extract the series ID from a cover filename created by the downloader."""
    path = Path(filename)
    if path.suffix.lower() not in COVER_EXTENSIONS:
        return None

    stem = path.stem
    if stem.endswith("-cover"):
        series_id = stem.removesuffix("-cover").strip()
        return series_id or None
    return None


def is_legacy_cover_filename(filename: str) -> bool:
    """Check whether a filename matches the old implicit cover naming scheme."""
    path = Path(filename)
    return path.suffix.lower() in COVER_EXTENSIONS and bool(LEGACY_COVER_STEM.fullmatch(path.stem))


def legacy_cover_target_filename(filename: str) -> Optional[str]:
    """Return the migrated filename for a legacy cover name."""
    path = Path(filename)
    if not is_legacy_cover_filename(filename):
        return None
    return build_cover_filename(path.stem, path.suffix)


def build_cover_archive_name(cover_path: str) -> str:
    """Build the archive entry name for a cover image."""
    return f"000-cover{Path(cover_path).suffix.lower()}"


def migrate_legacy_cover_filename(folder_path: str, filename: str) -> Optional[str]:
    """Rename a legacy cover filename to the explicit cover naming scheme.

    Returns the new absolute path if a migration happened, the existing explicit
    path if one already exists, or ``None`` if the file is not a legacy cover.
    """
    if not is_legacy_cover_filename(filename):
        return None

    source = Path(folder_path) / filename
    target = source.with_name(build_cover_filename(source.stem, source.suffix))

    if target.exists():
        return str(target)

    source.rename(target)
    return str(target)


def migrate_legacy_cover_filenames(folder_path: str, dry_run: bool = False) -> int:
    """Migrate every legacy cover filename in a folder.

    Returns the number of files migrated or that would be migrated in dry-run
    mode.
    """
    migrated_count = 0
    for filename in os.listdir(folder_path):
        if not is_legacy_cover_filename(filename):
            continue
        migrated_count += 1
        if not dry_run:
            migrate_legacy_cover_filename(folder_path, filename)
    return migrated_count


def find_cover_image_path(folder_path: str) -> Optional[str]:
    """Find the explicit cover image path, migrating old names if needed."""
    if not os.path.exists(folder_path):
        return None

    for filename in os.listdir(folder_path):
        if extract_series_id_from_cover_filename(filename):
            return os.path.join(folder_path, filename)

    for filename in os.listdir(folder_path):
        migrated = migrate_legacy_cover_filename(folder_path, filename)
        if migrated:
            return migrated

    return None


def _contains_cjk(text: str) -> bool:
    for ch in text:
        codepoint = ord(ch)
        if (
            0x3040 <= codepoint <= 0x30FF  # Hiragana and Katakana
            or 0x3400 <= codepoint <= 0x4DBF  # CJK Unified Ideographs Extension A
            or 0x4E00 <= codepoint <= 0x9FFF  # CJK Unified Ideographs
            or 0xF900 <= codepoint <= 0xFAFF  # CJK Compatibility Ideographs
        ):
            return True
    return False


def choose_series_title(
    h1_title: str,
    associated_names: Sequence[str],
    prefer_english_title: bool = False,
) -> str:
    """Choose the title to use for a series page.

    The downloader no longer guesses romaji from particle words. When English
    titles are requested, it only falls back to an associated name if the H1
    title contains CJK characters and an alternate name is available.
    """
    title = h1_title.strip()
    if not prefer_english_title:
        return title

    cleaned_alternates = [name.strip() for name in associated_names if name and name.strip()]
    if cleaned_alternates and _contains_cjk(title):
        ascii_alternates = [name for name in cleaned_alternates if name.isascii()]
        return ascii_alternates[0] if ascii_alternates else cleaned_alternates[0]

    return title

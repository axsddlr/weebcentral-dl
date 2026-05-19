import os
import re
import unicodedata
from pathlib import Path
from typing import Optional, Tuple

COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
LEGACY_COVER_STEM = re.compile(r"^[A-Za-z0-9]{26}$")


def sanitize_title(title: str) -> str:
    """Sanitizes a title to be used as a valid directory name.

    Preserves non-ASCII characters (e.g. CJK) when the ASCII-stripped
    result would be empty, so Japanese-only titles don't produce an
    empty directory name.
    """
    title = title.replace(" ", "-")
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    ascii_title = re.sub(r"[^A-Za-z0-9\-_]", "", ascii_title)

    if ascii_title.strip("-"):
        return re.sub(r"-+", "-", ascii_title).strip("-")

    title = re.sub(r'[<>:"/\\|?*]', "", title)
    title = unicodedata.normalize("NFKC", title)
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


def find_cover_in_dir(directory: str) -> str | None:
    """Find a WeebCentral cover image in a directory.

    Prefer the explicit `<series_id>-cover.<ext>` naming convention and
    fall back to legacy 26-character basenames.
    Returns the full path or None.
    """
    if not os.path.exists(directory):
        return None
    for f in os.listdir(directory):
        if extract_series_id_from_cover_filename(f):
            return os.path.join(directory, f)
    return None


def build_cover_filename(series_id: str, ext: str) -> str:
    """Build the on-disk cover filename for a series."""
    ext = ext if ext.startswith(".") else f".{ext}"
    return f"{series_id}-cover{ext.lower()}"


def extract_series_id_from_cover_filename(filename: str) -> Optional[str]:
    """Extract the series ID from an explicit cover filename."""
    path = Path(filename)
    if path.suffix.lower() not in COVER_EXTENSIONS:
        return None

    stem = path.stem
    if stem.endswith("-cover"):
        series_id = stem.removesuffix("-cover").strip()
        return series_id or None

    if LEGACY_COVER_STEM.fullmatch(stem):
        return stem

    return None


def is_legacy_cover_filename(filename: str) -> bool:
    """Check whether a filename matches the old implicit cover scheme."""
    path = Path(filename)
    return path.suffix.lower() in COVER_EXTENSIONS and bool(LEGACY_COVER_STEM.fullmatch(path.stem))


def legacy_cover_target_filename(filename: str) -> Optional[str]:
    """Return the migrated filename for a legacy cover name."""
    if not is_legacy_cover_filename(filename):
        return None
    path = Path(filename)
    return build_cover_filename(path.stem, path.suffix)


def migrate_legacy_cover_filename(folder_path: str, filename: str) -> Optional[str]:
    """Rename a legacy cover filename to the explicit naming scheme."""
    if not is_legacy_cover_filename(filename):
        return None

    source = Path(folder_path) / filename
    target = source.with_name(build_cover_filename(source.stem, source.suffix))

    if target.exists():
        return str(target)

    source.rename(target)
    return str(target)


def migrate_legacy_cover_filenames(folder_path: str, dry_run: bool = False) -> int:
    """Migrate every legacy cover filename in a folder."""
    migrated_count = 0
    for filename in os.listdir(folder_path):
        if not is_legacy_cover_filename(filename):
            continue
        migrated_count += 1
        if not dry_run:
            migrate_legacy_cover_filename(folder_path, filename)
    return migrated_count


def resolve_safe_path(base_dir: str, *path_parts: str) -> str:
    """
    Safely joins path parts and ensures the result is within the base directory.
    Resolves symlinks via realpath() to prevent symlink-based escapes.
    Raises ValueError if the path escapes the base directory.
    """
    base_dir = os.path.realpath(os.path.abspath(base_dir))
    joined_path = os.path.realpath(os.path.abspath(os.path.join(base_dir, *path_parts)))

    # Use commonpath to ensure containment
    # commonpath raises ValueError if paths are on different drives on Windows, 
    # which is also a form of "escape".
    try:
        if os.path.commonpath([base_dir, joined_path]) != base_dir:
            raise ValueError("Path escaped base directory")
    except ValueError:
        raise ValueError("Path escaped base directory")

    return joined_path

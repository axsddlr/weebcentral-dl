import os
import re
import unicodedata
from typing import Tuple


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

    Cover images are identified by a 26-character basename (series ID).
    Returns the full path or None.
    """
    if not os.path.exists(directory):
        return None
    for f in os.listdir(directory):
        if f.endswith(('.jpg', '.webp')) and len(os.path.splitext(f)[0]) == 26:
            return os.path.join(directory, f)
    return None


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

import os
import re
import unicodedata
from typing import Tuple


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


def resolve_safe_path(base_dir: str, *path_parts: str) -> str:
    """
    Safely joins path parts and ensures the result is within the base directory.
    Raises ValueError if the path escapes the base directory.
    """
    base_dir = os.path.abspath(base_dir)
    joined_path = os.path.abspath(os.path.join(base_dir, *path_parts))

    # Use commonpath to ensure containment
    # commonpath raises ValueError if paths are on different drives on Windows, 
    # which is also a form of "escape".
    try:
        if os.path.commonpath([base_dir, joined_path]) != base_dir:
            raise ValueError("Path escaped base directory")
    except ValueError:
        raise ValueError("Path escaped base directory")

    return joined_path

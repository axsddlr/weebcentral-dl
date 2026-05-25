"""External media server integration: import downloaded chapters via REST API."""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass

_log = logging.getLogger("integrations")

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class ExternalServerConfig:
    url: str = ""
    api_key: str = ""
    library_id: str = ""


def _headers(config: ExternalServerConfig) -> dict:
    return {
        "X-Api-Key": config.api_key,
        "Accept": "application/json",
    }


def _base_url(config: ExternalServerConfig) -> str:
    return config.url.rstrip("/")


def find_or_create_series(config: ExternalServerConfig, series_title: str) -> str | None:
    """Find a series by title in the external server, or create it. Returns series ID."""
    if not HAS_HTTPX:
        _log.warning("httpx not installed — install with: pip install httpx")
        return None
    try:
        r = httpx.get(
            f"{_base_url(config)}/api/v2/series",
            params={"search": series_title},
            headers=_headers(config),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("content"):
            return data["content"][0]["id"]

        r2 = httpx.post(
            f"{_base_url(config)}/api/v2/series",
            json={"libraryId": config.library_id, "name": series_title},
            headers=_headers(config),
            timeout=10,
        )
        if r2.is_success:
            return r2.json().get("id")
        _log.warning(f"Failed to create series {series_title}: {r2.status_code}")
        return None
    except Exception as e:
        _log.warning(f"Series lookup failed: {e}")
        return None


def upload_chapter(config: ExternalServerConfig, series_id: str, filepath: str) -> bool:
    """Upload a CBZ/ZIP file to an external server series."""
    if not HAS_HTTPX:
        _log.warning("httpx not installed")
        return False
    if not os.path.exists(filepath):
        _log.warning(f"File not found: {filepath}")
        return False
    try:
        with open(filepath, "rb") as f:
            r = httpx.post(
                f"{_base_url(config)}/api/v2/series/{series_id}/files",
                files={"file": (os.path.basename(filepath), f, "application/octet-stream")},
                headers=_headers(config),
                timeout=120,
            )
        if r.is_success:
            _log.info(f"Uploaded {os.path.basename(filepath)}")
            return True
        _log.warning(f"Upload failed: {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        _log.warning(f"Upload error: {e}")
        return False


def import_chapter(config: ExternalServerConfig, filepath: str, series_title: str) -> bool:
    """Import a downloaded chapter into external server: find/create series, upload file."""
    if not config.url or not config.api_key:
        return False
    series_id = find_or_create_series(config, series_title)
    if not series_id:
        return False
    return upload_chapter(config, series_id, filepath)

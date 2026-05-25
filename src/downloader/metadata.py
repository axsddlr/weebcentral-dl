"""Extract series metadata (title, description, authors, tags)."""
import re
import html
from src.logging_utils import logger
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL


class MetadataExtractor:
    def __init__(self, http: HttpClient):
        self.http = http

    def get_series_metadata(self, series_id: str) -> dict:
        url = f"{WEEBCENTRAL_URL}/series/{series_id}"
        metadata = {
            "title": "", "description": "", "authors": [], "tags": [],
            "coverUrl": None, "status": "", "type": "",
            "anime_adaptation": False, "official_translation": False, "adult": False,
        }
        try:
            resp = self.http.request("GET", url)
            text = resp.text
            if "<h1" not in text and "series/index" in text.lower():
                logger.warning(
                    f"Series page for {series_id} returned unexpected content "
                    f"(possible captcha or redirect). "
                    f"First 200 chars: {text[:200]}"
                )
                return metadata
            metadata.update(self._parse_metadata(text))
            metadata["coverUrl"] = self._extract_cover_url(text)
            metadata.update(self._parse_series_info(text))
        except Exception as e:
            logger.warning(f"Could not extract metadata for series_id {series_id}: {type(e).__name__}: {e}")
        return metadata

    @staticmethod
    def _parse_metadata(text: str) -> dict:
        result = {}
        title_match = re.search(r"<h1[^>]*>([^<]+)</h1>", text)
        result["title"] = html.unescape(title_match.group(1).strip()) if title_match else ""

        desc_match = re.search(
            r'<strong[^>]*>[^<]*Description[^<]*</strong>\s*\+?\s*<p[^>]*>([^<]+)</p>',
            text, re.IGNORECASE
        )
        result["description"] = html.unescape(desc_match.group(1).strip()) if desc_match else ""

        author_section = re.search(
            r'<strong[^>]*>[^<]*Author[^<]*</strong>(.*?)(?=<strong|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if author_section:
            result["authors"] = [html.unescape(a.strip())
                for a in re.findall(r'<a[^>]*>([^<]+)</a>', author_section.group(1))]

        tags_section = re.search(
            r'<strong[^>]*>[^<]*Tags[^<]*</strong>(.*?)(?=<strong|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if tags_section:
            result["tags"] = [html.unescape(t.strip())
                for t in re.findall(r'<a[^>]*>([^<]+)</a>', tags_section.group(1))]

        return result

    @staticmethod
    def _parse_series_info(text: str) -> dict:
        result = {}
        status_m = re.search(
            r'<strong[^>]*>[^<]*Status[^<]*</strong>\s*<[^>]*>([^<]+)</',
            text, re.IGNORECASE
        )
        if status_m:
            result["status"] = status_m.group(1).strip().lower()

        type_m = re.search(
            r'<strong[^>]*>[^<]*Type[^<]*</strong>\s*<[^>]*>([^<]+)</',
            text, re.IGNORECASE
        )
        if type_m:
            result["type"] = type_m.group(1).strip().lower()

        for flag, label in [("anime_adaptation", "Anime"), ("official_translation", "Official"), ("adult", "Adult")]:
            if re.search(rf'<strong[^>]*>[^<]*{label}[^<]*</strong>\s*<[^>]*>\s*Yes\s*<', text, re.IGNORECASE):
                result[flag] = True

        return result

    @staticmethod
    def _extract_cover_url(text: str) -> str | None:
        m = re.search(r'<source srcset="([^"]+)"', text)
        return m.group(1) if m else None

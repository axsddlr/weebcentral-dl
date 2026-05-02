"""Resolve series titles, with optional English-name fallback."""
import re
import html
from loguru import logger
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL
from src.utils import sanitize_title


class TitleResolver:
    def __init__(self, http: HttpClient, use_english_title: bool = False):
        self.http = http
        self.use_english_title = use_english_title

    def get_series_title_by_id(self, series_id: str) -> str:
        url = f"{WEEBCENTRAL_URL}/series/{series_id}"
        try:
            resp = self.http.request("GET", url)
            m = re.search(r"<h1[^>]*>([^<]+)</h1>", resp.text)
            if m:
                title = html.unescape(m.group(1).strip())
                if self.use_english_title:
                    title = self._resolve_english_title(title, resp.text)
                return sanitize_title(title)
        except Exception as e:
            logger.warning(f"Could not fetch manga title for series_id {series_id}: {e}")
        return series_id

    @staticmethod
    def _is_romaji(title: str) -> bool:
        return bool(re.search(r'\b(de|wo|ga|no|ni|wa)\b', title, re.IGNORECASE))

    @staticmethod
    def _resolve_english_title(h1_title: str, html_text: str) -> str:
        if not TitleResolver._is_romaji(h1_title):
            return h1_title
        assoc_pattern = r'Associated Name\(s\).*?<ul[^>]*>(.*?)</ul>'
        assoc_match = re.search(assoc_pattern, html_text, re.DOTALL | re.IGNORECASE)
        if assoc_match:
            li_items = re.findall(r'<li>([^<]+)</li>', assoc_match.group(1))
            if li_items:
                logger.debug(f"Using Associated Name: {li_items[0]}")
                return html.unescape(li_items[0].strip())
        return h1_title

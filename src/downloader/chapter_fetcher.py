"""Fetch chapter lists from WeebCentral (JSON API + HTML fallback)."""
import re
from typing import List, Tuple
from loguru import logger
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL


class ChapterFetcher:
    def __init__(self, http: HttpClient):
        self.http = http

    def fetch_chapter_list(self, series_id: str) -> List[Tuple[str, str, str]]:
        series_id = series_id.upper()
        url = f"{WEEBCENTRAL_URL}/series/{series_id}/full-chapter-list"
        try:
            resp = self.http.request("GET", url)
        except Exception as e:
            logger.error(
                f"Network error fetching chapter list for {series_id}: {type(e).__name__}: {e}. "
                f"All retries exhausted."
            )
            return []

        chapters = self._parse_chapter_data(resp)
        if not chapters:
            logger.warning(f"No chapters found for {series_id} (series may have no chapters published)")
        return chapters

    def _parse_chapter_data(self, resp) -> List[Tuple[str, str, str]]:

    @staticmethod
    def _parse_json_response(data: dict) -> list:
        chapters = []
        for chap in data.get("chapters", []):
            title = chap.get("title", "")
            match = re.search(r'([A-Za-z#]+)\s*([\d\.]+)', title)
            if match:
                chap_type = match.group(1).strip()
                chap_num = match.group(2)
                chap_url = chap.get("url", "")
                chap_id_match = re.search(r'/chapters/([A-Z0-9]+)', chap_url)
                if chap_id_match:
                    chapters.append((chap_type, chap_num, chap_id_match.group(1)))
        return chapters

    @staticmethod
    def _parse_html_response(html: str) -> list:
        pattern = re.compile(
            r'<span class="">([A-Za-z#]+)\s*([\d\.]+)</span>[\s\S]*?value="([A-Z0-9]+)"'
        )
        return [
            (m.group(1).strip(), m.group(2), m.group(3))
            for m in pattern.finditer(html)
        ]

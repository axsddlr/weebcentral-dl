"""Search WeebCentral and resolve series IDs."""
import re
from urllib.parse import quote_plus
from typing import Optional, Tuple
from loguru import logger
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL
from src.downloader.title_resolver import TitleResolver
from src.utils import sanitize_title


class SeriesResolver:
    def __init__(self, http: HttpClient, title_resolver: TitleResolver, use_english_title: bool = False):
        self.http = http
        self.title_resolver = title_resolver
        self.use_english_title = use_english_title

    def get_series_id_from_query(self, query: str) -> Optional[Tuple[str, str]]:
        encoded = quote_plus(query)
        url = f"{WEEBCENTRAL_URL}/search/data?author=&text={encoded}&sort=Best%20Match&order=Descending&official=Any&anime=Any&adult=Any&display_mode=Full%20Display"
        try:
            resp = self.http.request("GET", url)
        except Exception as e:
            logger.error(
                f"Network error searching for '{query}': {type(e).__name__}: {e}. "
                f"All retries exhausted."
            )
            return None, None

        results = re.findall(r'/series/([^"/]+/[^"]+)', resp.text)
        if not results:
            msg = f"NOT FOUND: {query}"
            logger.warning(msg)
            self.http.log_not_found(msg)
            return None, None

        unique_results = sorted(list(set(results)))
        if not unique_results:
            msg = f"NO UNIQUE LINKS: {query}"
            logger.warning(msg)
            self.http.log_not_found(msg)
            return None, None

        if len(unique_results) > 1:
            msg = f"MULTIPLE UNIQUE: {query} => {unique_results}"
            logger.warning(
                f"Multiple unique search results for '{query}', picking the first: {unique_results[0]}"
            )
            self.http.log_not_found(msg)

        series_id, series_title = unique_results[0].split("/")
        return series_id, series_title

    def resolve_series_info(
        self, title: Optional[str], series_id: Optional[str]
    ) -> Optional[Tuple[str, str]]:
        if series_id and title:
            series_id = series_id.strip()
            if self.use_english_title:
                series_title = self.title_resolver.get_series_title_by_id(series_id)
            else:
                series_title = sanitize_title(title.strip())
            logger.info(f"Processing series id: {series_id} (title: {series_title})")
            return series_id, series_title

        elif series_id:
            series_id = series_id.strip()
            series_title = self.title_resolver.get_series_title_by_id(series_id)
            logger.info(f"Processing series id: {series_id} (title: {series_title})")
            return series_id, series_title

        elif title:
            search_title = title.replace("-", " ").strip()
            result = self.get_series_id_from_query(search_title)
            if not result or not result[0]:
                logger.warning(f"Skipping '{title}': not found.")
                return None
            series_id, series_title = result
            if self.use_english_title:
                series_title = self.title_resolver.get_series_title_by_id(series_id)
            return series_id, series_title

        else:
            logger.error("No title or series_id provided.")
            return None

"""HTTP transport layer for WeebCentral API calls."""
import os
import time
import json as _json
from typing import Any
from scrapling.fetchers import StealthyFetcher
from src.logging_utils import logger

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
WEEBCENTRAL_URL = "https://weebcentral.com"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


class _Response:
    """Adapts scrapling Response to the requests-like interface callers expect."""
    def __init__(self, page):
        self._page = page
        self.status_code = getattr(page, "status", 200)

    @property
    def text(self) -> str:
        return self._page.html_content

    @property
    def content(self) -> bytes:
        return self._page.body

    def json(self) -> Any:
        return _json.loads(self._page.html_content)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}")


class HttpClient:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def request(self, method: str, url: str, **kwargs: Any) -> _Response:
        timeout = kwargs.pop("timeout", 30)
        extra_headers = kwargs.pop("headers", {})

        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                page = StealthyFetcher.fetch(
                    url,
                    headless=True,
                    disable_resources=True,
                    extra_headers=extra_headers,
                    timeout=timeout * 1000,
                )
                resp = _Response(page)
                resp.raise_for_status()
                return resp
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    raise
                last_exc = e
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(
                        f"HTTP {method} {url} failed (attempt {attempt}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)
        raise last_exc

    def log_not_found(self, msg: str):
        try:
            logfile = os.path.join(self.output_dir, "not_found.log")
            with open(logfile, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception as e:
            logger.warning(f"Could not write to not_found.log: {e}")

    def reset_scraper(self):
        pass  # StealthyFetcher is stateless; nothing to reset

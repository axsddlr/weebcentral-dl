"""HTTP transport layer for WeebCentral API calls."""
import os
import time
import cloudscraper
from typing import Any
from src.logging_utils import logger

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
WEEBCENTRAL_URL = "https://weebcentral.com"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


class HttpClient:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "HX-Request": "true",
        })

    def request(self, method: str, url: str, **kwargs: Any):
        if "timeout" not in kwargs:
            kwargs["timeout"] = 30

        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.scraper.request(method, url, **kwargs)
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
                    self.reset_scraper()
        raise last_exc

    def log_not_found(self, msg: str):
        try:
            logfile = os.path.join(self.output_dir, "not_found.log")
            with open(logfile, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception as e:
            logger.warning(f"Could not write to not_found.log: {e}")

    def reset_scraper(self):
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "HX-Request": "true",
        })

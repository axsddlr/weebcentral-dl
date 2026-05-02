"""HTTP transport layer for WeebCentral API calls."""
import os
import cloudscraper
from typing import Any
from loguru import logger

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
WEEBCENTRAL_URL = "https://weebcentral.com"


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
        resp = self.scraper.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp

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

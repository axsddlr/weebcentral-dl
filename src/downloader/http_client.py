"""HTTP transport layer for WeebCentral API calls."""
import os
import time
import json as _json
import threading
from typing import Any
from scrapling.fetchers import StealthySession
from src.logging_utils import logger

WEEBCENTRAL_URL = "https://weebcentral.com"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0
CF_TIMEOUT_MS = 60_000   # CF solver needs >= 60s
DEFAULT_TIMEOUT_MS = 30_000


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
    """
    Shared StealthySession per thread — keeps the browser alive across requests,
    avoiding per-call browser launch overhead.
    """
    _local = threading.local()

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def _get_session(self) -> StealthySession:
        if not getattr(self._local, "session", None):
            self._local.session = StealthySession(
                headless=True,
                disable_resources=True,
                solve_cloudflare=True,
                block_webrtc=True,
            )
            self._local.session.start()
        return self._local.session

    def request(self, method: str, url: str, **kwargs: Any) -> _Response:
        timeout = kwargs.pop("timeout", 30)
        extra_headers = kwargs.pop("headers", {})
        timeout_ms = max(timeout * 1000, CF_TIMEOUT_MS)

        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                session = self._get_session()
                page = session.fetch(
                    url,
                    extra_headers=extra_headers,
                    timeout=timeout_ms,
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
                    self._reset_session()
        raise last_exc

    def _reset_session(self):
        session = getattr(self._local, "session", None)
        if session:
            try:
                session.close()
            except Exception:
                pass
        self._local.session = None

    def log_not_found(self, msg: str):
        try:
            logfile = os.path.join(self.output_dir, "not_found.log")
            with open(logfile, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception as e:
            logger.warning(f"Could not write to not_found.log: {e}")

    def reset_scraper(self):
        self._reset_session()

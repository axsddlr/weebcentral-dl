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

# disable_resources=False is MANDATORY here, not a speed/quality trade-off.
#
# The chapter image-list partial
# (/chapters/{ID}/images?is_prev=False&current_page=1&reading_style=long_strip)
# renders ~49 <img> tags, each carrying
#     onerror="this.src='/static/images/broken_image.jpg'"
# With disable_resources=True the browser blocks every image fetch, the page's own
# onerror handler fires for all of them, and scrapling serialises the *mutated*
# DOM. Measured on that exact URL with the same headers:
#     disable_resources=True  ->  49 placeholder srcs,  0 real image URLs
#     disable_resources=False ->   0 placeholders,     49 real CDN URLs
# (e.g. https://hot.planeptune.us/manga/Solo-Leveling/0200-001.png ... -049.png.)
# The placeholder resolves to a real 62 KB JPEG, so the damage is silent: the
# chapter would "download" 49 copies of the site's broken-image graphic.
#
# Do NOT re-enable the flag for speed. One resource-loading session is not the
# slow path: the image-list fetch measured 982 ms through this single session
# versus 4165 ms through the former dual-session design, which paid for a second
# browser launch plus a failed attempt and a retry.


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
    One shared StealthySession per thread — keeps the browser alive across
    requests, avoiding per-call browser launch overhead.

    Every request in a thread goes through that same session, configured with
    ``disable_resources=False`` (see the module comment above): the DOM of the
    chapter image-list partial must survive intact, and a second session is
    neither needed nor safe (the per-request resource policy broke sequential
    downloads with "Context manager has been closed").
    """
    _local = threading.local()

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def _get_session(self) -> StealthySession:
        """This thread's single session, created and started on first use."""
        if not getattr(self._local, "session", None):
            self._local.session = StealthySession(
                headless=True,
                disable_resources=False,   # mandatory: see the module comment above
                solve_cloudflare=True,
                block_webrtc=True,
            )
            self._local.session.start()
        return self._local.session

    def request(self, method: str, url: str, retries: int = MAX_RETRIES,
                **kwargs: Any) -> _Response:
        timeout = kwargs.pop("timeout", 30)
        extra_headers = kwargs.pop("headers", {})
        timeout_ms = max(timeout * 1000, CF_TIMEOUT_MS)
        attempts = max(1, int(retries))

        last_exc = None
        for attempt in range(1, attempts + 1):
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
                if attempt < attempts:
                    wait = RETRY_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(
                        f"HTTP {method} {url} failed (attempt {attempt}/{attempts}): {e}. "
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

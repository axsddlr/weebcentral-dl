#!/usr/bin/env python3
"""
Focused unit tests for ImageDownloader.download_image.

These tests never touch the network, never launch a browser and never use the
real HttpClient. A hand-written stub stands in for the HTTP transport so the
exact request shape and the retry behaviour can be asserted.

Run with: python -m unittest -v test_image_downloader.py
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from src.downloader.image_downloader import ImageDownloader


class ConnectionRefusedError_(Exception):
    """Stands in for a transport-level connection failure."""


class StubResponse:
    """Minimal stand-in for the real HttpClient response object."""

    def __init__(self, content: bytes = b"", text: str = "", status_code: int = 200):
        self.content = content
        self.text = text
        self.status_code = status_code
        self.raise_for_status_calls = 0

    def raise_for_status(self):
        self.raise_for_status_calls += 1
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}")


class StubHttpClient:
    """Records request(...) calls; optionally raises instead of responding."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []
        self.reset_calls = 0

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.error is not None:
            raise self.error
        return self.response

    def reset_scraper(self):
        self.reset_calls += 1


class StubJsonResponse:
    """Response stub exposing only the json()/text surface _extract_image_urls uses."""

    def __init__(self, json_value=None, json_error=None, text=""):
        self._json_value = json_value
        self._json_error = json_error
        self.text = text

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._json_value


class StubChapterHttpClient:
    """Serves the chapter image-list request and records every page request."""

    LIST_MARKER = "reading_style=long_strip"

    def __init__(self, image_urls, failing_urls=(), list_error=None):
        self.image_urls = list(image_urls)
        self.failing_urls = set(failing_urls)
        self.list_error = list_error
        self.calls = []
        self.reset_calls = 0

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.LIST_MARKER in url:
            if self.list_error is not None:
                raise self.list_error
            return StubJsonResponse(
                json_value={"images": [{"src": u} for u in self.image_urls]}
            )
        if url in self.failing_urls:
            raise ConnectionRefusedError_("connection refused by peer")
        return StubResponse(content=b"page-bytes", text="")

    def reset_scraper(self):
        self.reset_calls += 1


class TestDownloadImage(unittest.TestCase):
    """download_image() must go through HttpClient.request and write its bytes."""

    URL = "https://weebcentral.com/chapters/01ABC/images/001.jpg?is_prev=False&current_page=1"
    REFERER = "https://weebcentral.com/chapters/01ABC/images?is_prev=False&current_page=1"
    PAYLOAD = b"\xff\xd8\xff\xe0fake-jpeg-payload"

    def test_download_image_writes_response_content_to_disk(self):
        """GET via the HTTP client, strip the query string, write resp.content."""
        http = StubHttpClient(response=StubResponse(content=self.PAYLOAD, text="<html></html>"))
        downloader = ImageDownloader(http)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = downloader.download_image(self.URL, tmpdir, self.REFERER)

            expected_path = os.path.join(tmpdir, "001.jpg")
            self.assertIsNotNone(out_path)
            self.assertEqual(out_path, expected_path)
            self.assertTrue(os.path.exists(expected_path))
            with open(expected_path, "rb") as fh:
                self.assertEqual(fh.read(), self.PAYLOAD)

        # Exactly one request, of the exact shape the real client expects.
        self.assertEqual(len(http.calls), 1)
        method, called_url, kwargs = http.calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(called_url, self.URL)
        self.assertEqual(kwargs.get("headers"), {"Referer": self.REFERER})
        # Only headers (plus an optional timeout/retry budget) may be forwarded.
        self.assertLessEqual(set(kwargs), {"headers", "timeout", "retries"})
        self.assertNotIn("stream", kwargs)
        self.assertEqual(http.response.raise_for_status_calls, 1)

    def test_download_image_returns_none_when_url_has_no_filename(self):
        """A URL whose basename is empty must return None and write nothing."""
        url = "https://weebcentral.com/chapters/01ABC/images/?"
        http = StubHttpClient(response=StubResponse(content=self.PAYLOAD, text=""))
        downloader = ImageDownloader(http)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = downloader.download_image(url, tmpdir, self.REFERER)
            self.assertIsNone(result)
            self.assertEqual(os.listdir(tmpdir), [])

    def test_download_image_retries_connection_errors_then_gives_up(self):
        """Connection errors retry max_retries times, reset the scraper, then return None."""
        http = StubHttpClient(error=ConnectionRefusedError_("connection refused by peer"))
        downloader = ImageDownloader(http, max_retries=3, max_sleep=1)

        with tempfile.TemporaryDirectory() as tmpdir, \
                patch("src.downloader.image_downloader.time.sleep") as sleep_mock, \
                patch("src.downloader.image_downloader.random.randint", return_value=0):
            result = downloader.download_image(self.URL, tmpdir, self.REFERER)
            self.assertEqual(os.listdir(tmpdir), [])

        self.assertIsNone(result)
        self.assertEqual(len(http.calls), 3)
        self.assertEqual(http.reset_calls, 3)
        # The sleep was requested but never really performed.
        self.assertEqual(sleep_mock.call_count, 3)
        self.assertTrue(all(call.args[0] == 0 for call in sleep_mock.call_args_list))

    def test_download_image_tolerates_max_sleep_below_the_backoff_floor(self):
        """max_sleep < 15 must not blow up randint inside the exception handler."""
        http = StubHttpClient(error=ConnectionRefusedError_("connection refused by peer"))
        downloader = ImageDownloader(http, max_retries=2, max_sleep=1)

        with tempfile.TemporaryDirectory() as tmpdir, \
                patch("src.downloader.image_downloader.time.sleep") as sleep_mock:
            result = downloader.download_image(self.URL, tmpdir, self.REFERER)

        self.assertIsNone(result)
        self.assertEqual(http.reset_calls, 2)
        self.assertEqual(sleep_mock.call_count, 2)
        # The 15s floor wins over the too-small configured maximum.
        self.assertTrue(all(call.args[0] == 15 for call in sleep_mock.call_args_list))

    def test_download_image_retries_modern_transport_errors(self):
        """A Playwright-style net::ERR_CONNECTION_REFUSED must consume the retry budget."""
        http = StubHttpClient(error=Exception("net::ERR_CONNECTION_REFUSED at https://cdn/p1.jpg"))
        downloader = ImageDownloader(http, max_retries=4, max_sleep=1)

        with tempfile.TemporaryDirectory() as tmpdir, \
                patch("src.downloader.image_downloader.time.sleep") as sleep_mock, \
                patch("src.downloader.image_downloader.random.randint", return_value=0):
            result = downloader.download_image(self.URL, tmpdir, self.REFERER)

        self.assertIsNone(result)
        self.assertEqual(len(http.calls), 4)
        self.assertEqual(http.reset_calls, 4)
        self.assertEqual(sleep_mock.call_count, 4)

    def test_connection_error_markers_cover_legacy_and_modern_shapes(self):
        """Every known transport-error shape must trigger the outer retry loop."""
        markers = [
            "beacon",
            "connection refused",
            "max retries exceeded",
            "connection reset",
            "err_connection",
            "net::",
            "timeout",
            "timed out",
            "failed to fetch",
            "target closed",
        ]
        for marker in markers:
            with self.subTest(marker=marker):
                http = StubHttpClient(error=Exception(f"boom: {marker}"))
                downloader = ImageDownloader(http, max_retries=2, max_sleep=1)
                with tempfile.TemporaryDirectory() as tmpdir, \
                        patch("src.downloader.image_downloader.time.sleep"), \
                        patch("src.downloader.image_downloader.random.randint", return_value=0):
                    downloader.download_image(self.URL, tmpdir, self.REFERER)
                self.assertEqual(
                    len(http.calls), 2, f"{marker!r} must trigger another attempt"
                )

    def test_connection_error_marker_list_is_a_module_constant(self):
        """The markers live in a greppable module-level constant."""
        from src.downloader import image_downloader as module

        markers = getattr(module, "CONNECTION_ERROR_MARKERS", None)
        self.assertIsNotNone(
            markers, "connection-error markers must live in a module constant"
        )
        for expected in (
            "beacon",
            "connection refused",
            "max retries exceeded",
            "connection reset",
            "err_connection",
            "net::",
            "timeout",
            "timed out",
            "failed to fetch",
            "target closed",
        ):
            self.assertIn(expected, markers)

    def test_download_image_forwards_a_single_attempt_budget(self):
        """The outer loop owns the retry budget, so HttpClient gets retries=1."""
        http = StubHttpClient(response=StubResponse(content=self.PAYLOAD, text=""))
        downloader = ImageDownloader(http, max_retries=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = downloader.download_image(self.URL, tmpdir, self.REFERER)

        self.assertIsNotNone(out_path)
        self.assertEqual(len(http.calls), 1)
        self.assertEqual(http.calls[0][2].get("retries"), 1)

    def test_download_image_logs_the_exception_type_at_error_level(self):
        """A swallowed failure must be loud: error level, naming the exception type."""
        http = StubHttpClient(error=ConnectionRefusedError_("connection refused by peer"))
        downloader = ImageDownloader(http, max_retries=2, max_sleep=1)

        with tempfile.TemporaryDirectory() as tmpdir, \
                patch("src.downloader.image_downloader.logger") as logger_mock, \
                patch("src.downloader.image_downloader.time.sleep"), \
                patch("src.downloader.image_downloader.random.randint", return_value=0):
            result = downloader.download_image(self.URL, tmpdir, self.REFERER)

        self.assertIsNone(result)
        error_messages = [str(call.args[0]) for call in logger_mock.error.call_args_list]
        self.assertTrue(
            any("ConnectionRefusedError_" in m and self.URL in m for m in error_messages),
            f"expected an error log naming the exception type and URL, got {error_messages}",
        )
        debug_messages = [str(call.args[0]) for call in logger_mock.debug.call_args_list]
        self.assertFalse(
            any("Error downloading" in m for m in debug_messages),
            f"the download failure must not be swallowed at debug level, got {debug_messages}",
        )


class TestExtractImageUrls(unittest.TestCase):
    """_extract_image_urls must fall back to HTML for any malformed JSON body."""

    def test_json_list_body_falls_back_to_html(self):
        resp = StubJsonResponse(
            json_value=[{"src": "https://cdn/from-json.jpg"}],
            text='<img src="https://cdn/from-html.jpg">',
        )
        self.assertEqual(
            ImageDownloader._extract_image_urls(resp), ["https://cdn/from-html.jpg"]
        )

    def test_json_string_body_falls_back_to_html(self):
        resp = StubJsonResponse(
            json_value="not-a-dict", text='<img src="https://cdn/from-html.png">'
        )
        self.assertEqual(
            ImageDownloader._extract_image_urls(resp), ["https://cdn/from-html.png"]
        )

    def test_json_error_falls_back_to_html(self):
        resp = StubJsonResponse(
            json_error=ValueError("no json body"), text='<img src="https://cdn/p1.jpg">'
        )
        self.assertEqual(ImageDownloader._extract_image_urls(resp), ["https://cdn/p1.jpg"])

    def test_well_formed_json_body_still_wins(self):
        resp = StubJsonResponse(
            json_value={"images": [{"src": "https://cdn/from-json.jpg"}]},
            text='<img src="https://cdn/from-html.jpg">',
        )
        self.assertEqual(
            ImageDownloader._extract_image_urls(resp), ["https://cdn/from-json.jpg"]
        )


class TestHtmlImageFallback(unittest.TestCase):
    """The HTML fallback must return page images, not scripts and trackers."""

    MIXED_PAGE = (
        '<html><head><script src="/static/app.js"></script></head><body>'
        '<img src="https://cdn/p1.jpg">'
        '<iframe src="https://ads/track"></iframe>'
        '<img src="https://cdn/p2.PNG?token=abc">'
        '<img src="https://cdn/p3.gif#page">'
        "</body></html>"
    )

    def _fallback(self, text):
        return ImageDownloader._extract_image_urls(
            StubJsonResponse(json_error=ValueError("no json body"), text=text)
        )

    def test_prefers_image_extensions_over_scripts_and_trackers(self):
        self.assertEqual(
            self._fallback(self.MIXED_PAGE),
            [
                "https://cdn/p1.jpg",
                "https://cdn/p2.PNG?token=abc",
                "https://cdn/p3.gif#page",
            ],
        )

    def test_recognises_every_image_extension_case_insensitively(self):
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".JPG", ".WebP"):
            with self.subTest(ext=ext):
                url = f"https://cdn/page{ext}?q=1"
                self.assertEqual(self._fallback(f'<img src="{url}">'), [url])

    def test_keeps_extensionless_urls_when_no_image_extension_exists(self):
        page = '<script src="/static/app.js"></script><img src="https://cdn/image?id=123">'
        self.assertEqual(
            self._fallback(page), ["/static/app.js", "https://cdn/image?id=123"]
        )

    def test_deduplicates_while_preserving_order(self):
        page = (
            '<img src="https://cdn/p1.jpg">'
            '<img src="/static/app.js">'
            '<img src="https://cdn/p1.jpg">'
        )
        self.assertEqual(self._fallback(page), ["https://cdn/p1.jpg"])


class TestDownloadChapterImages(unittest.TestCase):
    """download_chapter_images must report pages that never made it to disk."""

    CHAPTER_ID = "01ABC"
    CHAPTER_NUM = "7"
    OK_URL = "https://cdn/p1.jpg"
    BAD_URL = "https://cdn/p2.jpg"
    DIR_NAME = "vol_007"

    def _download(self, http, tmpdir, sequence):
        downloader = ImageDownloader(http, max_retries=1, max_sleep=1, sequence=sequence)
        with patch("src.downloader.image_downloader.time.sleep"), \
                patch("src.downloader.image_downloader.random.randint", return_value=0):
            return downloader.download_chapter_images(
                self.CHAPTER_ID, self.CHAPTER_NUM, tmpdir, self.DIR_NAME
            )

    def test_returns_none_and_logs_error_when_every_page_fails(self):
        for sequence in (True, False):
            with self.subTest(sequence=sequence):
                http = StubChapterHttpClient([self.OK_URL], failing_urls=[self.OK_URL])
                with tempfile.TemporaryDirectory() as tmpdir, \
                        patch("src.downloader.image_downloader.logger") as logger_mock:
                    result = self._download(http, tmpdir, sequence)

                self.assertIsNone(result)
                messages = [str(call.args[0]) for call in logger_mock.error.call_args_list]
                self.assertTrue(
                    any(
                        "All 1" in m and f"chapter {self.CHAPTER_NUM}" in m and "failed" in m
                        for m in messages
                    ),
                    f"expected a chapter-level error naming the chapter and count, got {messages}",
                )

    def test_returns_chapter_dir_when_every_page_succeeds(self):
        for sequence in (True, False):
            with self.subTest(sequence=sequence):
                http = StubChapterHttpClient([self.OK_URL])
                with tempfile.TemporaryDirectory() as tmpdir, \
                        patch("src.downloader.image_downloader.logger") as logger_mock:
                    result = self._download(http, tmpdir, sequence)

                    self.assertEqual(result, os.path.join(tmpdir, self.DIR_NAME))
                    self.assertEqual(sorted(os.listdir(result)), ["p1.jpg"])
                    with open(os.path.join(result, "p1.jpg"), "rb") as fh:
                        self.assertEqual(fh.read(), b"page-bytes")
                self.assertEqual(logger_mock.warning.call_count, 0)

    def test_warns_and_keeps_chapter_dir_on_partial_failure(self):
        for sequence in (True, False):
            with self.subTest(sequence=sequence):
                http = StubChapterHttpClient(
                    [self.OK_URL, self.BAD_URL], failing_urls=[self.BAD_URL]
                )
                with tempfile.TemporaryDirectory() as tmpdir, \
                        patch("src.downloader.image_downloader.logger") as logger_mock:
                    result = self._download(http, tmpdir, sequence)

                    self.assertEqual(result, os.path.join(tmpdir, self.DIR_NAME))
                    self.assertEqual(sorted(os.listdir(result)), ["p1.jpg"])
                warnings = [str(c.args[0]) for c in logger_mock.warning.call_args_list]
                self.assertTrue(
                    any("1 of 2" in m and f"chapter {self.CHAPTER_NUM}" in m for m in warnings),
                    f"expected a partial-failure warning, got {warnings}",
                )

    def test_parallel_worker_exception_is_counted_not_fatal(self):
        """A raising future must be recorded as a failure, not abort the chapter."""
        http = StubChapterHttpClient([self.OK_URL, self.BAD_URL])
        downloader = ImageDownloader(http, max_retries=1, max_sleep=1)
        real_download = downloader.download_image

        def flaky(img_url, dest_folder, referer):
            if img_url == self.BAD_URL:
                raise RuntimeError("worker blew up")
            return real_download(img_url, dest_folder, referer)

        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(downloader, "download_image", side_effect=flaky), \
                patch("src.downloader.image_downloader.logger") as logger_mock:
            result = downloader.download_chapter_images(
                self.CHAPTER_ID, self.CHAPTER_NUM, tmpdir, self.DIR_NAME
            )

            self.assertEqual(result, os.path.join(tmpdir, self.DIR_NAME))
            self.assertEqual(sorted(os.listdir(result)), ["p1.jpg"])
        warnings = [str(c.args[0]) for c in logger_mock.warning.call_args_list]
        self.assertTrue(
            any("1 of 2" in m for m in warnings),
            f"expected a partial-failure warning, got {warnings}",
        )


if __name__ == "__main__":
    unittest.main()

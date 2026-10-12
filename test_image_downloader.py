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
        # Only headers (plus an optional timeout) may be forwarded.
        self.assertLessEqual(set(kwargs), {"headers", "timeout"})
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


if __name__ == "__main__":
    unittest.main()

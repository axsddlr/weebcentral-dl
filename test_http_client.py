#!/usr/bin/env python3
"""
Focused unit tests for HttpClient's session configuration and retry budget.

These tests never touch the network and never launch a browser: the session
lookup is patched to a stub whose fetch() always raises, and the session
constructor is patched to a recorder that captures its kwargs.

Run with: python -m unittest -v test_http_client.py
"""

import unittest
from unittest.mock import patch

from src.downloader.http_client import MAX_RETRIES, HttpClient


class FailingSession:
    """Stands in for StealthySession: every fetch() raises the transport error."""

    def __init__(self, error):
        self.error = error
        self.fetch_calls = []

    def fetch(self, url, **kwargs):
        self.fetch_calls.append((url, kwargs))
        raise self.error

    def close(self):
        pass


class TestHttpClientRetryBudget(unittest.TestCase):
    """request() must make exactly as many attempts as its retry budget allows."""

    URL = "https://weebcentral.com/chapters/01ABC/images"
    ERROR = "net::ERR_CONNECTION_REFUSED"

    def _request(self, **kwargs):
        session = FailingSession(RuntimeError(self.ERROR))
        client = HttpClient(".")
        with patch.object(HttpClient, "_get_session", return_value=session), \
                patch.object(HttpClient, "_reset_session") as reset_mock, \
                patch("src.downloader.http_client.time.sleep") as sleep_mock:
            with self.assertRaises(RuntimeError):
                client.request("GET", self.URL, **kwargs)
        return session, reset_mock, sleep_mock

    def test_default_budget_matches_max_retries(self):
        """With no explicit budget, request() keeps the module default of 3."""
        session, reset_mock, sleep_mock = self._request()
        self.assertEqual(MAX_RETRIES, 3)
        self.assertEqual(len(session.fetch_calls), MAX_RETRIES)
        # Reset + backoff only happen when another attempt follows.
        self.assertEqual(reset_mock.call_count, MAX_RETRIES - 1)
        self.assertEqual(sleep_mock.call_count, MAX_RETRIES - 1)

    def test_explicit_budget_is_honoured(self):
        """retries=2 means exactly two fetch() attempts, then raise."""
        session, reset_mock, sleep_mock = self._request(retries=2)
        self.assertEqual(len(session.fetch_calls), 2)
        self.assertEqual(reset_mock.call_count, 1)
        self.assertEqual(sleep_mock.call_count, 1)

    def test_budget_is_clamped_to_at_least_one_attempt(self):
        """A zero/negative budget must still try once instead of never."""
        for value in (0, -3):
            with self.subTest(retries=value):
                session, reset_mock, _ = self._request(retries=value)
                self.assertEqual(len(session.fetch_calls), 1)
                self.assertEqual(reset_mock.call_count, 0)

    def test_retries_kwarg_is_consumed_not_forwarded_to_the_session(self):
        """headers/timeout keep working; retries must not leak into fetch()."""
        session, _, _ = self._request(retries=2, headers={"HX-Request": "true"}, timeout=30)
        self.assertTrue(session.fetch_calls)
        for _url, kwargs in session.fetch_calls:
            self.assertEqual(kwargs.get("extra_headers"), {"HX-Request": "true"})
            self.assertNotIn("retries", kwargs)

    def test_successful_request_makes_a_single_attempt(self):
        class OkSession:
            def __init__(self):
                self.fetch_calls = 0

            def fetch(self, url, **kwargs):
                self.fetch_calls += 1
                return type("Page", (), {"status": 200, "html_content": "<html></html>",
                                         "body": b"payload"})()

        session = OkSession()
        client = HttpClient(".")
        with patch.object(HttpClient, "_get_session", return_value=session), \
                patch.object(HttpClient, "_reset_session") as reset_mock:
            resp = client.request("GET", self.URL, retries=3)
        self.assertEqual(resp.content, b"payload")
        self.assertEqual(session.fetch_calls, 1)
        self.assertEqual(reset_mock.call_count, 0)


class RecordingSession:
    """Stands in for scrapling's StealthySession without launching a browser.

    Records the constructor kwargs so the session's resource policy can be
    asserted directly, and records every ``fetch`` call.
    """

    instances: list = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.started = False
        self.closed = False
        self.fetch_calls = []
        RecordingSession.instances.append(self)

    def start(self):
        self.started = True

    def close(self):
        self.closed = True

    def fetch(self, url, **kwargs):
        self.fetch_calls.append((url, kwargs))
        return type(
            "Page", (), {"status": 200, "html_content": "<html></html>", "body": b"ok"}
        )()


class FailingRecordingSession(RecordingSession):
    """A recording session whose every fetch fails with a transport error."""

    def fetch(self, url, **kwargs):
        self.fetch_calls.append((url, kwargs))
        raise RuntimeError("net::ERR_CONNECTION_REFUSED")


class TestHttpClientSessionConfiguration(unittest.TestCase):
    """There is exactly one session per thread, and it must load resources.

    ``test_session_is_built_with_resources_enabled`` is the regression assertion
    that would have caught the original defect: with disable_resources=True the
    chapter image-list partial's own onerror handler rewrites all 49 page image
    srcs to the site placeholder, so the scraper sees 0 real URLs. A second
    per-request "resource session" is deliberately NOT the fix any more — that
    arrangement broke sequential downloads ("Context manager has been closed"),
    so this suite also pins that no second session and no per-request policy
    flag exist.
    """

    SERIES_URL = "https://weebcentral.com/series/01J76XYCPSY3C4BNPBRY8JMCBE"
    IMAGE_LIST_URL = (
        "https://weebcentral.com/chapters/01ABC/images"
        "?is_prev=False&current_page=1&reading_style=long_strip"
    )
    EXPECTED_KWARGS = {
        "headless": True,
        "disable_resources": False,
        "solve_cloudflare": True,
        "block_webrtc": True,
    }

    def setUp(self):
        self.client = HttpClient(".")
        self.client.reset_scraper()  # drop anything an earlier test left in this thread
        RecordingSession.instances.clear()
        patcher = patch("src.downloader.http_client.StealthySession", RecordingSession)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Runs before patcher.stop() (cleanups are LIFO): reset while still patched.
        self.addCleanup(self.client.reset_scraper)

    def _sessions(self):
        return RecordingSession.instances

    def test_session_is_built_with_resources_enabled(self):
        """The one explicit regression assertion: disable_resources must be False.

        Resources cannot be disabled anywhere in the stack. If this test is ever
        "fixed" by flipping the flag, chapter downloads silently archive the
        site's broken-image placeholder instead of the pages.
        """
        self.client.request("GET", self.SERIES_URL)

        self.assertEqual(len(self._sessions()), 1)
        session = self._sessions()[0]
        self.assertIs(
            session.kwargs.get("disable_resources"),
            False,
            "with disable_resources=True every <img> fetch is blocked, the page's "
            "onerror fires, and the 49 real page URLs become 49 placeholders",
        )
        # Everything else about the stealth configuration is unchanged.
        self.assertEqual(session.kwargs, self.EXPECTED_KWARGS)
        self.assertTrue(session.started, "the session must be started on first use")
        self.assertEqual(len(session.fetch_calls), 1)

    def test_chapter_image_list_url_uses_that_same_session(self):
        """The image-list partial gets the resource-loading session, as one session."""
        self.client.request("GET", self.IMAGE_LIST_URL, headers={"HX-Request": "true"})

        self.assertEqual(len(self._sessions()), 1)
        self.assertEqual(self._sessions()[0].kwargs, self.EXPECTED_KWARGS)

    def test_second_request_in_the_same_thread_reuses_the_session_object(self):
        """Identity, not just count: reuse must not rebuild the browser."""
        self.client.request("GET", self.SERIES_URL)
        first = self._sessions()[0]
        self.client.request("GET", self.IMAGE_LIST_URL, headers={"HX-Request": "true"})

        self.assertEqual(len(self._sessions()), 1, "one thread must own one session")
        self.assertIs(self._sessions()[0], first)
        self.assertEqual(len(first.fetch_calls), 2)
        self.assertFalse(first.closed)

    def test_reset_scraper_closes_and_clears_the_session(self):
        self.client.request("GET", self.SERIES_URL)
        first = self._sessions()[0]
        self.assertFalse(first.closed)

        self.client.reset_scraper()

        self.assertTrue(first.closed, "reset_scraper must close the session")
        self.assertIsNone(
            getattr(self.client._local, "session", None),
            "reset_scraper must clear the thread-local so it rebuilds",
        )

        self.client.request("GET", self.SERIES_URL)
        self.assertEqual(len(self._sessions()), 2, "reset must force a rebuild")
        rebuilt = self._sessions()[1]
        self.assertIsNot(rebuilt, first)
        self.assertTrue(rebuilt.started)
        self.assertEqual(rebuilt.kwargs, self.EXPECTED_KWARGS)

    def test_reset_session_closes_and_clears_the_session(self):
        self.client.request("GET", self.SERIES_URL)
        first = self._sessions()[0]

        self.client._reset_session()

        self.assertTrue(first.closed)
        self.assertIsNone(getattr(self.client._local, "session", None))

    def test_only_fetch_arguments_are_forwarded_to_the_session(self):
        """There is one session: no per-request transport-policy flag may exist."""
        self.client.request(
            "GET", self.IMAGE_LIST_URL, headers={"HX-Request": "true"}
        )

        session = self._sessions()[0]
        self.assertTrue(session.fetch_calls)
        for _url, kwargs in session.fetch_calls:
            self.assertEqual(set(kwargs), {"extra_headers", "timeout"})
            self.assertEqual(kwargs.get("extra_headers"), {"HX-Request": "true"})

    def test_retry_budget_rebuilds_the_session_with_the_same_configuration(self):
        """retries=N means exactly N fetch attempts, all on the one session."""
        with patch("src.downloader.http_client.StealthySession", FailingRecordingSession), \
                patch("src.downloader.http_client.time.sleep") as sleep_mock:
            client = HttpClient(".")
            client.reset_scraper()
            FailingRecordingSession.instances.clear()
            with self.assertRaises(RuntimeError):
                client.request("GET", self.SERIES_URL, retries=2)

            attempts = sum(len(s.fetch_calls) for s in FailingRecordingSession.instances)
            self.assertEqual(attempts, 2)
            self.assertEqual(sleep_mock.call_count, 1)
            for session in FailingRecordingSession.instances:
                self.assertIs(
                    session.kwargs.get("disable_resources"),
                    False,
                    "every retry must rebuild the resource-loading session",
                )
            client.reset_scraper()


if __name__ == "__main__":
    unittest.main()

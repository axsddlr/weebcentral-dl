#!/usr/bin/env python3
"""
Focused unit tests for HttpClient.request's retry budget.

These tests never touch the network and never launch a browser: the session
lookup is patched to a stub whose fetch() always raises, and both the session
reset and time.sleep are no-ops.

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


if __name__ == "__main__":
    unittest.main()

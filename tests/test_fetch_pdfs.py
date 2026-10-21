import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "shidi" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import unittest
import urllib.error

import fetch_pdfs


class DoiFromTextTest(unittest.TestCase):
    def test_bare_doi(self):
        self.assertEqual(fetch_pdfs.doi_from_text("10.1021/acs.joc.0c01234"), "10.1021/acs.joc.0c01234")

    def test_doi_org_url(self):
        self.assertEqual(
            fetch_pdfs.doi_from_text("https://doi.org/10.1002/anie.202001234"),
            "10.1002/anie.202001234",
        )

    def test_trailing_punctuation_stripped(self):
        self.assertEqual(fetch_pdfs.doi_from_text("(10.1038/s41586-020-2649-2)."), "10.1038/s41586-020-2649-2")

    def test_garbage(self):
        self.assertEqual(fetch_pdfs.doi_from_text("no doi here"), "")


class LooksLikePdfTest(unittest.TestCase):
    def test_valid_header(self):
        self.assertTrue(fetch_pdfs.looks_like_pdf(b"%PDF-1.7\n..."))
        self.assertTrue(fetch_pdfs.looks_like_pdf(b"  %PDF-1.4"))

    def test_html_and_empty(self):
        self.assertFalse(fetch_pdfs.looks_like_pdf(b"<html>cloudflare</html>"))
        self.assertFalse(fetch_pdfs.looks_like_pdf(b""))
        self.assertFalse(fetch_pdfs.looks_like_pdf(None))


class BackoffTest(unittest.TestCase):
    def test_exponential_and_cap(self):
        self.assertEqual(fetch_pdfs.backoff_seconds(0), 1.0)
        self.assertEqual(fetch_pdfs.backoff_seconds(1), 2.0)
        self.assertEqual(fetch_pdfs.backoff_seconds(10), 8.0)

    def test_retry_after_wins_and_clamps(self):
        self.assertEqual(fetch_pdfs.backoff_seconds(0, "5"), 5.0)
        self.assertEqual(fetch_pdfs.backoff_seconds(0, "120"), 60.0)
        self.assertEqual(fetch_pdfs.backoff_seconds(2, "garbage"), 4.0)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def _http_error(code, retry_after=None):
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("https://example.org", code, "err", headers, None)


class HttpGetRetryTest(unittest.TestCase):
    def test_retries_429_then_succeeds(self):
        calls = []

        def opener(req, timeout=None):
            calls.append(req.full_url)
            if len(calls) == 1:
                raise _http_error(429, "3")
            return _Response(b"ok")

        waits = []
        result = fetch_pdfs.http_get("https://example.org/x", opener=opener, sleep=waits.append)
        self.assertEqual(result, b"ok")
        self.assertEqual(len(calls), 2)
        self.assertEqual(waits, [3.0])

    def test_404_is_not_retried(self):
        calls = []

        def opener(req, timeout=None):
            calls.append(req.full_url)
            raise _http_error(404)

        waits = []
        result = fetch_pdfs.http_get("https://example.org/x", opener=opener, sleep=waits.append)
        self.assertIsNone(result)
        self.assertEqual(len(calls), 1)
        self.assertEqual(waits, [])

    def test_network_errors_exhaust_retries(self):
        calls = []

        def opener(req, timeout=None):
            calls.append(req.full_url)
            raise urllib.error.URLError("connection reset")

        waits = []
        result = fetch_pdfs.http_get("https://example.org/x", retries=2, opener=opener, sleep=waits.append)
        self.assertIsNone(result)
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(waits), 2)


if __name__ == "__main__":
    unittest.main()

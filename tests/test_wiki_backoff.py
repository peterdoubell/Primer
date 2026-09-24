"""Respect explicit Wikipedia overload without masking genuinely absent titles."""
from email.message import Message
from email.utils import formatdate
from urllib.error import HTTPError

import pytest

from primer.wiki import WikiService


@pytest.mark.parametrize("code,retry,expected", [
    (429, "18", 1018), (503, "120", 1120), (429, "bad", 1060),
    (429, formatdate(1090, usegmt=True), 1090), (404, "120", 0),
])
def test_live_backoff_respects_retry_after(monkeypatch, code, retry, expected):
    monkeypatch.setattr("primer.wiki.time.time", lambda: 1000)
    service = WikiService.__new__(WikiService)
    service._live_fetch_blocked_until = 0
    headers = Message()
    headers["Retry-After"] = retry
    service._note_live_failure(HTTPError("https://en.wikipedia.org", code, "failure", headers, None))
    assert service._live_fetch_blocked_until == expected

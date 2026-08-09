"""AAA-audit regression tests for the content core (wiki.py / library.py).

Covers the five audit findings:
1. _cache_get honours its lang argument (prefer_simple works for cached articles)
2. proxy_image validates upstream Content-Type before caching/serving
3. get_summary/_fetch_live share an offline circuit breaker
4. resume-download accounting when a server ignores Range and returns 200
5. article_cache eviction cap + staleness-aware refresh
"""

import io
import time

import pytest

import primer.library as lib
import primer.wiki as wiki
from primer.wiki import WikiService


@pytest.fixture
def svc(tmp_path, monkeypatch):
    # Isolate from the real content/ directory: these tests exercise the
    # cache/live layers, so no ZIM archive may answer first.
    monkeypatch.setattr(wiki, "CONTENT_DIR", str(tmp_path / "content"))
    return WikiService(str(tmp_path / "wiki-test.db"))


def _seed(svc_, title, lang, html, fetched_at=None):
    with wiki._db_lock, svc_._conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO article_cache(title, lang, html, summary, fetched_at)"
            " VALUES(?,?,?,'',?)",
            (title, lang, html, fetched_at if fetched_at is not None else time.time()),
        )


def _block_network(monkeypatch):
    def boom(url, timeout=15.0):
        raise OSError("network down")
    monkeypatch.setattr(wiki, "_http_get", boom)


# ---------- 1. lang-aware cache lookup ----------

class TestCacheLang:
    def test_cache_get_filters_on_lang(self, svc):
        _seed(svc, "Cat", "en", "<p>english cat</p>")
        assert svc._cache_get("Cat", "en")["html"] == "<p>english cat</p>"
        assert svc._cache_get("Cat", "simple") is None

    def test_cache_get_lang_none_matches_any(self, svc):
        _seed(svc, "Cat", "simple", "<p>simple cat</p>")
        got = svc._cache_get("Cat", None)
        assert got and got["simple"] is True

    def test_prefer_simple_serves_cached_simple(self, svc, monkeypatch):
        _block_network(monkeypatch)
        _seed(svc, "Cat", "simple", "<p>simple cat</p>")
        got = svc.get_article("Cat", prefer_simple=True)
        assert got["html"] == "<p>simple cat</p>" and got["simple"] is True

    def test_offline_falls_back_to_other_lang(self, svc, monkeypatch):
        # Only an English copy cached; a Simple-preferring offline reader
        # should still get it rather than nothing.
        _block_network(monkeypatch)
        _seed(svc, "Cat", "en", "<p>english cat</p>")
        got = svc.get_article("Cat", prefer_simple=True)
        assert got is not None and got["html"] == "<p>english cat</p>"
        assert got["simple"] is False


# ---------- 2. image proxy content-type ----------

class _FakeResponse(io.BytesIO):
    def __init__(self, data, content_type):
        super().__init__(data)
        self.headers = {"Content-Type": content_type}
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestProxyImageContentType:
    URL = "https://upload.wikimedia.org/x/y/pic.jpg"

    def _serve(self, monkeypatch, data, ctype):
        class Opener:
            def open(self, req, timeout=20):
                return _FakeResponse(data, ctype)
        monkeypatch.setattr(wiki.urllib.request, "build_opener", lambda *a: Opener())

    def test_non_image_response_is_refused_and_not_cached(self, svc, monkeypatch):
        self._serve(monkeypatch, b"<html>error page</html>", "text/html; charset=utf-8")
        assert svc.proxy_image(self.URL) is None
        with wiki._db_lock, svc._conn() as c:
            assert c.execute("SELECT COUNT(*) FROM image_cache").fetchone()[0] == 0

    def test_image_response_is_served_and_cached(self, svc, monkeypatch):
        self._serve(monkeypatch, b"\x89PNGdata", "image/png")
        assert svc.proxy_image(self.URL) == (b"\x89PNGdata", "image/png")
        with wiki._db_lock, svc._conn() as c:
            assert c.execute("SELECT COUNT(*) FROM image_cache").fetchone()[0] == 1


# ---------- 3. offline circuit breaker for articles/summaries ----------

class TestFetchBreaker:
    def test_fetch_live_failure_trips_breaker(self, svc, monkeypatch):
        calls = []

        def boom(url, timeout=15.0):
            calls.append(url)
            raise OSError("network down")

        monkeypatch.setattr(wiki, "_http_get", boom)
        assert svc._fetch_live("Alpha", "en") is None
        assert time.time() < svc._live_fetch_blocked_until
        # Subsequent fetches fail fast without touching the network.
        assert svc._fetch_live("Beta", "en") is None
        assert len(calls) == 1

    def test_http_404_does_not_trip_breaker(self, svc, monkeypatch):
        def not_found(url, timeout=15.0):
            exc = OSError("not found")
            exc.code = 404
            raise exc

        monkeypatch.setattr(wiki, "_http_get", not_found)
        assert svc._fetch_live("Nope", "en") is None
        assert svc._live_fetch_blocked_until == 0.0

    def test_summary_uses_breaker_and_local_fallback(self, svc, monkeypatch):
        calls = []

        def boom(url, timeout=15.0):
            calls.append(url)
            raise OSError("network down")

        monkeypatch.setattr(wiki, "_http_get", boom)
        _seed(svc, "Gamma", "en", "<p>Gamma is a letter of the Greek alphabet.</p>")
        svc._live_fetch_blocked_until = time.time() + 60
        got = svc.get_summary("Gamma")
        assert got and "Greek alphabet" in got["extract"]
        assert calls == []  # breaker skipped the live attempt entirely

    def test_summary_failure_trips_breaker(self, svc, monkeypatch):
        _block_network(monkeypatch)
        svc.get_summary("Delta")
        assert time.time() < svc._live_fetch_blocked_until


# ---------- 4. resume accounting on a 200 response ----------

class TestDownloadResumeAccounting:
    def _fake_urlopen(self, monkeypatch, body, status):
        class Resp(io.BytesIO):
            def __init__(self):
                super().__init__(body)
                self.status = status
                self.headers = {"Content-Length": str(len(body))}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(lib.urllib.request, "urlopen", lambda req, timeout=60: Resp())

    def test_200_resume_discards_partial_from_total(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "x.zim")
        with open(dest + ".part", "wb") as f:
            f.write(b"a" * 100)  # stale partial the server will ignore
        body = b"b" * 40
        self._fake_urlopen(monkeypatch, body, 200)
        state = {"key": "x", "status": "downloading", "bytes": 0, "total": 0, "error": ""}
        lib._download_worker(state, "http://example.invalid/x.zim", dest)
        # Total must be the file length alone — the discarded 100 partial
        # bytes must not inflate it.
        assert state["total"] == 40
        assert state["bytes"] == 40
        assert state["status"] == "done"
        with open(dest, "rb") as f:
            assert f.read() == body

    def test_206_resume_keeps_partial_in_total(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "y.zim")
        with open(dest + ".part", "wb") as f:
            f.write(b"a" * 100)
        body = b"b" * 40
        self._fake_urlopen(monkeypatch, body, 206)
        state = {"key": "y", "status": "downloading", "bytes": 0, "total": 0, "error": ""}
        lib._download_worker(state, "http://example.invalid/y.zim", dest)
        assert state["total"] == 140
        assert state["bytes"] == 140
        with open(dest, "rb") as f:
            assert f.read() == b"a" * 100 + body


# ---------- 5. eviction cap + staleness refresh ----------

class TestCacheEvictionAndStaleness:
    def test_fetch_live_evicts_beyond_cap(self, svc, monkeypatch):
        monkeypatch.setattr(WikiService, "CACHE_MAX_ARTICLES", 5)
        now = time.time()
        for i in range(10):
            _seed(svc, "Old %d" % i, "en", "<p>x</p>", fetched_at=now - 1000 + i)
        monkeypatch.setattr(wiki, "_http_get", lambda url, timeout=15.0: b"<p>fresh</p>")
        svc._fetch_live("Fresh", "en")
        with wiki._db_lock, svc._conn() as c:
            titles = {r[0] for r in c.execute("SELECT title FROM article_cache")}
        assert len(titles) == 5
        assert "Fresh" in titles          # newest survives
        assert "Old 0" not in titles      # oldest evicted

    def test_stale_cached_article_is_refreshed_when_online(self, svc, monkeypatch):
        _seed(svc, "Epoch", "en", "<p>old copy</p>",
              fetched_at=time.time() - WikiService.CACHE_STALE_SECONDS - 10)
        monkeypatch.setattr(wiki, "_http_get", lambda url, timeout=15.0: b"<p>new copy</p>")
        got = svc.get_article("Epoch")
        assert got["source"] == "live" and got["html"] == "<p>new copy</p>"

    def test_stale_cached_article_survives_offline(self, svc, monkeypatch):
        _block_network(monkeypatch)
        _seed(svc, "Epoch", "en", "<p>old copy</p>",
              fetched_at=time.time() - WikiService.CACHE_STALE_SECONDS - 10)
        got = svc.get_article("Epoch")
        assert got["source"] == "cache" and got["html"] == "<p>old copy</p>"

    def test_fresh_cached_article_skips_refresh(self, svc, monkeypatch):
        calls = []

        def spy(url, timeout=15.0):
            calls.append(url)
            raise OSError("should not be called")

        monkeypatch.setattr(wiki, "_http_get", spy)
        _seed(svc, "Now", "en", "<p>fresh enough</p>")
        got = svc.get_article("Now")
        assert got["source"] == "cache"
        assert calls == []

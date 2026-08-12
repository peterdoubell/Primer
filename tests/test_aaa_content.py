"""AAA-audit regression tests for the content core (wiki.py / library.py).

Covers the five audit findings:
1. _cache_get honours its lang argument (prefer_simple works for cached articles)
2. proxy_image validates upstream Content-Type before caching/serving
3. get_summary/_fetch_live share an offline circuit breaker
4. resume-download accounting when a server ignores Range and returns 200
5. article_cache eviction cap + staleness-aware refresh

Plus the content-core follow-up round:
6.  (title, lang) composite cache key — both language copies coexist
7.  get_summary is lang-exact on the cached-summary path
8.  images up to MAX_IMAGE_BYTES are cached; image_cache has an eviction cap
9.  download integrity: size check, .sha256 sidecar verify, disk preflight
10. a finished download fires the rescan hook so the archive mounts at once
11. _entry_for_title tolerates interior capitalization on multi-word titles
"""

import io
import os
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


def _no_network(url, timeout=15.0):
    raise OSError("network down")


def _block_network(monkeypatch):
    monkeypatch.setattr(wiki, "_http_get", _no_network)


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
        # Keep the .sha256 sidecar lookup off the network: these tests are
        # about byte accounting, so verification downgrades to the size check.
        monkeypatch.setattr(lib, "_http_get", _no_network)

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


# ---------- 6. (title, lang) composite cache key ----------

class TestCompositeCacheKey:
    def test_both_language_copies_coexist(self, svc, monkeypatch):
        # The audit bug: caching the Simple copy overwrote the English copy
        # via the title-only primary key, so an offline 'en' reader lost it.
        monkeypatch.setattr(wiki, "_http_get", lambda url, timeout=15.0: b"<p>en</p>")
        svc._fetch_live("Cat", "en")
        monkeypatch.setattr(wiki, "_http_get", lambda url, timeout=15.0: b"<p>simple</p>")
        svc._fetch_live("Cat", "simple")
        assert svc._cache_get("Cat", "en")["html"] == "<p>en</p>"
        assert svc._cache_get("Cat", "simple")["html"] == "<p>simple</p>"

    def test_old_title_only_schema_is_migrated(self, tmp_path, monkeypatch):
        import sqlite3
        monkeypatch.setattr(wiki, "CONTENT_DIR", str(tmp_path / "content"))
        db = str(tmp_path / "old.db")
        with sqlite3.connect(db) as c:
            c.execute(
                """CREATE TABLE article_cache (
                       title TEXT PRIMARY KEY, lang TEXT, html TEXT,
                       summary TEXT, fetched_at REAL)"""
            )
            c.execute(
                "INSERT INTO article_cache VALUES('Cat', NULL, '<p>old</p>', '', 1.0)"
            )
        svc = WikiService(db)
        # The pre-lang row survives, coalesced to 'en' to satisfy the key.
        assert svc._cache_get("Cat", "en")["html"] == "<p>old</p>"
        # And the composite key now holds: a simple copy does not clobber it.
        _seed(svc, "Cat", "simple", "<p>simple</p>")
        assert svc._cache_get("Cat", "en")["html"] == "<p>old</p>"


# ---------- 7. get_summary lang-exact cached lookup ----------

class TestSummaryLangExact:
    def _seed_summary(self, svc_, title, lang, extract):
        import json as _json
        with wiki._db_lock, svc_._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO article_cache(title, lang, html, summary, fetched_at)"
                " VALUES(?,?,'',?,?)",
                (title, lang, _json.dumps({"title": title, "extract": extract,
                                           "description": "", "thumbnail": ""}),
                 time.time()),
            )

    def test_cached_summary_of_other_lang_is_not_served(self, svc, monkeypatch):
        _block_network(monkeypatch)
        self._seed_summary(svc, "Cat", "simple", "simple words")
        # An 'en' request must not get the Simple summary; with nothing else
        # available it falls through (breaker trips on the live miss).
        assert svc.get_summary("Cat", "en") is None

    def test_cached_summary_matching_lang_is_served(self, svc, monkeypatch):
        _block_network(monkeypatch)
        self._seed_summary(svc, "Cat", "simple", "simple words")
        got = svc.get_summary("Cat", "simple")
        assert got and got["extract"] == "simple words"


# ---------- 8. image cache: large images cached, eviction cap ----------

class TestImageCacheCoverage:
    URL = "https://upload.wikimedia.org/x/y/big.jpg"

    def _serve(self, monkeypatch, data, ctype="image/jpeg"):
        class Opener:
            def open(self, req, timeout=20):
                return _FakeResponse(data, ctype)
        monkeypatch.setattr(wiki.urllib.request, "build_opener", lambda *a: Opener())

    def test_image_between_4_and_8mb_is_cached(self, svc, monkeypatch):
        # The audit bug: 4-8MB images were served but never cached, so they
        # were re-fetched every view and silently missing offline.
        data = b"j" * (5 * 1024 * 1024)
        self._serve(monkeypatch, data)
        assert svc.proxy_image(self.URL) == (data, "image/jpeg")
        with wiki._db_lock, svc._conn() as c:
            n = c.execute("SELECT COUNT(*) FROM image_cache WHERE url=?",
                          (self.URL,)).fetchone()[0]
        assert n == 1

    def test_image_cache_evicts_beyond_cap(self, svc, monkeypatch):
        monkeypatch.setattr(WikiService, "CACHE_MAX_IMAGES", 3)
        now = time.time()
        with wiki._db_lock, svc._conn() as c:
            for i in range(6):
                c.execute(
                    "INSERT INTO image_cache(url, data, mime, fetched_at) VALUES(?,?,?,?)",
                    ("https://upload.wikimedia.org/old/%d.png" % i, b"x",
                     "image/png", now - 1000 + i),
                )
        self._serve(monkeypatch, b"fresh", "image/png")
        svc.proxy_image(self.URL)
        with wiki._db_lock, svc._conn() as c:
            urls = {r[0] for r in c.execute("SELECT url FROM image_cache")}
        assert len(urls) == 3
        assert self.URL in urls                                    # newest kept
        assert "https://upload.wikimedia.org/old/0.png" not in urls  # oldest gone


# ---------- 9. download integrity: size, checksum, disk preflight ----------

class TestDownloadIntegrity:
    def _fake_urlopen(self, monkeypatch, body, status=200, content_length=None):
        class Resp(io.BytesIO):
            def __init__(self):
                super().__init__(body)
                self.status = status
                self.headers = {"Content-Length": str(
                    len(body) if content_length is None else content_length)}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(lib.urllib.request, "urlopen", lambda req, timeout=60: Resp())

    def _state(self, key="z"):
        return {"key": key, "status": "downloading", "bytes": 0, "total": 0, "error": ""}

    def test_truncated_body_keeps_part_and_errors(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "z.zim")
        # Server promises 100 bytes but the stream dies after 40.
        self._fake_urlopen(monkeypatch, b"b" * 40, content_length=100)
        monkeypatch.setattr(lib, "_http_get", _no_network)
        state = self._state()
        lib._download_worker(state, "http://example.invalid/z.zim", dest)
        assert state["status"] == "error" and "truncated" in state["error"]
        assert not os.path.exists(dest)
        assert os.path.exists(dest + ".part")   # resumable

    def test_checksum_mismatch_discards_part(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "z.zim")
        self._fake_urlopen(monkeypatch, b"corrupt bytes!")
        bogus = "0" * 64
        monkeypatch.setattr(lib, "_http_get",
                            lambda url, timeout=20: (bogus + "  z.zim\n").encode())
        state = self._state()
        lib._download_worker(state, "http://example.invalid/z.zim", dest)
        assert state["status"] == "error" and "sha256" in state["error"]
        assert not os.path.exists(dest)
        # A bad prefix cannot be fixed by resuming, so the .part is dropped.
        assert not os.path.exists(dest + ".part")

    def test_checksum_match_completes(self, tmp_path, monkeypatch):
        import hashlib
        dest = str(tmp_path / "z.zim")
        body = b"good zim bytes"
        self._fake_urlopen(monkeypatch, body)
        digest = hashlib.sha256(body).hexdigest()
        monkeypatch.setattr(lib, "_http_get",
                            lambda url, timeout=20: (digest + "  z.zim\n").encode())
        state = self._state()
        lib._download_worker(state, "http://example.invalid/z.zim", dest)
        assert state["status"] == "done"
        with open(dest, "rb") as f:
            assert f.read() == body

    def test_missing_sidecar_does_not_fail_download(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "z.zim")
        self._fake_urlopen(monkeypatch, b"unverifiable but complete")
        monkeypatch.setattr(lib, "_http_get", _no_network)   # sidecar unreachable
        state = self._state()
        lib._download_worker(state, "http://example.invalid/z.zim", dest)
        assert state["status"] == "done"

    def test_insufficient_disk_space_fails_before_streaming(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "z.zim")
        self._fake_urlopen(monkeypatch, b"b" * 40)
        monkeypatch.setattr(lib, "_http_get", _no_network)

        class Usage:
            free = 10  # bytes — nowhere near 40 + headroom

        monkeypatch.setattr(lib.shutil, "disk_usage", lambda p: Usage())
        state = self._state()
        lib._download_worker(state, "http://example.invalid/z.zim", dest)
        assert state["status"] == "error" and "disk space" in state["error"]
        assert not os.path.exists(dest)


# ---------- 10. rescan hook fires after a finished download ----------

class TestRescanHook:
    def test_hook_fires_on_completed_download(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "h.zim")

        class Resp(io.BytesIO):
            def __init__(self):
                super().__init__(b"zimdata")
                self.status = 200
                self.headers = {"Content-Length": "7"}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(lib.urllib.request, "urlopen", lambda req, timeout=60: Resp())
        monkeypatch.setattr(lib, "_http_get", _no_network)
        fired = []
        monkeypatch.setattr(lib, "_rescan_hooks", [lambda: fired.append(True)])
        state = {"key": "h", "status": "downloading", "bytes": 0, "total": 0, "error": ""}
        lib._download_worker(state, "http://example.invalid/h.zim", dest)
        assert state["status"] == "done"
        assert fired == [True]

    def test_wiki_service_registers_its_rescan(self, svc):
        # Construction wires svc.rescan into the library hooks (weakly).
        import weakref
        assert any(isinstance(h, weakref.WeakMethod) and h() == svc.rescan
                   for h in lib._rescan_hooks)

    def test_hook_failure_does_not_mark_download_error(self, tmp_path, monkeypatch):
        dest = str(tmp_path / "h2.zim")

        class Resp(io.BytesIO):
            def __init__(self):
                super().__init__(b"zimdata")
                self.status = 200
                self.headers = {"Content-Length": "7"}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(lib.urllib.request, "urlopen", lambda req, timeout=60: Resp())
        monkeypatch.setattr(lib, "_http_get", _no_network)

        def bad_hook():
            raise RuntimeError("mount failed")

        monkeypatch.setattr(lib, "_rescan_hooks", [bad_hook])
        state = {"key": "h2", "status": "downloading", "bytes": 0, "total": 0, "error": ""}
        lib._download_worker(state, "http://example.invalid/h2.zim", dest)
        assert state["status"] == "done"   # the download itself succeeded


# ---------- 11. multi-word title case tolerance ----------

class _FakeZim:
    """Path-keyed stand-in for a libzim Archive: case-exact, like the real one."""

    def __init__(self, paths):
        self.paths = set(paths)

    def has_entry_by_path(self, path):
        return path in self.paths

    def get_entry_by_path(self, path):
        if path in self.paths:
            return path      # any non-None sentinel will do
        raise KeyError(path)

    def get_entry_by_title(self, title):
        raise KeyError(title)


class TestTitleCaseTolerance:
    def _arc(self, paths):
        arc = wiki.ZimArchive.__new__(wiki.ZimArchive)
        arc.archive = _FakeZim(paths)
        return arc

    def test_all_lowercase_multiword_finds_capitalized_entry(self):
        arc = self._arc({"Albert_Einstein"})
        assert arc._entry_for_title("albert einstein") == "Albert_Einstein"

    def test_first_letter_only_capitalization_still_works(self):
        arc = self._arc({"Freedom_of_speech"})
        # Sentence-case entry: matched by the first-letter-upcased variant,
        # before the every-word-capped variant would miss it.
        assert arc._entry_for_title("freedom of speech") == "Freedom_of_speech"

    def test_exact_title_still_preferred(self):
        arc = self._arc({"eBay"})
        assert arc._entry_for_title("eBay") == "eBay"

    def test_missing_title_returns_none(self):
        arc = self._arc(set())
        assert arc._entry_for_title("nothing here") is None


def test_rendered_mathematics_is_not_blocked_by_the_image_allowlist():
    """Wikipedia serves rendered formulas from the APEX domain.

    The allowlist's suffix tests carry a leading dot so that
    `evilwikimedia.org` cannot match — correct, and the reason this bug was
    invisible: `wikimedia.org` itself matched neither the dotted suffix nor
    the one exact host that was listed (`upload.wikimedia.org`). Every
    equation in every article proxied to a 404, and the reader got a broken
    image where the mathematics should be.
    """
    from primer.wiki import WikiService

    math = ("https://wikimedia.org/api/rest_v1/media/math/render/svg/"
            "df0284d6d3707f6972edd6b5797aa405b91080ad")
    assert WikiService._image_host_allowed(math)
    assert WikiService._image_host_allowed("https://wikipedia.org/x.png")
    assert WikiService._image_host_allowed("https://upload.wikimedia.org/x.png")
    assert WikiService._image_host_allowed("https://en.wikipedia.org/x.png")

    # The guard the leading dot exists for must still hold.
    for blocked in ("https://evilwikimedia.org/x.png",
                    "https://notwikipedia.org/x.png",
                    "https://wikimedia.org.evil.com/x.png",
                    "http://169.254.169.254/latest/meta-data/"):
        assert not WikiService._image_host_allowed(blocked), blocked

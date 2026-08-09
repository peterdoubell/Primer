"""Content core of the Primer.

Serves encyclopedia articles from three layers, in order of preference:

1. Local ZIM archives (content/*.zim) read natively via libzim — this is how
   the book literally contains Wikipedia. The full English Wikipedia is a
   single ZIM file the Library page can download.
2. The local article cache (SQLite) — every article ever read while online is
   kept forever, so the book grows toward completeness as it is used.
3. The live Wikipedia REST API (when online).

Also provides unified search (ZIM suggestion index + live search), raw entry
serving for images/CSS inside ZIM archives, and an image proxy cache so
pictures survive going offline.
"""

import json
import logging
import os
import re
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("primer.wiki")

try:
    from libzim.reader import Archive
    from libzim.suggestion import SuggestionSearcher
    from libzim.search import Query, Searcher
    HAVE_LIBZIM = True
except ImportError:  # pragma: no cover
    HAVE_LIBZIM = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Overridable for the same reason as PRIMER_DB: on a host where the code
# tree is read-only (a serverless bundle), archives and the makedirs below
# must land on the writable disk instead of beside the source.
CONTENT_DIR = os.environ.get("PRIMER_CONTENT_DIR") or os.path.join(ROOT, "content")
USER_AGENT = "ThePrimer/1.0 (offline-first educational reader; local personal use)"

_db_lock = threading.Lock()
_search_lock = threading.Lock()
_live_cache: Dict[str, List[str]] = {}


def _http_get(url: str, timeout: float = 15.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _http_get_json(url: str, timeout: float = 15.0):
    return json.loads(_http_get(url, timeout).decode("utf-8"))


class ZimArchive:
    """One mounted ZIM file."""

    def __init__(self, path: str):
        self.path = path
        self.id = re.sub(r"[^a-zA-Z0-9_-]", "_", os.path.basename(path)[:-4])
        self.archive = Archive(path)
        self._suggestion = None
        self._searcher = None
        self._lock = threading.Lock()
        m = self.archive.metadata_keys if hasattr(self.archive, "metadata_keys") else []
        self.meta = {}
        for key in ("Title", "Description", "Language", "Date"):
            try:
                self.meta[key.lower()] = bytes(self.archive.get_metadata(key)).decode("utf-8")
            except Exception:
                self.meta[key.lower()] = ""   # optional metadata; absence is normal
        self.is_simple = "simple" in os.path.basename(path).lower()

    @property
    def article_count(self) -> int:
        try:
            return self.archive.article_count
        except Exception:
            return self.archive.entry_count

    def _entry_for_title(self, title: str):
        """Find an entry by article title, tolerating path conventions."""
        candidates = [
            title.replace(" ", "_"),
            "A/" + title.replace(" ", "_"),
            title,
            "A/" + title,
        ]
        for cand in candidates:
            try:
                if self.archive.has_entry_by_path(cand):
                    return self.archive.get_entry_by_path(cand)
            except Exception:
                continue          # path shape not present in this archive
        try:
            return self.archive.get_entry_by_title(title)
        except Exception:
            pass          # not in this archive; the caller falls through
        # Case-tolerant retry: Wikipedia titles capitalize the first letter.
        if title and title[0].islower():
            return self._entry_for_title(title[0].upper() + title[1:])
        return None

    def get_article(self, title: str) -> Optional[Tuple[str, str]]:
        """Return (html, base_dir) for an article title, or None."""
        entry = self._entry_for_title(title)
        if entry is None:
            return None
        try:
            while entry.is_redirect:
                entry = entry.get_redirect_entry()
        except Exception as exc:
            log.warning("broken redirect chain for %r in %s: %s", title[:60], self.id, exc)
        item = entry.get_item()
        mime = item.mimetype or ""
        if "html" not in mime:
            return None
        html = bytes(item.content).decode("utf-8", errors="replace")
        base = os.path.dirname(entry.path)
        return html, base

    def get_entry_raw(self, path: str) -> Optional[Tuple[bytes, str]]:
        try:
            entry = self.archive.get_entry_by_path(path)
            while entry.is_redirect:
                entry = entry.get_redirect_entry()
            item = entry.get_item()
            return bytes(item.content), item.mimetype or "application/octet-stream"
        except KeyError:
            return None          # simply not in this archive
        except Exception as exc:
            log.warning("archive %s failed reading %s: %s", self.id, path[:80], exc)
            return None

    def suggest(self, query: str, limit: int = 12) -> List[Dict]:
        if not query.strip():
            return []
        with self._lock:
            try:
                if self._suggestion is None:
                    self._suggestion = SuggestionSearcher(self.archive)
                search = self._suggestion.suggest(query)
                n = min(limit, search.getEstimatedMatches())
                results = []
                for path in search.getResults(0, n):
                    title = path.split("/")[-1].replace("_", " ")
                    results.append({"title": title, "path": path, "source": self.id})
                return results
            except Exception as exc:
                log.warning("suggestion index unavailable in %s: %s", self.id, exc)
                return []

    def search_fulltext(self, query: str, limit: int = 12) -> List[Dict]:
        with self._lock:
            try:
                if self._searcher is None:
                    self._searcher = Searcher(self.archive)
                search = self._searcher.search(Query().set_query(query))
                n = min(limit, search.getEstimatedMatches())
                results = []
                for path in search.getResults(0, n):
                    title = path.split("/")[-1].replace("_", " ")
                    results.append({"title": title, "path": path, "source": self.id})
                return results
            except Exception as exc:
                log.warning("full-text search failed in %s: %s", self.id, exc)
                return []

    def random_title(self) -> Optional[str]:
        try:
            entry = self.archive.get_random_entry()
            return entry.title
        except Exception as exc:
            log.warning("random entry failed in %s: %s", self.id, exc)
            return None


class WikiService:
    """Unified article access across ZIM archives, cache, and live Wikipedia."""

    def __init__(self, db_path: str):
        os.makedirs(CONTENT_DIR, exist_ok=True)
        self.db_path = db_path
        self.archives: List[ZimArchive] = []
        self._live_search_blocked_until = 0.0
        self._init_db()
        self.rescan()

    # ---------- storage ----------

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=8000")
        return conn

    def _init_db(self):
        with _db_lock, self._conn() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS article_cache (
                    title TEXT PRIMARY KEY,
                    lang TEXT,
                    html TEXT,
                    summary TEXT,
                    fetched_at REAL
                )"""
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS image_cache (
                    url TEXT PRIMARY KEY,
                    data BLOB,
                    mime TEXT,
                    fetched_at REAL
                )"""
            )

    # ---------- archives ----------

    def rescan(self):
        found = []
        if HAVE_LIBZIM:
            for name in sorted(os.listdir(CONTENT_DIR)):
                if name.endswith(".zim"):
                    path = os.path.join(CONTENT_DIR, name)
                    try:
                        found.append(ZimArchive(path))
                    except Exception as exc:
                        log.error("could not open archive %s: %s — skipping", name, exc)
        # Prefer the biggest general-purpose archive first, but remember
        # which are Simple English so young readers can be routed there.
        found.sort(key=lambda a: a.article_count, reverse=True)
        self.archives = found

    def archive_by_id(self, archive_id: str) -> Optional[ZimArchive]:
        for a in self.archives:
            if a.id == archive_id:
                return a
        return None

    def library_status(self) -> Dict:
        cache_count = 0
        with _db_lock, self._conn() as c:
            row = c.execute("SELECT COUNT(*) FROM article_cache").fetchone()
            cache_count = row[0] if row else 0
        return {
            "archives": [
                {
                    "id": a.id,
                    "file": os.path.basename(a.path),
                    "title": a.meta.get("title") or a.id,
                    "description": a.meta.get("description", ""),
                    "language": a.meta.get("language", ""),
                    "date": a.meta.get("date", ""),
                    "articles": a.article_count,
                    "size_mb": round(os.path.getsize(a.path) / 1048576, 1),
                    "simple": a.is_simple,
                }
                for a in self.archives
            ],
            "cached_articles": cache_count,
            "libzim": HAVE_LIBZIM,
        }

    # ---------- article access ----------

    def get_article(self, title: str, prefer_simple: bool = False) -> Optional[Dict]:
        """Fetch an article by title. Returns dict with html + provenance."""
        title = title.strip()
        if not title:
            return None

        ordered = sorted(
            self.archives,
            key=lambda a: (a.is_simple != prefer_simple, -a.article_count),
        )
        for arc in ordered:
            got = arc.get_article(title)
            if got:
                html, base = got
                return {
                    "title": title.replace("_", " "),
                    "html": html,
                    "source": "zim",
                    "archive": arc.id,
                    "base": "/zim/{}/{}".format(arc.id, base + "/" if base else ""),
                    "simple": arc.is_simple,
                }

        lang = "simple" if prefer_simple else "en"
        cached = self._cache_get(title, lang) or self._cache_get(title, "en")
        if cached:
            return cached

        fetched = self._fetch_live(title, lang)
        if fetched is None and lang != "en":
            fetched = self._fetch_live(title, "en")
        return fetched

    def get_summary(self, title: str, lang: str = "en") -> Optional[Dict]:
        """Plain-text summary — used for quizzes and the tutor."""
        # Try live/cached summary first (clean plain text), else strip ZIM html.
        with _db_lock, self._conn() as c:
            row = c.execute(
                "SELECT summary FROM article_cache WHERE title=? AND summary != ''",
                (self._norm(title),),
            ).fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except Exception:
                pass
        try:
            url = "https://{}.wikipedia.org/api/rest_v1/page/summary/{}".format(
                lang, urllib.parse.quote(title.replace(" ", "_"), safe="")
            )
            data = _http_get_json(url)
            summary = {
                "title": data.get("title", title),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
                "thumbnail": (data.get("thumbnail") or {}).get("source", ""),
            }
            with _db_lock, self._conn() as c:
                c.execute(
                    """INSERT INTO article_cache(title, lang, html, summary, fetched_at)
                       VALUES(?,?,COALESCE((SELECT html FROM article_cache WHERE title=?),''),?,?)
                       ON CONFLICT(title) DO UPDATE SET summary=excluded.summary""",
                    (self._norm(title), lang, self._norm(title), json.dumps(summary), time.time()),
                )
            return summary
        except Exception as exc:
            log.info("summary unavailable for %r: %s", title[:60], exc.__class__.__name__)
        # Offline fallback: derive text from whatever article HTML we have.
        art = self.get_article(title)
        if art:
            text = self.article_plaintext(art["html"], max_chars=1200)
            if text:
                return {"title": title, "extract": text, "description": "", "thumbnail": ""}
        return None

    @staticmethod
    def article_plaintext(html: str, max_chars: int = 6000) -> str:
        """Crude but dependable HTML → text for quiz/tutor generation."""
        html = re.sub(r"(?is)<(script|style|table|figure|sup)[^>]*>.*?</\1>", " ", html)
        # Keep only paragraph contents to skip nav chrome.
        paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", html)
        text = " ".join(paras) if paras else html
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = (
            text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&#39;", "'").replace("&quot;", '"').replace("&nbsp;", " ")
        )
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]

    @staticmethod
    def _norm(title: str) -> str:
        return title.replace("_", " ").strip()

    def _cache_get(self, title: str, lang: str) -> Optional[Dict]:
        with _db_lock, self._conn() as c:
            row = c.execute(
                "SELECT html, lang FROM article_cache WHERE title=? AND html != ''",
                (self._norm(title),),
            ).fetchone()
        if not row:
            return None
        return {
            "title": self._norm(title),
            "html": row[0],
            "source": "cache",
            "archive": None,
            "base": "",
            "simple": row[1] == "simple",
        }

    def _fetch_live(self, title: str, lang: str) -> Optional[Dict]:
        try:
            url = "https://{}.wikipedia.org/api/rest_v1/page/html/{}".format(
                lang, urllib.parse.quote(title.replace(" ", "_"), safe="")
            )
            html = _http_get(url, timeout=20).decode("utf-8", errors="replace")
        except Exception as exc:
            # Distinguish "no such article" from "we are offline".
            code = getattr(exc, "code", None)
            if code == 404:
                log.info("no live article for %r (%s)", title[:60], lang)
            else:
                log.info("live fetch failed for %r: %s", title[:60], exc.__class__.__name__)
            return None
        with _db_lock, self._conn() as c:
            c.execute(
                """INSERT INTO article_cache(title, lang, html, summary, fetched_at)
                   VALUES(?,?,?,'',?)
                   ON CONFLICT(title) DO UPDATE SET html=excluded.html, lang=excluded.lang""",
                (self._norm(title), lang, html, time.time()),
            )
        return {
            "title": self._norm(title),
            "html": html,
            "source": "live",
            "archive": None,
            "base": "",
            "simple": lang == "simple",
        }

    # ---------- search ----------

    def search(self, query: str, limit: int = 14, live: bool = False) -> List[Dict]:
        results: List[Dict] = []
        seen = set()
        for arc in self.archives:
            for r in arc.suggest(query, limit):
                key = r["title"].lower()
                if key not in seen:
                    seen.add(key)
                    results.append(r)
            if len(results) >= limit:
                break
        # Full-text fallback is much slower than the suggestion index on a
        # 400k+ article ZIM (0.3–1.4s), so only reach for it when title
        # suggestions came up nearly empty, the query looks deliberate rather
        # than mid-typing, and only on the largest archive.
        if len(results) < 4 and self.archives:
            for arc in self.archives[:1]:
                for r in arc.search_fulltext(query, limit - len(results)):
                    key = r["title"].lower()
                    if key not in seen:
                        seen.add(key)
                        results.append(r)
        # The live lookup is the expensive part (0.7–0.9s). It only runs when
        # the reader has committed to a query, is memoised, and trips a
        # circuit-breaker while offline so search stays instant either way.
        if len(results) < 5 and live:
            for t in self._live_search(query, limit):
                if t.lower() not in seen:
                    seen.add(t.lower())
                    results.append({"title": t, "path": "", "source": "live"})
        return results[:limit]

    def _live_search(self, query: str, limit: int) -> List[str]:
        key = query.strip().lower()
        with _search_lock:
            if key in _live_cache:
                return _live_cache[key]
            if time.time() < self._live_search_blocked_until:
                return []
        try:
            url = (
                "https://en.wikipedia.org/w/api.php?action=opensearch&format=json"
                "&limit={}&search={}".format(limit, urllib.parse.quote(query))
            )
            titles = _http_get_json(url, timeout=4)[1]
        except Exception as exc:
            # Offline (or slow): stop trying for a while rather than making every
            # keystroke wait for a timeout.
            self._live_search_blocked_until = time.time() + 60
            log.info("live search unavailable (%s); pausing for 60s", exc.__class__.__name__)
            return []
        with _search_lock:
            if len(_live_cache) > 500:
                _live_cache.clear()
            _live_cache[key] = titles
        return titles

    def random_article(self) -> Optional[str]:
        for arc in self.archives:
            t = arc.random_title()
            if t:
                return t
        try:
            data = _http_get_json(
                "https://en.wikipedia.org/api/rest_v1/page/random/summary", timeout=8
            )
            return data.get("title")
        except Exception as exc:
            log.info("random article unavailable: %s", exc.__class__.__name__)
            return None

    # ---------- images ----------

    @staticmethod
    def _image_host_allowed(url: str) -> bool:
        """Only fetch images from Wikimedia hosts — parse the host, don't regex
        the whole URL (which let `evil.com/a.wikipedia.org/` and metadata IPs
        through). Blocks SSRF to internal/link-local addresses."""
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            return False
        if parsed.scheme not in ("http", "https"):
            return False
        host = (parsed.hostname or "").lower()
        return (
            host == "upload.wikimedia.org"
            or host.endswith(".wikipedia.org")
            or host.endswith(".wikimedia.org")
        )

    class _StrictRedirect(urllib.request.HTTPRedirectHandler):
        """Re-validate the host on every redirect hop — otherwise an allowed
        host could bounce the fetch to an internal address."""

        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if not WikiService._image_host_allowed(newurl):
                log.warning("blocked redirect to disallowed host: %s", newurl[:120])
                return None
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    MAX_IMAGE_BYTES = 8 * 1024 * 1024

    def proxy_image(self, url: str) -> Optional[Tuple[bytes, str]]:
        if not self._image_host_allowed(url):
            log.warning("blocked image fetch to disallowed host: %s", url[:120])
            return None
        with _db_lock, self._conn() as c:
            row = c.execute("SELECT data, mime FROM image_cache WHERE url=?", (url,)).fetchone()
        if row:
            return row[0], row[1]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            opener = urllib.request.build_opener(self._StrictRedirect())
            with opener.open(req, timeout=20) as resp:
                # Bounded read: never buffer an unbounded remote response.
                data = resp.read(self.MAX_IMAGE_BYTES + 1)
                if len(data) > self.MAX_IMAGE_BYTES:
                    log.warning("image too large, refused: %s", url[:120])
                    return None
                mime = resp.headers.get("Content-Type", "image/jpeg")
        except Exception as exc:
            log.info("image fetch failed (%s): %s", exc.__class__.__name__, url[:120])
            return None
        if len(data) < 4 * 1024 * 1024:
            with _db_lock, self._conn() as c:
                c.execute(
                    "INSERT OR REPLACE INTO image_cache(url, data, mime, fetched_at) VALUES(?,?,?,?)",
                    (url, data, mime, time.time()),
                )
        return data, mime

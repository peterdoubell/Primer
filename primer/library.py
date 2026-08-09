"""Library manager: catalog of knowledge archives and a background downloader.

The Primer's shelf. Each catalog entry is a ZIM archive on download.kiwix.org;
filenames carry dates, so we resolve the newest matching file at download time.
Downloads stream to .part files with resumable byte-ranges and live progress.
"""

import logging
import os
import re
import threading
import urllib.request
from typing import Dict, List, Optional

from .wiki import CONTENT_DIR, USER_AGENT, _http_get

log = logging.getLogger("primer.library")

CATALOG = [
    {
        "key": "wikipedia_en_all_maxi",
        "dir": "wikipedia",
        "prefix": "wikipedia_en_all_maxi_",
        "title": "Wikipedia (English, complete, with images)",
        "blurb": "Every English Wikipedia article with images. The whole book. ~110 GB.",
        "approx_gb": 110,
    },
    {
        "key": "wikipedia_en_all_nopic",
        "dir": "wikipedia",
        "prefix": "wikipedia_en_all_nopic_",
        "title": "Wikipedia (English, complete, text only)",
        "blurb": "Every English Wikipedia article, no images. ~60 GB.",
        "approx_gb": 60,
    },
    {
        "key": "wikipedia_en_all_mini",
        "dir": "wikipedia",
        "prefix": "wikipedia_en_all_mini_",
        "title": "Wikipedia (English, complete, introductions)",
        "blurb": "Introduction + infobox for every English article. ~12 GB.",
        "approx_gb": 12,
    },
    {
        "key": "wikipedia_en_simple_all_maxi",
        "dir": "wikipedia",
        "prefix": "wikipedia_en_simple_all_maxi_",
        "title": "Simple English Wikipedia (with images)",
        "blurb": "The entire Simple English Wikipedia — ideal for young readers. ~3 GB.",
        "approx_gb": 3.3,
    },
    {
        "key": "wikipedia_en_simple_all_nopic",
        "dir": "wikipedia",
        "prefix": "wikipedia_en_simple_all_nopic_",
        "title": "Simple English Wikipedia (text only)",
        "blurb": "The entire Simple English Wikipedia, no images. ~1 GB.",
        "approx_gb": 0.94,
    },
    {
        "key": "wiktionary_en_all_nopic",
        "dir": "wiktionary",
        "prefix": "wiktionary_en_all_nopic_",
        "title": "Wiktionary (English dictionary)",
        "blurb": "Every word: definitions, etymology, pronunciation. ~7 GB.",
        "approx_gb": 7,
    },
    {
        "key": "wikibooks_en_all_nopic",
        "dir": "wikibooks",
        "prefix": "wikibooks_en_all_nopic_",
        "title": "Wikibooks (open textbooks)",
        "blurb": "Free textbooks across every subject. ~4 GB.",
        "approx_gb": 4,
    },
    {
        "key": "wikiversity_en_all_nopic",
        "dir": "wikiversity",
        "prefix": "wikiversity_en_all_nopic_",
        "title": "Wikiversity (courses)",
        "blurb": "University-style open courses and exercises. ~2 GB.",
        "approx_gb": 2,
    },
    {
        "key": "wikiquote_en_all_nopic",
        "dir": "wikiquote",
        "prefix": "wikiquote_en_all_nopic_",
        "title": "Wikiquote",
        "blurb": "Sourced quotations from history's voices. ~0.4 GB.",
        "approx_gb": 0.4,
    },
]

_downloads: Dict[str, Dict] = {}
_dl_lock = threading.Lock()


def resolve_latest_url(entry: Dict) -> Optional[str]:
    """Find the newest dated file for a catalog prefix."""
    listing_url = "https://download.kiwix.org/zim/{}/".format(entry["dir"])
    try:
        html = _http_get(listing_url, timeout=20).decode("utf-8", errors="replace")
    except Exception:
        return None
    pattern = 'href="({}[0-9-]+\\.zim)"'.format(re.escape(entry["prefix"]))
    matches = sorted(set(re.findall(pattern, html)))
    if not matches:
        return None
    return listing_url + matches[-1]


def start_download(key: str) -> Dict:
    entry = next((e for e in CATALOG if e["key"] == key), None)
    if entry is None:
        return {"error": "unknown catalog key"}
    with _dl_lock:
        st = _downloads.get(key)
        if st and st["status"] == "downloading":
            return st
    url = resolve_latest_url(entry)
    if not url:
        return {"error": "could not resolve download URL (offline?)"}
    dest = os.path.join(CONTENT_DIR, key + ".zim")
    if os.path.exists(dest):
        return {"status": "done", "key": key, "file": dest}
    state = {
        "key": key, "status": "downloading", "url": url,
        "bytes": 0, "total": 0, "error": "",
    }
    with _dl_lock:
        _downloads[key] = state
    t = threading.Thread(target=_download_worker, args=(state, url, dest), daemon=True)
    t.start()
    return state


def _download_worker(state: Dict, url: str, dest: str):
    part = dest + ".part"
    try:
        existing = os.path.getsize(part) if os.path.exists(part) else 0
        headers = {"User-Agent": USER_AGENT}
        if existing:
            headers["Range"] = "bytes={}-".format(existing)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            # A 206 body is only the remaining bytes, so the file total is
            # Content-Length plus what we already have. A 200 means the server
            # ignored our Range: the body is the whole file, the .part restarts
            # from zero, and the previously downloaded bytes must NOT be added
            # to the total (they are being discarded, not kept).
            resumed = bool(existing) and resp.status == 206
            length = int(resp.headers.get("Content-Length", 0))
            state["total"] = length + existing if resumed else length
            state["bytes"] = existing if resumed else 0
            mode = "ab" if resumed else "wb"
            with open(part, mode) as f:
                while True:
                    chunk = resp.read(1024 * 512)
                    if not chunk:
                        break
                    f.write(chunk)
                    state["bytes"] += len(chunk)
        os.rename(part, dest)
        state["status"] = "done"
    except Exception as exc:  # keep .part for resume
        state["status"] = "error"
        state["error"] = str(exc)
        # This background thread has no request to tag with a correlation
        # id — the same reason _maintenance_loop logs its own failures
        # explicitly rather than relying on request-scoped logging to catch
        # them. Without this, a multi-GB download (up to 110 GB) could fail
        # hours in with zero trace in the server logs; the only way to
        # discover it was to actively poll GET /api/library.
        log.error("download failed for %s: %s: %s", state["key"], exc.__class__.__name__, exc)


def downloads_status() -> List[Dict]:
    with _dl_lock:
        return [dict(v) for v in _downloads.values()]


def catalog_with_status() -> List[Dict]:
    out = []
    for entry in CATALOG:
        dest = os.path.join(CONTENT_DIR, entry["key"] + ".zim")
        item = dict(entry)
        item["installed"] = os.path.exists(dest)
        with _dl_lock:
            st = _downloads.get(entry["key"])
        if st:
            item["download"] = dict(st)
        out.append(item)
    return out

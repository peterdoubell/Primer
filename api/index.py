"""Vercel serverless entry: the whole book as one ASGI function.

The reader's record lives in Turso (libSQL) whenever TURSO_DATABASE_URL is
set, which the Vercel marketplace integration provides. That is the whole
point of it being there: /tmp on a serverless instance is per-instance and
short-lived, so a profile written by one request was routinely gone by the
next — the reader met a "no profile" page having onboarded a minute earlier.
primer/store.py makes the choice per connection, so nothing here has to know
which backend won.

PRIMER_DB still points somewhere writable because it names the local file
used when no Turso URL is configured, and because the article cache and any
downloaded archive need a real directory either way. Neither survives an
instance; both are caches that rebuild from Wikipedia, unlike the record.
"""
import os
import sys

os.environ.setdefault("PRIMER_DB", "/tmp/primer.db")
os.environ.setdefault("PRIMER_CONTENT_DIR", "/tmp/content")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer.server import app  # noqa: E402,F401

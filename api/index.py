"""Vercel serverless entry: the whole book as one ASGI function.

The bundle's filesystem is read-only, so everything the book writes — the
reader's database, its backups, any downloaded archives — is pointed at
/tmp before the server module computes its paths. /tmp lives only as long
as the warm instance: this deployment is the demo reading room, not the
archive. A reader's real, permanent book runs locally with its own
content/ directory.
"""
import os
import sys

os.environ.setdefault("PRIMER_DB", "/tmp/primer.db")
os.environ.setdefault("PRIMER_CONTENT_DIR", "/tmp/content")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer.server import app  # noqa: E402,F401

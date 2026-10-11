"""Compression for the hosted book, on the book's own text only.

Nothing the book served was compressed. The shell pulls about 2.8 MB of
JavaScript and CSS, and on Vercel every one of those files is served by the
Python function — vercel.json routes /app/* there so they stay behind the
reader gate — so all of it crossed the wire at full size. Compressing it takes
the shell to roughly 0.8 MB and the curriculum map from 531 KB to 110 KB.

Two decisions shape this, and both are deliberate.

It is an ALLOW-list, by path. A content-type exclusion list fails open: every
new kind of file is compressed until somebody remembers to exclude it. The
first cut did exactly that — it double-encoded the radiology study series and
then put a Content-Encoding on reviewed source PDFs whose delivery contract is
"the exact original bytes, no encoding". The book's own text (scripts,
styles, HTML, JSON) is what is worth compressing; source media, anatomy, study
volumes and images are left precisely as they are written.

It lives HERE and is applied in the Vercel entrypoint, not inside
primer/server.py. Reviewed radiology records pin that file's SHA-256 as the
backend they verified (docs/acute-stroke-reader-review-20261011/), and editing
it would make those records false. The reviewed backend is untouched; this is a
transport layer around it.
"""

import os

from starlette.middleware.gzip import DEFAULT_EXCLUDED_CONTENT_TYPES, GZipMiddleware

# The book's own text. Anything else under /app/ passes through untouched.
_TEXT_SUFFIXES = (".js", ".css", ".html", ".json", ".svg", ".webmanifest", ".txt", ".map")
# Source material with its own delivery contracts: exact originals, reviewed
# bodies, build-time-encoded meshes, raster media. Never compressed, whatever
# their suffix — a reviewed reference.html is still a reviewed body.
_UNTOUCHED_PREFIXES = ("/app/anatomy/", "/app/reference-media/", "/app/studies/",
                       "/app/illustrations/", "/source-media/")


def compressible(path: str) -> bool:
    """Whether a request path is the book's own text."""
    if path in ("/", "/app", "/app/") or path.startswith("/api/"):
        return True
    if not path.startswith("/app/") or path.startswith(_UNTOUCHED_PREFIXES):
        return False
    return os.path.splitext(path)[1].lower() in _TEXT_SUFFIXES


class TextCompression:
    """Gzip the book's own text; pass everything else through unchanged."""

    def __init__(self, app):
        self.app = app
        # The content-type exclusions still apply inside the allow-list, as a
        # second guard: an /api route that answers with an image or a binary
        # payload is not recompressed either.
        self._gzip = GZipMiddleware(
            app, minimum_size=1024, compresslevel=6,
            exclude_content_types=DEFAULT_EXCLUDED_CONTENT_TYPES
            + ("application/octet-stream", "application/pdf"))

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and compressible(scope.get("path", "")):
            await self._gzip(scope, receive, send)
        else:
            await self.app(scope, receive, send)

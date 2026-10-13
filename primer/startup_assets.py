"""Consolidate the hosted book's startup text without changing source assets.

The extra asset routes still run through the book's authentication middleware.
Only successful book-shell HTML is rewritten; source viewers and API bodies
pass through unchanged. Original individual files remain available for source
verification and local development.
"""
import hashlib
import re
from pathlib import Path

from fastapi import Request
from fastapi.responses import Response
from fastapi.routing import APIRoute

_SCRIPT = re.compile(rb'<script src="/app/([\w-]+\.js)(?:\?[^"<>]*)?"></script>')
_STYLE = re.compile(rb'<link rel="stylesheet" href="/app/([\w-]+\.css)(?:\?[^"<>]*)?">')
_SHELL_PATHS = {"/", "/app/", "/app/index.html"}


class StartupAssets:
    def __init__(self, book, web_dir):
        self.app = book
        directory = Path(web_dir)
        index = (directory / "index.html").read_bytes()
        self.bundles = {}
        for kind, pattern, separator, media_type in (
            ("js", _SCRIPT, b"\n;\n", "text/javascript"),
            ("css", _STYLE, b"\n", "text/css"),
        ):
            names = pattern.findall(index)
            if not names:
                raise ValueError("Missing startup " + kind + " assets")
            body = separator.join((directory / name.decode()).read_bytes() for name in names)
            if kind == "js":
                body = b"'use strict';\n" + body
            digest = hashlib.sha256(body).hexdigest()[:16]
            self.bundles[kind] = {"body": body, "digest": digest, "media_type": media_type,
                                  "names": names}

        async def javascript(request: Request):
            return self.asset_response("js", request)

        async def stylesheet(request: Request):
            return self.asset_response("css", request)

        # Insert before the /app static mount, inside the existing access guard.
        book.router.routes[0:0] = [
            APIRoute("/app/startup.js", javascript, methods=["GET", "HEAD"], include_in_schema=False),
            APIRoute("/app/startup.css", stylesheet, methods=["GET", "HEAD"], include_in_schema=False),
        ]

    def asset_response(self, kind, request):
        asset = self.bundles[kind]
        versioned = request.query_params.get("v") == asset["digest"]
        headers = {"Cache-Control": "private, max-age=31536000, immutable" if versioned
                   else "private, no-cache", "ETag": 'W/"' + asset["digest"] + '"'}
        if request.headers.get("if-none-match") == headers["ETag"]:
            return Response(status_code=304, headers=headers)
        return Response(asset["body"], media_type=asset["media_type"], headers=headers)

    def rewrite(self, body):
        # Fail closed to the original shell if its asset inventory differs.
        if (_SCRIPT.findall(body) != self.bundles["js"]["names"]
                or _STYLE.findall(body) != self.bundles["css"]["names"]):
            return body
        for kind, pattern in (("css", _STYLE), ("js", _SCRIPT)):
            asset = self.bundles[kind]
            url = '/app/startup.' + kind + '?v=' + asset["digest"]
            tag = ('<script defer src="' + url + '"></script>' if kind == "js"
                   else '<link rel="stylesheet" href="' + url + '">').encode()
            first = True

            def replace(match):
                nonlocal first
                if first:
                    first = False
                    return tag
                return b""

            body = pattern.sub(replace, body)
        return body

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("path") not in _SHELL_PATHS:
            return await self.app(scope, receive, send)
        start = None
        chunks = []

        async def shell_send(message):
            nonlocal start
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                if message["status"] == 200 and headers.get(b"content-type", b"").startswith(b"text/html"):
                    start = message
                    return
            elif message["type"] == "http.response.body" and start is not None:
                chunks.append(message.get("body", b""))
                if message.get("more_body", False):
                    return
                body = self.rewrite(b"".join(chunks))
                headers = [(key, value) for key, value in start["headers"] if key != b"content-length"]
                headers.append((b"content-length", str(len(body)).encode()))
                await send(dict(start, headers=headers))
                await send(dict(message, body=body))
                return
            await send(message)

        await self.app(scope, receive, shell_send)

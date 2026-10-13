"""Hosted startup bundles keep ordering, cache versions and the access gate."""
import hashlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.testclient import TestClient

from primer.startup_assets import StartupAssets

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    book = FastAPI()

    @book.middleware("http")
    async def gate(request, call_next):
        if request.headers.get("x-test-reader") != "signed-in":
            return JSONResponse({"error": "sign in"}, status_code=401)
        response = await call_next(request)
        response.headers["content-security-policy"] = "script-src 'self'"
        return response

    @book.get("/")
    @book.get("/app/")
    @book.get("/app/index.html")
    def shell():
        return HTMLResponse((ROOT / "web/index.html").read_text(), headers={"cache-control": "no-cache"})

    @book.get("/app/anatomy/reference.html")
    def source():
        return HTMLResponse('<script src="/app/app.js"></script>')

    @book.get("/api/example")
    def api():
        return {"body": '<script src="/app/app.js"></script>'}

    assets = StartupAssets(book, ROOT / "web")
    return assets, TestClient(assets)


def test_shell_has_two_versioned_startup_requests_in_original_order():
    assets, client = fixture()
    for path in ("/", "/app/", "/app/index.html"):
        response = client.get(path, headers={"x-test-reader": "signed-in"})
        assert response.status_code == 200
        assert response.text.count('<script ') == 1
        assert response.text.count('rel="stylesheet"') == 1
        assert '<script defer src="/app/startup.js?v=' in response.text
        assert response.headers["content-security-policy"] == "script-src 'self'"
        assert int(response.headers["content-length"]) == len(response.content)
    for kind in ("js", "css"):
        bundle = assets.bundles[kind]
        last = 0
        for name in bundle["names"]:
            original = (ROOT / "web" / name.decode()).read_bytes()
            offset = bundle["body"].index(original, last)
            assert offset >= last
            last = offset + len(original)
        assert bundle["digest"] == hashlib.sha256(bundle["body"]).hexdigest()[:16]


def test_bundles_stay_authenticated_and_only_current_versions_are_immutable():
    assets, client = fixture()
    for kind in ("js", "css"):
        path = '/app/startup.' + kind
        assert client.get(path).status_code == 401
        headers = {"x-test-reader": "signed-in"}
        current = client.get(path + '?v=' + assets.bundles[kind]["digest"], headers=headers)
        assert "private" in current.headers["cache-control"]
        assert "immutable" in current.headers["cache-control"]
        assert current.content == assets.bundles[kind]["body"]
        assert client.get(path, headers=headers).headers["cache-control"] == "private, no-cache"
        assert client.get(path + '?v=old', headers=headers).headers["cache-control"] == "private, no-cache"
        assert client.get(path, headers=dict(headers, **{"if-none-match": current.headers["etag"]})).status_code == 304


def test_non_shell_content_and_unknown_asset_inventories_are_unchanged():
    assets, client = fixture()
    headers = {"x-test-reader": "signed-in"}
    assert client.get('/app/anatomy/reference.html', headers=headers).content == b'<script src="/app/app.js"></script>'
    assert client.get('/api/example', headers=headers).json()["body"] == '<script src="/app/app.js"></script>'
    unknown = b'<html><script src="/app/unknown.js"></script></html>'
    assert assets.rewrite(unknown) == unknown


def test_actual_hosted_book_guard_protects_the_new_asset_routes(monkeypatch):
    import primer.server as server
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('PRIMER_ACCESS_USERNAME', 'qa')
    monkeypatch.setenv('PRIMER_ACCESS_PASSWORD', 'performance-qa-only')
    assets = StartupAssets(server.app, ROOT / 'web')
    with TestClient(assets) as client:
        for path in ['/app/startup.js', '/app/startup.css', '/app/']:
            assert client.get(path, headers={'accept': 'application/json'}).status_code == 401

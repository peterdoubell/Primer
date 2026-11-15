"""Authored lessons must remain available without live encyclopedia services."""

import json
import io
from urllib.error import HTTPError

import pytest

from primer import wiki as wiki_module
from primer.wiki import WikiService


@pytest.fixture
def cached_wiki(tmp_path, monkeypatch):
    # No real reader data, downloaded archives, or remote database is used.
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.setattr(wiki_module, "CONTENT_DIR", str(tmp_path / "content"))
    service = WikiService(str(tmp_path / "cache.db"))

    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("cache-only metadata attempted a live fetch")

    monkeypatch.setattr(wiki_module, "_http_get", unexpected_fetch)
    monkeypatch.setattr(wiki_module, "_http_get_json", unexpected_fetch)
    monkeypatch.setattr(service, "get_article", unexpected_fetch)
    return service


def seed_summary(service, title, summary, lang="en"):
    with service._conn() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO article_cache "
            "(title,lang,html,summary,fetched_at) VALUES(?,?,'',?,0)",
            (title, lang, summary),
        )


def test_cached_summary_miss_never_fetches(cached_wiki):
    assert cached_wiki.get_cached_summary("Ultrasound") is None


def test_cached_summary_is_language_exact_and_ignores_staleness(cached_wiki):
    saved = {"title": "Ultrasound", "extract": "Saved explanation.",
             "description": "Sound imaging", "thumbnail": "https://upload.wikimedia.org/example.jpg"}
    seed_summary(cached_wiki, "Ultrasound", json.dumps(saved), "simple")
    assert cached_wiki.get_cached_summary("Ultrasound", "en") is None
    assert cached_wiki.get_cached_summary("Ultrasound", "simple") == saved
    assert cached_wiki.get_summary("Ultrasound", "simple") == saved


@pytest.mark.parametrize("saved", ["{broken", "null", "[]", "12", '"text"'])
def test_malformed_summary_is_a_cache_miss(cached_wiki, saved):
    seed_summary(cached_wiki, "Ultrasound", saved)
    assert cached_wiki.get_cached_summary("Ultrasound") is None


def test_cached_summary_fields_are_safe_strings(cached_wiki):
    seed_summary(cached_wiki, "Ultrasound", json.dumps({
        "extract": ["invalid"], "description": None, "thumbnail": {"source": "invalid"},
    }))
    assert cached_wiki.get_cached_summary("Ultrasound") == {
        "title": "Ultrasound", "extract": "", "description": "", "thumbnail": "",
    }


@pytest.fixture
def local_app(tmp_path, monkeypatch, cached_wiki):
    # Set the import-time paths too, in case this module is run by itself.
    monkeypatch.setenv("PRIMER_DB", str(tmp_path / "boot.db"))
    monkeypatch.setenv("PRIMER_CONTENT_DIR", str(tmp_path / "content"))
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("PRIMER_ACCESS_PASSWORD", raising=False)
    import primer.server as server
    from fastapi.testclient import TestClient
    from primer.learner import LearnerStore

    monkeypatch.setattr(server, "learner", LearnerStore(str(tmp_path / "learner.db")))
    monkeypatch.setattr(server, "wiki", cached_wiki)

    def unexpected_summary(*args, **kwargs):
        raise AssertionError("lesson requested a live summary")

    monkeypatch.setattr(cached_wiki, "get_summary", unexpected_summary)
    # No lifespan: this read-only route does not need background maintenance.
    client = TestClient(server.app)
    yield client, server
    client.close()


@pytest.mark.parametrize("node_id", ["rad.5.ultrasound-physics", "bio.3.genetics", "math.3.trig"])
def test_local_lesson_and_visuals_do_not_wait_for_wikipedia(local_app, node_id):
    client, server = local_app
    node = server.curr.node(node_id)
    response = client.get("/api/curriculum/node/" + node_id)
    assert response.status_code == 200
    payload = response.json()
    assert payload["lesson_media"] == node["lesson_media"]
    assert payload["article_cards"] == [
        {"title": title, "summary": "", "thumb": ""}
        for title in node["articles"][:6]
    ]


def test_local_lesson_keeps_cached_card_metadata(local_app, cached_wiki):
    client, server = local_app
    node = server.curr.node("rad.5.ultrasound-physics")
    title = node["articles"][0]
    seed_summary(cached_wiki, title, json.dumps({
        "extract": "x" * 400, "thumbnail": "https://upload.wikimedia.org/example.jpg",
    }))
    payload = client.get("/api/curriculum/node/" + node["id"]).json()
    assert payload["article_cards"][0] == {
        "title": title, "summary": "x" * 280,
        "thumb": "https://upload.wikimedia.org/example.jpg",
    }


def test_optional_cache_failure_cannot_hide_lesson(local_app, cached_wiki, monkeypatch):
    client, server = local_app

    def unavailable(*args, **kwargs):
        raise OSError("optional cache unavailable")

    monkeypatch.setattr(cached_wiki, "get_cached_summary", unavailable)
    response = client.get("/api/curriculum/node/rad.5.ultrasound-physics")
    assert response.status_code == 200
    assert response.json()["lesson_media"]
    assert all(card["summary"] == card["thumb"] == "" for card in response.json()["article_cards"])


@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_upstream_server_errors_back_off_instead_of_becoming_missing_articles(monkeypatch, code):
    monkeypatch.setattr(wiki_module.time, "time", lambda: 1000)
    service = WikiService.__new__(WikiService)
    service._live_fetch_blocked_until = 0
    service._note_live_failure(HTTPError("https://en.wikipedia.org", code, "unavailable", {}, None))
    assert service._live_fetch_blocked_until == 1060


def test_not_found_does_not_block_other_articles(monkeypatch):
    service = WikiService.__new__(WikiService)
    service._live_fetch_blocked_until = 0
    service._note_live_failure(HTTPError("https://en.wikipedia.org", 404, "missing", {}, None))
    assert service._live_fetch_blocked_until == 0


@pytest.mark.parametrize("code,expected", [(500, 503), (502, 503), (504, 503), (404, 404)])
def test_article_api_distinguishes_upstream_failure_from_missing_page(
        local_app, cached_wiki, monkeypatch, code, expected):
    client, server = local_app
    monkeypatch.setattr(cached_wiki, "get_article", WikiService.get_article.__get__(cached_wiki))

    def unavailable(url, **kwargs):
        raise HTTPError(url, code, "upstream failure", {}, None)

    monkeypatch.setattr(wiki_module, "_http_get", unavailable)
    response = client.get("/api/article", params={"title": "Not cached", "log_read": "false"})
    assert response.status_code == expected
    if expected == 503:
        assert int(response.headers["Retry-After"]) > 0
        assert response.json()["error"] == "article temporarily unavailable"


def serve_image(monkeypatch, data, headers):
    calls = []

    class UpstreamResponse(io.BytesIO):
        def __init__(self):
            super().__init__(data)
            self.headers = headers

    class Opener:
        def open(self, request, timeout=20):
            calls.append(request.full_url)
            return UpstreamResponse()

    monkeypatch.setattr(wiki_module.urllib.request, "build_opener", lambda *args: Opener())
    return calls


@pytest.mark.parametrize("data,headers", [
    (b"<html>unavailable</html>", {}),
    (b"", {"Content-Type": "image/png"}),
    (b"<html>unavailable</html>", {"Content-Type": "text/html"}),
])
def test_invalid_image_response_is_not_saved_as_permanent_broken_photo(
        cached_wiki, monkeypatch, data, headers):
    serve_image(monkeypatch, data, headers)
    assert cached_wiki.proxy_image("https://upload.wikimedia.org/test.png") is None
    with cached_wiki._conn() as connection:
        assert connection.execute("SELECT COUNT(*) FROM image_cache").fetchone()[0] == 0


@pytest.mark.parametrize("old_data,old_mime", [(b"", "image/png"), (b"error", "text/html")])
def test_invalid_cached_image_is_replaced_by_a_good_upstream_image(
        cached_wiki, monkeypatch, old_data, old_mime):
    url = "https://upload.wikimedia.org/test.png"
    with cached_wiki._conn() as connection:
        connection.execute(
            "INSERT INTO image_cache (url,data,mime,fetched_at) VALUES(?,?,?,0)",
            (url, old_data, old_mime),
        )
    good_data = b"\x89PNG\r\n\x1a\nexample"
    calls = serve_image(monkeypatch, good_data, {"Content-Type": "image/png"})
    assert cached_wiki.proxy_image(url) == (good_data, "image/png")
    assert cached_wiki.proxy_image(url) == (good_data, "image/png")
    assert calls == [url]

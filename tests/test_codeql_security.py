"""Regression coverage for the CodeQL security findings fixed in this pass."""

import io
import json

import pytest
from starlette.requests import Request

import primer.render as render
import primer.wiki as wiki
from primer.wiki import WikiService


@pytest.mark.parametrize("url", [
    "http://upload.wikimedia.org/a.png",
    "https://attacker.wikimedia.org/a.png",
    "https://thumb.wikimedia.org.evil.test/a.png",
    "https://upload.wikimedia.org.evil.test/a.png",
    "https://upload.wikimedia.org@127.0.0.1/a.png",
    "https://upload.wikimedia.org:444/a.png",
    "https://upload.wikimedia.org/ok.png\r\nX-Evil: yes",
])
def test_image_proxy_rejects_caller_controlled_authorities(url):
    assert WikiService._validated_image_url(url) is None


def test_image_proxy_rebuilds_a_canonical_server_owned_url(tmp_path, monkeypatch):
    monkeypatch.setattr(wiki, "CONTENT_DIR", str(tmp_path / "content"))
    service = WikiService(str(tmp_path / "wiki.db"))
    seen = []

    class Response(io.BytesIO):
        headers = {"Content-Type": "image/png"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class Opener:
        def open(self, request, timeout=20):
            seen.append((request.full_url, timeout))
            return Response(b"png")

    monkeypatch.setattr(wiki.urllib.request, "build_opener", lambda *_args: Opener())
    supplied = "https://UPLOAD.WIKIMEDIA.ORG:443/a b.png?width=20#ignored"

    assert service.proxy_image(supplied) == (b"png", "image/png")
    assert seen == [("https://upload.wikimedia.org/a%20b.png?width=20", 20)]
    with wiki._db_lock, service._conn() as conn:
        keys = [row[0] for row in conn.execute("SELECT url FROM image_cache")]
    assert keys == ["https://upload.wikimedia.org/a%20b.png?width=20"]


def test_image_proxy_canonicalizes_the_exact_thumbnail_origin():
    supplied = "https://THUMB.WIKIMEDIA.ORG:443/a b.png?width=20#ignored"
    assert WikiService._validated_image_url(supplied) == (
        "https://thumb.wikimedia.org/a%20b.png?width=20"
    )


def test_image_proxy_revalidates_and_canonicalizes_redirects():
    handler = WikiService._StrictRedirect()
    request = wiki.urllib.request.Request("https://upload.wikimedia.org/start")

    blocked = handler.redirect_request(
        request, None, 302, "Found", {}, "http://127.0.0.1/metadata"
    )
    allowed = handler.redirect_request(
        request, None, 302, "Found", {},
        "https://UPLOAD.WIKIMEDIA.ORG:443/next image.png#ignored",
    )

    assert blocked is None
    assert allowed.full_url == "https://upload.wikimedia.org/next%20image.png"


def test_generic_wiki_fetch_reads_only_the_configured_limit(monkeypatch):
    reads = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, amount):
            reads.append(amount)
            return b"x" * amount

    monkeypatch.setattr(wiki, "MAX_HTTP_BYTES", 8)
    monkeypatch.setattr(wiki.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())

    with pytest.raises(ValueError, match="remote response exceeds"):
        wiki._http_get("https://en.wikipedia.org/api/rest_v1/page/html/Test")
    assert reads == [9]


@pytest.mark.parametrize("tag", ["script", "style"])
def test_malformed_active_tags_are_dropped_by_the_parser(tag):
    hostile = (
        "<p>before</p><{0}>alert(1)</{0} data-broken=yes>"
        "<p>after</p>".format(tag)
    )
    output = render.rewrite_article(hostile)

    assert "before" in output and "after" in output
    assert "alert(1)" not in output
    assert "<{}".format(tag) not in output.lower()


def test_parser_failure_uses_a_linear_escaped_text_fallback(monkeypatch):
    def fail(_self, _html):
        raise ValueError("synthetic parser failure")

    monkeypatch.setattr(render._Sanitizer, "feed", fail)
    output = render.sanitize('<b title=">">safe</b><script>inert')

    assert "<" not in output and ">" not in output
    assert "safe" in output


def test_incomplete_tag_runs_are_bounded_before_htmlparser():
    hostile = "<table " * 20000

    bounded = render._bound_malformed_markup(hostile)

    assert bounded == "&lt;table " * 20000
    assert render.sanitize(hostile) == bounded


def test_markup_preflight_preserves_valid_quotes_text_and_comments():
    valid = (
        '<img alt="a < b > c" src="/x.png"><p>1 < 2</p>'
        '<!-- an inert <i>example</i> -->'
    )

    assert render._bound_malformed_markup(valid) == valid


def test_tutor_reflection_is_an_explicit_json_response(monkeypatch):
    import primer.server as server

    attack = '</script><script>alert("xss")</script>'

    class Learner:
        @staticmethod
        def get_profile(reader_id=1):
            return {"stage": 2, "settings": {}}

    monkeypatch.setattr(server, "learner", Learner())
    monkeypatch.setattr(
        server.tutor,
        "ask",
        lambda *_args, **_kwargs: {"reply": attack, "remote": False},
    )

    response = server.ask_tutor(server.TutorIn(
        messages=[{"role": "user", "content": attack}],
        title=attack,
        excerpt=attack,
    ), Request(scope={"type": "http", "headers": []}))

    assert response.media_type == "application/json"
    assert json.loads(response.body)["reply"] == attack

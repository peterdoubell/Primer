"""Hosted deployment safeguards that do not depend on live infrastructure."""

import pytest
from fastapi.testclient import TestClient

import primer.server as srv
from primer.learner import LearnerStore
from primer.wiki import WikiService


@pytest.fixture(autouse=True)
def isolated_stores(tmp_path, monkeypatch):
    """Never let an app lifespan in this module touch the reader's real DB."""
    shutdown_was_set = srv._shutdown.is_set()
    db_path = str(tmp_path / "primer.db")
    monkeypatch.setattr(srv, "learner", LearnerStore(db_path))
    monkeypatch.setattr(srv, "wiki", WikiService(db_path))
    monkeypatch.setattr(srv, "BACKUP_DIR", str(tmp_path / "backups"))
    # Capture a no-op as the thread target.  Merely swapping the stores is not
    # enough: the real maintenance thread can outlive fixture teardown and
    # look the module globals up again after they have been restored.
    monkeypatch.setattr(srv, "_maintenance_loop", lambda: None)
    try:
        yield
    finally:
        if not shutdown_was_set:
            srv._shutdown.clear()


def test_vercel_fails_closed_without_an_access_password(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv(srv.ACCESS_PASSWORD_ENV, raising=False)

    with TestClient(srv.app) as client:
        assert client.get("/healthz").status_code == 200
        response = client.get("/")

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"


def test_brand_assets_are_public_without_opening_the_private_app(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    expected_types = {
        "/app/favicon.ico": "image/",
        "/app/favicon-32x32.png": "image/png",
        "/app/apple-touch-icon.png": "image/png",
        "/app/icon-192.png": "image/png",
        "/app/icon-512.png": "image/png",
        "/app/icon-1024.png": "image/png",
    }
    with TestClient(srv.app) as client:
        assets = {path: client.get(path) for path in expected_types}
        manifest = client.get("/app/manifest.webmanifest")
        private_script = client.get("/app/app.js")

    for path, response in assets.items():
        assert response.status_code == 200, path
        assert response.headers["content-type"].startswith(expected_types[path])
    assert manifest.status_code == 200
    assert manifest.json()["short_name"] == "Primer"
    assert {icon["sizes"] for icon in manifest.json()["icons"]} == {
        "192x192", "512x512",
    }
    assert private_script.status_code == 401


def test_health_exemption_cannot_be_forged_with_host_header(monkeypatch):
    """CVE-2026-48710 must not turn a protected raw path into /healthz."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv(srv.ACCESS_PASSWORD_ENV, raising=False)

    with TestClient(srv.app) as client:
        response = client.get(
            "/api/state", headers={"host": "example.com/healthz?ignored="})

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"


def test_hosted_access_password_protects_html_and_api(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "correct horse battery staple")

    with TestClient(srv.app) as client:
        challenge = client.get("/api/state")
        wrong = client.get("/api/state", auth=("reader", "wrong"))
        allowed = client.get(
            "/api/state", auth=("reader", "correct horse battery staple"))

    assert challenge.status_code == 401
    assert wrong.status_code == 401
    assert allowed.status_code == 200
    assert allowed.headers["vary"] == "Authorization, Cookie"


def test_mathematics_illustration_dashboard_stays_behind_the_hosted_gate(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    path = "/api/curriculum/mathematics/illustrations"

    with TestClient(srv.app) as client:
        denied = client.get(path)
        allowed = client.get(path, auth=("reader", "secret"))

    assert denied.status_code == 401
    assert allowed.status_code == 200
    assert allowed.json()["count"] == 59
    assert allowed.headers["vary"] == "Authorization, Cookie"


def test_challenge_never_asks_the_browser_to_draw_its_own_dialog(monkeypatch):
    """WWW-Authenticate is what summons the unstyleable native credential box."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app) as client:
        api = client.get("/api/state")
        page = client.get("/", headers={"accept": "text/html"},
                          follow_redirects=False)

    assert "www-authenticate" not in api.headers
    assert "www-authenticate" not in page.headers


def test_a_locked_out_reader_is_sent_to_the_books_own_sign_in(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app) as client:
        redirect = client.get("/api/curriculum", headers={"accept": "text/html"},
                              follow_redirects=False)
        page = client.get(srv.SIGN_IN_PATH)

    assert redirect.status_code == 303
    assert redirect.headers["location"] == "/sign-in?next=/api/curriculum"
    assert page.status_code == 200
    assert "The Primer" in page.text
    assert "Open the book" in page.text


def test_signing_in_opens_the_book_and_keeps_it_open(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    # https, because the cookie is Secure when hosted — over plain http a real
    # browser would drop it exactly as this client does.
    with TestClient(srv.app, base_url="https://testserver") as client:
        # The form has no action attribute, so a browser posts back to the
        # URL the page was served from — ?next= travels in the query string,
        # never in the page or the body.
        posted = client.post(srv.SIGN_IN_PATH + "?next=/%23atlas",
                             follow_redirects=False,
                             data={"username": "reader", "password": "secret"})
        # The cookie the redirect set is now the only credential in play.
        after = client.get("/api/state")
        signed_out = client.post("/sign-out", follow_redirects=False)
        locked = client.get("/api/state")

    assert posted.status_code == 303
    assert posted.headers["location"] == "/#atlas"
    assert posted.cookies[srv.ACCESS_COOKIE]
    assert after.status_code == 200
    assert signed_out.status_code == 303
    assert locked.status_code == 401


def test_the_unsuffixed_account_still_resolves_to_reader_one(monkeypatch):
    """Slot 1 (PRIMER_ACCESS_USERNAME/PASSWORD, unsuffixed) is the original
    single-tenant credential — signing in with it must land on reader_id=1,
    the profile every deployment already had, exactly as before this
    existed."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app, base_url="https://testserver") as client:
        client.post(srv.SIGN_IN_PATH, data={"username": "reader", "password": "secret"})
        account = client.get("/api/account").json()

    assert account["reader_id"] == 1


def test_a_second_account_opens_its_own_separate_profile(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV + "2", "reader2")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV + "2", "secret2")

    with TestClient(srv.app, base_url="https://testserver") as client:
        client.post(srv.SIGN_IN_PATH, data={"username": "reader", "password": "secret"})
        client.post("/api/profile", json={
            "name": "First", "age": 8, "hours_per_week": 6,
            "breadth": "balanced", "domains": ["math"]})
        first_account = client.get("/api/account").json()

        client.cookies.clear()
        client.post(srv.SIGN_IN_PATH, data={"username": "reader2", "password": "secret2"})
        client.post("/api/profile", json={
            "name": "Second", "age": 10, "hours_per_week": 6,
            "breadth": "balanced", "domains": ["math"]})
        second_account = client.get("/api/account").json()

    assert first_account["reader_id"] != second_account["reader_id"]
    assert second_account["reader_id"] != 1, \
        "the second account must not land on the first account's profile"

    with TestClient(srv.app, base_url="https://testserver") as client:
        client.post(srv.SIGN_IN_PATH, data={"username": "reader", "password": "secret"})
        assert client.get("/api/state").json()["profile"]["name"] == "First"
        client.cookies.clear()
        client.post(srv.SIGN_IN_PATH, data={"username": "reader2", "password": "secret2"})
        assert client.get("/api/state").json()["profile"]["name"] == "Second"


def test_switching_accounts_on_one_browser_switches_the_active_reader(monkeypatch):
    """Signing in again — even on the same cookie jar, without an explicit
    sign-out first — must move the active reader to the new account, not
    leave it pinned to whichever session cookie was set first."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV + "2", "reader2")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV + "2", "secret2")

    with TestClient(srv.app, base_url="https://testserver") as client:
        client.post(srv.SIGN_IN_PATH, data={"username": "reader", "password": "secret"})
        first_reader_id = client.get("/api/account").json()["reader_id"]

        client.post(srv.SIGN_IN_PATH, data={"username": "reader2", "password": "secret2"})
        second_reader_id = client.get("/api/account").json()["reader_id"]

    assert first_reader_id != second_reader_id


def test_a_static_account_is_not_google_signed_in_or_claimable(monkeypatch):
    """A static account already has its own permanent, password-backed
    identity — it must never read as a Google sign-in, and must never be
    offered the "claim the legacy profile" action meant for an ambiguous
    Google identity."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV + "2", "reader2")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV + "2", "secret2")

    with TestClient(srv.app, base_url="https://testserver") as client:
        client.post(srv.SIGN_IN_PATH, data={"username": "reader2", "password": "secret2"})
        account = client.get("/api/account").json()
        claim = client.post("/api/account/claim", json={"password": "secret"})

    assert account["signed_in"] is False
    assert account["claimable"] is False
    assert claim.status_code == 400


def test_rotating_one_accounts_password_does_not_sign_the_other_out(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV + "2", "reader2")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV + "2", "secret2")

    with TestClient(srv.app, base_url="https://testserver") as first:
        first.post(srv.SIGN_IN_PATH, data={"username": "reader", "password": "secret"})
        with TestClient(srv.app, base_url="https://testserver") as second:
            second.post(srv.SIGN_IN_PATH, data={"username": "reader2", "password": "secret2"})
            monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV + "2", "a new secret")
            second_after_rotation = second.get("/api/state")
        first_after_rotation = first.get("/api/state")

    assert second_after_rotation.status_code == 401
    assert first_after_rotation.status_code == 200


def test_a_wrong_word_is_refused_without_saying_which_half_was_wrong(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app) as client:
        wrong_word = client.post(srv.SIGN_IN_PATH, follow_redirects=False,
                                 data={"username": "reader", "password": "no"})
        wrong_reader = client.post(srv.SIGN_IN_PATH, follow_redirects=False,
                                   data={"username": "nobody", "password": "secret"})

    assert wrong_word.status_code == 401
    assert srv.ACCESS_COOKIE not in wrong_word.cookies
    assert wrong_reader.status_code == 401
    assert wrong_word.text == wrong_reader.text


def test_a_forged_cookie_does_not_open_the_book(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app) as client:
        client.cookies.set(srv.ACCESS_COOKIE, "0" * 64)
        response = client.get("/api/state")

    assert response.status_code == 401


def test_a_cookie_dies_with_the_password_that_signed_it(monkeypatch):
    """Rotating the password is the whole session-revocation story."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app, base_url="https://testserver") as client:
        client.post(srv.SIGN_IN_PATH, follow_redirects=False,
                    data={"username": "primer", "password": "secret"})
        still_open = client.get("/api/state")
        monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "a new secret")
        rotated = client.get("/api/state")

    assert still_open.status_code == 200
    assert rotated.status_code == 401


@pytest.mark.parametrize("hostile", [
    "https://evil.example/steal", "//evil.example/steal", "/\\evil.example",
    "/ok\r\nSet-Cookie: x=1", "not-a-path",
])
def test_next_cannot_be_bent_into_an_open_redirect(monkeypatch, hostile):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app) as client:
        # On the query string — the channel the handler actually reads now.
        # A hostile value in the body is simply ignored, which is its own
        # guarantee, but ignoring it is not what this test is here to prove.
        import urllib.parse
        posted = client.post(
            srv.SIGN_IN_PATH + "?next=" + urllib.parse.quote(hostile, safe=""),
            follow_redirects=False,
            data={"username": "primer", "password": "secret"})

    assert posted.headers["location"] == "/"


def test_hosted_access_rejects_non_ascii_credentials_without_crashing(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    with TestClient(srv.app) as client:
        response = client.get("/api/state", auth=("réader", "secret"))

    assert response.status_code == 401


def test_local_install_remains_password_free(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv(srv.ACCESS_PASSWORD_ENV, raising=False)

    with TestClient(srv.app) as client:
        assert client.get("/api/state").status_code == 200


def test_turso_reports_managed_remote_backup_status(monkeypatch):
    monkeypatch.setenv(srv.store.URL_ENV, "libsql://example.turso.io")

    status = srv.backup_status()

    assert status["mode"] == "managed_remote"
    assert status["off_disk"] is True
    assert status["dir"] is None
    assert "Turso" in status["advice"]


def test_remote_maintenance_skips_local_online_backup(monkeypatch):
    calls = []

    class Learner:
        def get_profile(self):
            return {"id": 1}

        def backup(self, *_args, **_kwargs):
            calls.append("backup")

        def prune(self):
            calls.append("prune")

    monkeypatch.setattr(srv, "learner", Learner())
    monkeypatch.setattr(srv.store, "using_turso", lambda: True)

    srv._run_maintenance_once()

    assert calls == ["prune"]


def test_safe_next_is_constructed_not_checked():
    """The bounce target is rebuilt from an allowlist, character by character.

    Checking a string and passing the original through leaves everything the
    check forgot; a constructed value contains nothing but what the allowlist
    admits, in any context it is later pasted into — the form's hidden field,
    the redirect header, or anywhere a future refactor moves it. This is also
    what lets static analysis see the sanitisation instead of being asked to
    take html.escape on faith (CodeQL flagged both sinks on the checked-and-
    passed-through version).
    """
    from primer.server import _safe_next

    # Hostile shapes are refused outright — never laundered into a cleaned
    # residue that still half-honours the attacker's aim.
    assert _safe_next("//evil.com") == "/"
    assert _safe_next("https://evil.com") == "/"
    assert _safe_next("/a b\"<script>alert(1)</script>") == "/"
    assert _safe_next("/x\r\nSet-Cookie: a=b") == "/"
    assert _safe_next("/\\/evil.com") == "/"
    assert _safe_next("///nested") == "/"
    # Everything a legitimate deep link needs survives.
    assert _safe_next("/#atlas") == "/#atlas"
    assert _safe_next("/api/today?x=1&y=2") == "/api/today?x=1&y=2"
    assert _safe_next("/%23atlas") == "/%23atlas"
    # No output ever carries a quote, an angle bracket, a control character,
    # a backslash, or a colon — by construction.
    for raw in ("/'\"<>&;:\\\x00\x1f", "/ok:8080/x", "/java\tscript:alert(1)"):
        out = _safe_next(raw)
        assert not any(c in out for c in "'\"<>:\\\r\n\t\x00"), (raw, out)


def test_the_error_banner_renders_and_swallows_hostile_markup(monkeypatch):
    """The one templating slot in sign-in.html can never carry a reader's markup.

    The guarantee has lived only in _sign_in_page's use of html.escape and a
    comment beside {{ERROR}}.  This pins it: a refused attempt must actually
    render the banner (otherwise the rest proves nothing), the script tag the
    stranger typed must be reflected nowhere, and the banner's own text must
    be escaped rather than substituted raw.
    """
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")

    hostile = '<script>alert("xss")</script>'
    with TestClient(srv.app) as client:
        refused = client.post(srv.SIGN_IN_PATH + "?next=" + hostile,
                              follow_redirects=False,
                              data={"username": hostile, "password": hostile})

    # The banner is on the page, so the escaping path below was exercised.
    assert refused.status_code == 401
    assert 'class="err"' in refused.text
    assert "That is not the word this copy knows." in refused.text
    assert "{{ERROR}}" not in refused.text

    # Nothing the stranger typed comes back, in any form.
    assert "<script>" not in refused.text
    assert "alert(" not in refused.text
    assert "xss" not in refused.text

    # And the slot escapes what it is handed, rather than trusting the caller.
    forged = srv._sign_in_page(hostile, 401)
    body = forged.body.decode()
    assert "<script>" not in body
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in body

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
        posted = client.post(srv.SIGN_IN_PATH, follow_redirects=False,
                             data={"username": "reader", "password": "secret",
                                   "next": "/#atlas"})
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
        posted = client.post(srv.SIGN_IN_PATH, follow_redirects=False,
                             data={"username": "primer", "password": "secret",
                                   "next": hostile})

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

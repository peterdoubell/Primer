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
    assert challenge.headers["www-authenticate"].startswith("Basic ")
    assert challenge.headers["vary"] == "Authorization"
    assert wrong.status_code == 401
    assert allowed.status_code == 200
    assert allowed.headers["vary"] == "Authorization"


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

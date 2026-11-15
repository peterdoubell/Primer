"""Keep liver source payloads outside the function while gating the reader routes."""
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from primer.learner import LearnerStore
from primer.wiki import WikiService

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "web/anatomy/hva-ct-318"
PREFIX = "/app/anatomy/hva-ct-318/"


def test_every_published_file_matches_the_delivery_inventory():
    inventory = json.loads((DIRECTORY / "delivery.json").read_text())["files"]
    actual = {str(path.relative_to(DIRECTORY)) for path in DIRECTORY.rglob("*") if path.is_file()}
    assert actual == set(inventory) | {"delivery.json"}
    for name, row in inventory.items():
        raw = (DIRECTORY / name).read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["sha256"], name
        if name.endswith(".gz"):
            assert len(raw) < 4_000_000
    config = json.loads((ROOT / "vercel.json").read_text())
    pattern = "web/anatomy/hva-ct-318/*.gz"
    assert {"src": pattern, "use": "@vercel/static"} in config["builds"]
    assert pattern in config["builds"][0]["config"]["excludeFiles"]
    assert {str(p.relative_to(DIRECTORY)) for p in ROOT.glob(pattern)} == {
        name for name in inventory if name.endswith(".gz")
    }


def test_hosted_source_redirects_need_only_the_whitelisted_inventory(tmp_path, monkeypatch):
    import primer.server as server

    inventory = (DIRECTORY / "delivery.json").read_bytes()
    directory = tmp_path / "web/anatomy/hva-ct-318"
    directory.mkdir(parents=True)
    (directory / "delivery.json").write_bytes(inventory)
    monkeypatch.setattr(server, "WEB_DIR", str(tmp_path / "web"))
    monkeypatch.setattr(server, "learner", LearnerStore(str(tmp_path / "reader.db")))
    monkeypatch.setattr(server, "wiki", WikiService(str(tmp_path / "reader.db")))
    monkeypatch.setattr(server, "BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setattr(server, "_maintenance_loop", lambda *_: None)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV, "fixture-only")
    with TestClient(server.app) as client:
        for name in json.loads(inventory)["files"]:
            if not name.endswith(".gz"):
                continue
            assert client.get(PREFIX + name).status_code == 401
            for method in ("GET", "HEAD"):
                response = client.request(method, PREFIX + name, auth=("reader", "fixture-only"), follow_redirects=False)
                assert response.status_code == 307, name
                assert response.headers["location"] == "/source-media/anatomy/hva-ct-318/" + name
                assert "content-encoding" not in response.headers
        for name in ["ct-999.gz", "unlisted.mesh.gz", "private.json"]:
            assert client.get(PREFIX + name, auth=("reader", "fixture-only")).status_code == 404

"""The large native MRI chunks must use static delivery behind the reader route."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from primer.learner import LearnerStore
from primer.wiki import WikiService


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/app/anatomy/cptac-endometrial/"


def test_hosted_chunks_redirect_without_opening_excluded_files(tmp_path, monkeypatch):
    import primer.server as server

    manifest = json.loads((ROOT / "web/anatomy/cptac-endometrial/source.json").read_text())
    chunks = [chunk["file"] for sequence in manifest["sequences"].values() for chunk in sequence["chunks"]]
    directory = tmp_path / "web/anatomy/cptac-endometrial"
    directory.mkdir(parents=True)
    (directory / "source.json").write_text(json.dumps(manifest))
    # Only metadata exists in this simulated function bundle.
    monkeypatch.setattr(server, "WEB_DIR", str(tmp_path / "web"))
    monkeypatch.setattr(server, "learner", LearnerStore(str(tmp_path / "reader.db")))
    monkeypatch.setattr(server, "wiki", WikiService(str(tmp_path / "reader.db")))
    monkeypatch.setattr(server, "BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setattr(server, "_maintenance_loop", lambda *_: None)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV, "reader")
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV, "fixture-only")
    with TestClient(server.app) as client:
        for filename in chunks:
            assert client.get(PREFIX + filename).status_code == 401
            for method in ("GET", "HEAD"):
                response = client.request(method, PREFIX + filename, auth=("reader", "fixture-only"), follow_redirects=False)
                assert response.status_code == 307
                assert response.headers["location"] == "/source-media/anatomy/cptac-endometrial/" + filename
        assert client.get(PREFIX + "unknown.gz", auth=("reader", "fixture-only")).status_code == 404
        figures = json.loads((ROOT / "web/reference-studies/cervical-staging-2024/figures.json").read_text())["figures"]
        for figure in figures:
            if not figure.get("existingSourceAsset"):
                continue
            url = figure["file"]
            assert client.get(url).status_code == 401
            for method in ("GET", "HEAD"):
                response = client.request(method, url, auth=("reader", "fixture-only"), follow_redirects=False)
                assert response.status_code == 307
                assert response.headers["location"] == url.replace("/app/", "/source-media/", 1)
        assert client.get("/app/reference-media/radiology-open/cervical-cancer/unknown.png",
                          auth=("reader", "fixture-only")).status_code == 404


def test_mri_chunks_are_static_builds_and_excluded_from_function():
    config = json.loads((ROOT / "vercel.json").read_text())
    pattern = "web/anatomy/cptac-endometrial/*.gz"
    assert {"src": pattern, "use": "@vercel/static"} in config["builds"]
    assert pattern in config["builds"][0]["config"]["excludeFiles"].removeprefix("{").removesuffix("}").split(",")
    assert len(list(ROOT.glob(pattern))) == 18

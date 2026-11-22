"""Regression checks for the tracked US study, descriptor report and source delivery."""
import gzip
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from primer.segthy_reference import NECK, THYROID
from primer.server import app

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "web/anatomy/segthy-001"
MANIFEST = "d054557d2c5e6230c49659c23812a4f91d2d044ffc43d4f4b31aca88b0f5e440"


def test_sweeps_keep_distinct_grids_and_all_source_labels():
    raw = (DIRECTORY / "manifest.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MANIFEST
    left, right = json.loads(raw)["cases"]
    assert (left["shape"], right["shape"]) == ([486, 453, 370], [496, 404, 396])
    assert left["affine"] != right["affine"]
    assert [label["code"] for label in left["labels"]] == [1, 2, 3]
    assert [label["code"] for label in right["labels"]] == [1, 4, 5]
    for case in (left, right):
        for label in case["labels"]:
            xyz = label["focus"]
            brick = next(b for b in case["bricks"] if all(
                start <= x < start + size for start, size, x in zip(b["start"], b["size"], xyz)))
            i, j, k = [x - start for x, start in zip(xyz, brick["start"])]
            nx, ny, nz = brick["size"]
            raw = gzip.decompress((DIRECTORY / brick["file"]).read_bytes())
            assert len(raw) == 2 * nx * ny * nz
            assert raw[2 * (i + nx * (j + ny * k)) + 1] == label["code"]
            assert label["mesh"]["triangles"] > 80000


def test_source_inspection_is_reachable_from_both_reports_and_the_thyroid_lesson():
    with TestClient(app) as client:
        for identifier in (THYROID, NECK):
            response = client.get("/api/radiology/modules/" + identifier)
            assert response.status_code == 200, identifier
            ref = response.json()["radiology_reference"]
            study = next(r for r in ref["source_native_inspectors"] if r["id"] == "segthy-001")
            assert study["src"] == "/app/anatomy/segthy-001/index.html"
            assert study["clinical_approval"] is False
            assert "segthy" not in ref["quick_report"]["dictation"]["text"].lower()
            if identifier == NECK:
                assert ref["descriptor_only"] is True
        from primer.curriculum import Curriculum
        node = Curriculum().nodes["rad.5.thyroid-tirads"]
        assert any(THYROID in media.get("investigation_ids", []) and media["kind"] == "source-native-inspectors"
                   for media in node["lesson_media"])


def test_published_file_list_and_source_transport(monkeypatch):
    # Keep the ordinary static request local, then exercise the hosted 307 explicitly.
    monkeypatch.delenv("VERCEL", raising=False)
    auth = ("segthy-fixture", "fixture-only")
    monkeypatch.setenv("PRIMER_ACCESS_USERNAME", auth[0])
    monkeypatch.setenv("PRIMER_ACCESS_PASSWORD", auth[1])
    files = json.loads((DIRECTORY / "delivery.json").read_bytes())["files"]
    assert set(files) == {p.name for p in DIRECTORY.iterdir() if p.is_file() and p.name != "delivery.json"}
    for name, record in files.items():
        raw = (DIRECTORY / name).read_bytes()
        assert (len(raw), hashlib.sha256(raw).hexdigest()) == (record["bytes"], record["sha256"])
    prefix = "/app/anatomy/segthy-001/"
    with TestClient(app) as client:
        asset = "left-1-mesh.gz"
        assert client.get(prefix + asset).status_code == 401
        result = client.get(prefix + asset, auth=auth, headers={"range": "bytes=0-9"})
        assert result.status_code == 206 and result.content[:2] == bytes.fromhex("1f8b")
        assert client.get(prefix + "unknown.gz", auth=auth).status_code == 404
        monkeypatch.setenv("VERCEL", "1")
        response = client.head(prefix + asset, auth=auth, follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/source-media/anatomy/segthy-001/" + asset

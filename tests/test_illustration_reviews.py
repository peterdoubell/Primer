"""Review approval must not survive changed images, descriptions or lesson aims."""
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def reviewer(monkeypatch):
    tools = Path(__file__).resolve().parents[1] / "tools"
    monkeypatch.syspath_prepend(str(tools))
    spec = importlib.util.spec_from_file_location("illustration_reviews", tools / "check_illustration_reviews.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def example(tmp_path):
    directory = tmp_path / "data/curriculum"
    directory.mkdir(parents=True)
    assets = tmp_path / "web/illustrations"
    assets.mkdir(parents=True)
    for width in (800, 1600):
        (assets / (str(width) + ".webp")).write_bytes(b"synthetic-image-fixture")
    node = {"id": "test.0.a", "title": "Test", "goal": "Explain a relationship", "stage": 0,
            "lesson_media": [{"id": "test-primary", "kind": "illustration", "src": "/app/illustrations/800.webp",
                              "srcset": "/app/illustrations/800.webp 800w, /app/illustrations/1600.webp 1600w"}]}
    (directory / "01-test.json").write_text(json.dumps({"id": "test", "nodes": [node]}))
    return tmp_path


def approval(report):
    return [{"lesson": "test.0.a", "fingerprint": report["rows"][0]["fingerprint"],
             "evidence": "Both render sizes inspected", "finding": "Labels and relationships verified"}]


def test_missing_review_is_pending(reviewer, example):
    assert reviewer.audit(example, [])["reviewed"] == 0


@pytest.mark.parametrize("change", ["image", "caption", "goal"])
def test_changes_invalidate_review(reviewer, example, change):
    records = approval(reviewer.audit(example, []))
    assert reviewer.audit(example, records)["reviewed"] == 1
    if change == "image":
        (example / "web/illustrations/800.webp").write_bytes(b"changed")
    else:
        path = example / "data/curriculum/01-test.json"
        data = json.loads(path.read_text())
        node = data["nodes"][0]
        (node["lesson_media"][0] if change == "caption" else node)[change] = "Changed"
        path.write_text(json.dumps(data))
    assert reviewer.audit(example, records)["stale"] == 1


def test_invalid_records_fail(reviewer, example):
    records = approval(reviewer.audit(example, []))
    with pytest.raises(ValueError, match="Duplicate review"):
        reviewer.audit(example, records * 2)
    records[0]["lesson"] = "unknown"
    with pytest.raises(ValueError, match="unknown lesson"):
        reviewer.audit(example, records)


def test_actual_inventory_is_exhaustive(reviewer):
    assert reviewer.audit()["lessons"] == 440


def test_companion_requires_its_own_review(reviewer, example):
    source = example / 'data/curriculum/01-test.json'
    data = json.loads(source.read_text())
    first = reviewer.audit(example, [])
    companion = dict(data['nodes'][0]['lesson_media'][0], id='test-companion')
    data['nodes'][0]['lesson_media'].append(companion)
    source.write_text(json.dumps(data))
    report = reviewer.audit(example, approval(first))
    assert report['lessons'] == 1 and report['plates'] == 2
    assert [r['status'] for r in report['rows']] == ['reviewed', 'pending']
    records = approval(first) + [dict(lesson='test.0.a', media_id='test-companion',
        fingerprint=report['rows'][1]['fingerprint'], evidence='Inspected', finding='Companion checked')]
    assert reviewer.audit(example, records)['reviewed'] == 2
    data['nodes'][0]['lesson_media'][1]['alt'] = 'Changed explanation'
    source.write_text(json.dumps(data))
    assert [r['status'] for r in reviewer.audit(example, records)['rows']] == ['reviewed', 'stale']

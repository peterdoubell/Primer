"""Coverage must not pass vacuously or double-count duplicated curriculum data."""
import importlib.util
import json
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "model_coverage_gate", Path(__file__).resolve().parents[1] / "tools/check_model_coverage.py"
)
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


def write_domain(directory, filename, domain, nodes):
    (directory / filename).write_text(json.dumps({"id": domain, "nodes": nodes}), encoding="utf-8")


def lesson(identifier, models=0):
    return {"id": identifier, "title": identifier, "stage": 0,
            "lesson_media": [{"kind": "model"} for _ in range(models)]}


def test_no_files_is_not_complete_coverage(tmp_path):
    with pytest.raises(ValueError, match="No curriculum files"):
        coverage.inventory(tmp_path)


def test_empty_domain_is_not_complete_coverage(tmp_path):
    write_domain(tmp_path, "01-empty.json", "empty", [])
    with pytest.raises(ValueError, match="Empty curriculum domain"):
        coverage.inventory(tmp_path)


def test_duplicate_domain_is_rejected(tmp_path):
    write_domain(tmp_path, "01-first.json", "same", [lesson("a")])
    write_domain(tmp_path, "02-second.json", "same", [lesson("b")])
    with pytest.raises(ValueError, match="Duplicate curriculum domain"):
        coverage.inventory(tmp_path)


@pytest.mark.parametrize("cross_domain", [False, True])
def test_duplicate_lesson_is_rejected(tmp_path, cross_domain):
    write_domain(tmp_path, "01-first.json", "first", [lesson("a")] if cross_domain else [lesson("a"), lesson("a")])
    if cross_domain:
        write_domain(tmp_path, "02-second.json", "second", [lesson("a")])
    with pytest.raises(ValueError, match="Duplicate curriculum lesson"):
        coverage.inventory(tmp_path)


def test_multiple_models_do_not_inflate_covered_lessons(tmp_path):
    write_domain(tmp_path, "01-first.json", "first", [lesson("a", 2), lesson("b")])
    report = coverage.inventory(tmp_path)
    assert (report["lessons"], report["covered"], report["model_entries"]) == (2, 1, 2)
    assert report["domains"][0]["missing"] == [{"id": "b", "title": "b", "stage": 0}]


def test_actual_curriculum_has_nonvacuous_inventory():
    report = coverage.inventory()
    assert report["lessons"] == 558
    assert 0 < report["covered"] <= report["lessons"]
    assert report["model_entries"] >= report["covered"]

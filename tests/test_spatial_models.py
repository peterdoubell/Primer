"""Scientific geometry and curriculum binding checks for the local 3D models."""
import shutil
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import SPATIAL_MODEL_SCENARIOS, _validate_lesson_media


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_spatial_model_geometry_and_curriculum_bindings():
    result = subprocess.run(
        ["node", str(ROOT / "tools" / "check_spatial_models.js")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Verified 17 spatial models" in result.stdout
    assert {
        line.removeprefix("COVER ") for line in result.stdout.splitlines()
        if line.startswith("COVER ")
    } == set(SPATIAL_MODEL_SCENARIOS)


def spatial_node(node_id, props):
    return {
        "id": node_id,
        "lesson_media": [{
            "id": "spatial-geometry",
            "kind": "model",
            "renderer": "spatial-3d",
            "title": "Explore the geometry",
            "instructions": "Change a parameter, then rotate the view.",
            "props": props,
        }],
    }


@pytest.mark.parametrize("node_id", sorted(SPATIAL_MODEL_SCENARIOS))
def test_spatial_scenario_is_valid_only_on_its_own_lesson(node_id):
    _validate_lesson_media(spatial_node(node_id, {"scenario": node_id}))
    other_id = next(value for value in sorted(SPATIAL_MODEL_SCENARIOS) if value != node_id)
    with pytest.raises(ValueError, match="cross-lesson"):
        _validate_lesson_media(spatial_node(other_id, {"scenario": node_id}))


@pytest.mark.parametrize("props", [
    {}, {"scenario": "unknown"}, {"scenario": "constructor"},
    {"scenario": "__proto__"}, {"scenario": None}, {"scenario": True},
    {"scenario": []}, {"scenario": {}}, {"scenario": 1},
    {"scenario": "math.2.geometry", "url": "https://example.com/model.js"},
    {"scenario": "math.2.geometry", "camera": {"zoom": 500}},
    [], None,
])
def test_spatial_model_rejects_unknown_and_malformed_props(props):
    with pytest.raises(ValueError):
        _validate_lesson_media(spatial_node("math.2.geometry", props))

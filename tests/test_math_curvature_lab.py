"""Independent surface geometry, signed quadrature and transport checks."""
import copy
import shutil
import subprocess
from pathlib import Path

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_curvature_binding_rejects_extra_props_and_cross_lesson():
    authored = Curriculum().node("math.5.diffgeo")
    model = next(m for m in authored["lesson_media"] if m.get("renderer") == "math-curvature-lab")
    assert model["props"] == {"scenario": "math.5.diffgeo.curvature-transport"}
    _validate_lesson_media(authored)
    for props in ({"scenario": "math.5.diffgeo.curvature-transport", "extra": True},
                  {"scenario": "math.5.diffgeo"},
                  {"scenario": "math.5.functional.operators-truncation"}):
        changed = copy.deepcopy(authored)
        next(m for m in changed["lesson_media"] if m.get("renderer") == "math-curvature-lab")["props"] = props
        with pytest.raises(ValueError, match="math-curvature-lab"):
            _validate_lesson_media(changed)
    relocated = {"id": "math.5.functional", "lesson_media": [copy.deepcopy(model)]}
    with pytest.raises(ValueError, match="math-curvature-lab"):
        _validate_lesson_media(relocated)


def test_curvature_dependency_precedes_registry():
    shell = (ROOT / "web/index.html").read_text()
    assert shell.index("/app/math-curvature-lab.js") < shell.index("/app/lesson-models.js")
    assert "/app/math-curvature-lab.css" in shell


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_curvature_geometry_transport_and_mounted_controls():
    result = subprocess.run(
        ["node", str(ROOT / "tools" / "check_math_curvature_lab.js")],
        cwd=ROOT, capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1200 independently differentiated surface states" in result.stdout
    assert "103 quadrature patches" in result.stdout
    assert "4320 geometric transport states" in result.stdout
    assert "27 mounted controls" in result.stdout

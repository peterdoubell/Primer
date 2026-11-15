"""Whole-node complex-analysis binding and focused independent oracles."""
import copy
import shutil
import subprocess
from pathlib import Path

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "math.5.complex-analysis.holomorphy-contours"


def test_complex_lab_binding_is_exact_and_lesson_scoped():
    authored = Curriculum().node("math.5.complex-analysis")
    model = next(m for m in authored["lesson_media"] if m.get("renderer") == "math-complex-lab")
    assert model["props"] == {"scenario": SCENARIO}
    _validate_lesson_media(authored)
    for props in ({"scenario": SCENARIO, "extra": True},
                  {"scenario": "math.5.complex-analysis"},
                  {"scenario": "math.5.diffgeo.curvature-transport"}):
        changed = copy.deepcopy(authored)
        next(m for m in changed["lesson_media"] if m.get("renderer") == "math-complex-lab")["props"] = props
        with pytest.raises(ValueError, match="math-complex-lab"):
            _validate_lesson_media(changed)
    with pytest.raises(ValueError, match="math-complex-lab"):
        _validate_lesson_media({"id": "math.5.diffgeo", "lesson_media": [copy.deepcopy(model)]})


def test_complex_lab_dependency_and_scoped_hidden_styles():
    shell = (ROOT / "web/index.html").read_text()
    assert shell.index("/app/math-complex-lab.js") < shell.index("/app/lesson-models.js")
    assert "/app/math-complex-lab.css" in shell
    styles = (ROOT / "web/math-complex-lab.css").read_text()
    assert ".math-complex-lab [hidden] { display: none !important; }" in styles
    assert "min-height: 44px" in styles


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_complex_lab_independent_equations_and_mounted_controls():
    result = subprocess.run(
        ["node", str(ROOT / "tools/check_math_complex_lab.js")],
        cwd=ROOT, capture_output=True, text=True, timeout=90, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for evidence in (
        "420 independent derivative/CR/Cauchy states", "410 contour quadrature/winding states",
        "108 Taylor/coefficient states", "96 mean/max states", "180 Jordan arc states",
        "768 polynomial exterior inequalities", "76 mounted controls", "all six stations",
        "path-pole omissions", "blur", "exact resets",
    ):
        assert evidence in result.stdout

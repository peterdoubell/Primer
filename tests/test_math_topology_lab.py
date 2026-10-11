"""Whole-node topology binding and independent finite/infinite witnesses."""
import copy
import shutil
import subprocess
from pathlib import Path

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "math.5.topology.opens-covers-surfaces"


def test_topology_lab_binding_is_exact_and_lesson_scoped():
    authored = Curriculum().node("math.5.topology")
    model = next(m for m in authored["lesson_media"] if m.get("renderer") == "math-topology-lab")
    assert model["props"] == {"scenario": SCENARIO}
    _validate_lesson_media(authored)
    for props in ({"scenario": SCENARIO, "extra": True},
                  {"scenario": "math.5.topology"},
                  {"scenario": "math.5.complex-analysis.holomorphy-contours"}):
        changed = copy.deepcopy(authored)
        next(m for m in changed["lesson_media"] if m.get("renderer") == "math-topology-lab")["props"] = props
        with pytest.raises(ValueError, match="math-topology-lab"):
            _validate_lesson_media(changed)
    with pytest.raises(ValueError, match="math-topology-lab"):
        _validate_lesson_media({"id": "math.5.complex-analysis", "lesson_media": [copy.deepcopy(model)]})


def test_topology_lab_dependency_and_scoped_hidden_styles():
    shell = (ROOT / "web/index.html").read_text()
    assert shell.index("/app/math-topology-lab.js") < shell.index("/app/lesson-models.js")
    assert shell.index("/app/lesson-state.js") < shell.index("/app/math-topology-lab.js")
    assert "/app/math-topology-lab.css" in shell
    styles = (ROOT / "web/math-topology-lab.css").read_text()
    assert ".math-topology-lab [hidden] { display: none !important; }" in styles
    assert "min-height: 44px" in styles


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_topology_independent_science_and_mounted_controls():
    result = subprocess.run(
        ["node", str(ROOT / "tools/check_math_topology_lab.js")],
        cwd=ROOT, capture_output=True, text=True, timeout=90, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for evidence in (
        "256 exhaustive open-family states (29 topologies)",
        "432 independent preimage maps", "237 cover/witness states",
        "144 infinite cofinite illustrations", "45 sine-closure states",
        "8 closed oriented manifold meshes with every vertex link and Euler characteristic",
        "72 exact affine deformation/inverse states", "27 circle/theorem states",
        "50 mounted controls across all seven stations", "no oscillation bridge",
        "Draft/blur/Enter/Escape", "exact resets", "complete-state bus propagation",
    ):
        assert evidence in result.stdout

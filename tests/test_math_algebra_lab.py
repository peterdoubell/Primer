"""Exact finite algebra, universal hypotheses, and authored lesson isolation."""
import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "math.5.abstract.groups-rings-fields"


def test_algebra_lab_is_bound_only_to_the_authored_abstract_algebra_node():
    authored = Curriculum().node("math.5.abstract")
    model = next(m for m in authored["lesson_media"] if m.get("renderer") == "math-algebra-lab")
    assert model["props"] == {"scenario": SCENARIO}
    _validate_lesson_media(authored)
    for props in ({"scenario": SCENARIO, "extra": True}, {"scenario": "math.5.abstract"},
                  {"scenario": "math.5.topology.opens-covers-surfaces"}):
        changed = copy.deepcopy(authored)
        next(m for m in changed["lesson_media"] if m.get("renderer") == "math-algebra-lab")["props"] = props
        with pytest.raises(ValueError, match="math-algebra-lab"):
            _validate_lesson_media(changed)
    with pytest.raises(ValueError, match="math-algebra-lab"):
        _validate_lesson_media({"id": "math.5.topology", "lesson_media": [copy.deepcopy(model)]})


def test_algebra_dependency_order_and_touch_sized_scoped_controls():
    shell = (ROOT / "web/index.html").read_text()
    assert shell.index("/app/lesson-state.js") < shell.index("/app/math-algebra-lab.js") < shell.index("/app/lesson-models.js")
    assert "/app/math-algebra-lab.css" in shell
    styles = (ROOT / "web/math-algebra-lab.css").read_text()
    assert ".math-algebra-lab [hidden] { display: none !important; }" in styles
    assert "min-height: 44px" in styles


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js required")
def test_independent_exhaustive_algebra_and_actual_rendered_values():
    result = subprocess.run(["node", str(ROOT / "tools/check_math_algebra_lab.js")],
                            cwd=ROOT, capture_output=True, text=True, timeout=90, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    for evidence in ("19683 exhaustive three-element operation tables (3 groups)",
                     "209 cyclic element/subgroup/coset states", "576 independent S4 compositions",
                     "312 powers", "six four-cycles", "189 modular ring/kernel states",
                     "481 integer-map examples with separate universal proofs", "all 225 CRT products",
                     "6 normal/nonnormal quotient states", "51 matrix field-map/ideal states",
                     "94 mounted states", "3597 exact rendered table cells",
                     "Draft/blur/Enter/Escape", "complete-state bus propagation"):
        assert evidence in result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js required")
def test_large_integer_and_noncommutative_target_claims_have_correct_hypotheses():
    # The runtime's displayed windows are deliberately finite; verify decisive
    # algebraic counterexamples separately with Python integers/matrices.
    source = "const l=require('./web/math-algebra-lab.js');console.log(JSON.stringify({integer:l.integerModel({multiplier:3,targetInteger:12}),field:l.fieldModel({fieldPrime:'5',fieldMap:'scalar'}),sylow:l.sylowModel({})}));"
    output = subprocess.run(["node", "-e", source], cwd=ROOT, capture_output=True, text=True, check=True)
    data = json.loads(output.stdout)
    assert data["integer"]["inverseValue"] == 4
    assert not data["integer"]["onto"]
    assert 3 * 10**30 + 3 * (-10**30 + 1) == 3
    assert 1 % 3 != 0
    # C2×C2×C3 is a counterexample to the false blanket claim that normal
    # coprime-order factors imply a cyclic product (orders 4 and 3).
    elements = [(a, b, c) for a in range(2) for b in range(2) for c in range(3)]
    assert len(elements) == 12
    assert all((6*a % 2, 6*b % 2, 6*c % 3) == (0, 0, 0) for a, b, c in elements)
    assert "Groups of prime order are cyclic" in data["sylow"]["steps"][-1]
    # A noncommutative target is permitted: E12E21 != E21E12 modulo five.
    def multiply(a, b):
        return [[sum(a[i][k] * b[k][j] for k in range(2)) % 5 for j in range(2)] for i in range(2)]
    e12, e21 = [[0, 1], [0, 0]], [[0, 0], [1, 0]]
    assert multiply(e12, e21) != multiply(e21, e12)
    assert data["field"]["targetNonzero"] and data["field"]["unital"] and data["field"]["injective"]
    assert data["field"]["kernel"] == [0]

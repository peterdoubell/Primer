"""Independent finite-set oracles; the tests do not certify infinite metatheorems."""
import copy
import itertools
import json
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def node(source):
    result = subprocess.run(["node", "-e", source], cwd=ROOT, check=True, text=True, capture_output=True, timeout=30)
    return json.loads(result.stdout)


def test_all_three_element_maps_have_independent_diagonal_witnesses():
    actual = node("const a=require('./web/math-logic-lab.js');console.log(JSON.stringify(Array.from({length:512},(_,code)=>{const rows=[code%8,Math.floor(code/8)%8,Math.floor(code/64)%8];return {rows,...a.diagonal(rows,3)};})));")
    for row in actual:
        subsets = [{j for j in range(3) if code & (1 << j)} for code in row["rows"]]
        missing = {j for j in range(3) if j not in subsets[j]}
        assert missing not in subsets
        assert row["missing"] == sum(1 << j for j in missing)
        assert row["subsetCount"] == 8
        assert len(row["comparisons"]) == 3


def test_all_three_element_relation_properties_and_complete_counterexamples():
    actual = node("const a=require('./web/math-logic-lab.js');console.log(JSON.stringify(Array.from({length:512},(_,mask)=>a.relation(3,mask))));")
    counts = dict.fromkeys(["reflexive", "symmetric", "antisymmetric", "transitive"], 0)
    names = range(3)
    for row in actual:
        pairs = {tuple(pair) for pair in row["pairs"]}
        expected_failures = {
            "reflexive": {(x,) for x in names if (x, x) not in pairs},
            "symmetric": {(x, y) for x, y in itertools.product(names, repeat=2) if (x, y) in pairs and (y, x) not in pairs},
            "antisymmetric": {(x, y) for x, y in itertools.product(names, repeat=2) if x != y and (x, y) in pairs and (y, x) in pairs},
            "transitive": {(x, y, z) for x, y, z in itertools.product(names, repeat=3) if (x, y) in pairs and (y, z) in pairs and (x, z) not in pairs},
        }
        for kind, failures in expected_failures.items():
            assert {tuple(v) for v in row["failures"][kind]} == failures
            assert row["properties"][kind] is (not failures)
            counts[kind] += not failures
        assert row["pairSlots"] == 9 and row["relationCount"] == 512
    assert counts == {"reflexive": 64, "symmetric": 64, "antisymmetric": 216, "transitive": 171}


def test_decimal_uniqueness_rule_and_all_finite_compactness_demands():
    data = node("const a=require('./web/math-logic-lab.js');console.log(JSON.stringify({decimal:a.decimalDiagonal(['00000000','11111111','99999999','22222222','33333333','44444444','55555555','66666666']),finite:Array.from({length:21},(_,bound)=>Array.from({length:23},(_,witness)=>a.build({station:'compactness',bound,witness}).data)).flat()}));")
    assert data["decimal"]["digits"] == ["1", "2", "1", "1", "1", "1", "1", "1"]
    assert all(c["listed"] != c["constructed"] for c in data["decimal"]["comparisons"])
    for i, row in enumerate(data["finite"]):
        bound, witness = divmod(i, 23)
        assert row["allSatisfied"] is (witness > bound)
        assert row["canonicalWitness"] == bound + 1
        assert [c["holds"] for c in row["constraints"]] == [witness > n for n in range(bound + 1)]


def test_logic_lesson_binding_is_exact_and_cross_lesson_closed():
    lesson = copy.deepcopy(Curriculum().node("math.5.logic"))
    item = next(m for m in lesson["lesson_media"] if m.get("renderer") == "math-logic-lab")
    assert item["props"] == {"scenario": "math.5.logic.diagonal-models-proof"}
    _validate_lesson_media(lesson)
    item["props"]["scenario"] = "math.5.abstract.groups-rings-fields"
    with pytest.raises(ValueError, match="math-logic-lab"):
        _validate_lesson_media(lesson)


def test_full_finite_and_mounted_checker():
    result = subprocess.run(["node", "tools/check_math_logic_lab.js"], cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "66066 complete finite diagonal maps" in result.stdout
    assert "66066 complete relation encodings" in result.stdout

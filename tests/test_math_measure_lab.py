"""Independent rational membership and boundary-aware integration oracles."""
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")


def node(script, cases):
    result = subprocess.run(["node", "-e", script, json.dumps(cases)], cwd=ROOT,
                            capture_output=True, text=True, timeout=30, check=True)
    return json.loads(result.stdout)


def test_measure_math_and_actual_mounted_controls():
    result = subprocess.run(["node", "tools/check_math_measure_lab.js"], cwd=ROOT,
                            capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "150 boundary-split integration states" in result.stdout
    assert "309 exact rational probe states and 28 mounted control states passed" in result.stdout


def test_exact_rational_probes_and_selected_family_envelopes():
    cases = [dict(n=n, amplitude=a, alpha=alpha, numerator=num, denominator=den)
             for n in (1, 3, 4, 1024, 65536) for a in (0, .25, 2)
             for alpha in ("0", "0.5", "1")
             for num, den in ((0, 1), (1, 1), (1, 4), (1, 65536), (3, 17))]
    actual = node("const l=require('./web/math-measure-lab.js');console.log(JSON.stringify(JSON.parse(process.argv[1]).map(s=>l.build(s))));", cases)
    for case, model in zip(cases, actual, strict=True):
        n, amplitude, alpha = case["n"], Fraction(case["amplitude"]), float(case["alpha"])
        x = Fraction(case["numerator"], case["denominator"])
        inside = 0 < x < Fraction(1, n)
        assert model["probe"]["inside"] is inside
        height = float(amplitude) * n ** alpha
        assert math.isclose(model["probe"]["value"], height if inside else 0, rel_tol=2e-14, abs_tol=1e-14)
        threshold = 1 if x == 0 else math.ceil(1 / x)
        assert model["probe"]["zeroFrom"] == threshold
        last = 0 if x == 0 else threshold - 1
        expected_envelope = 0 if last == 0 else float(amplitude) * last ** alpha
        assert math.isclose(model["probe"]["envelope"], expected_envelope, rel_tol=2e-14, abs_tol=1e-14)
        # 2α−1 is an integer for every exposed family: this oracle is exact rational arithmetic.
        squared_l2 = amplitude ** 2 * Fraction(n) ** int(2 * alpha - 1)
        assert math.isclose(model["norm2Squared"], float(squared_l2), rel_tol=2e-14, abs_tol=1e-14)
        if case["alpha"] in ("0", "1"):
            exact_l1 = amplitude * Fraction(n) ** int(alpha - 1)
            assert math.isclose(model["integral"], float(exact_l1), rel_tol=2e-14, abs_tol=1e-14)


def test_independent_scipy_quadrature_splits_at_support_boundary():
    integrate = pytest.importorskip("scipy.integrate")
    cases = [dict(n=n, amplitude=a, alpha=alpha)
             for n in (1, 2, 3, 4, 7, 16, 255, 1023, 1024, 65536)
             for a in (0, .25, 2, 7.75) for alpha in ("0", "0.5", "1")]
    actual = node("const l=require('./web/math-measure-lab.js');console.log(JSON.stringify(JSON.parse(process.argv[1]).map(s=>l.build(s))));", cases)
    for case, model in zip(cases, actual, strict=True):
        n, a, alpha = case["n"], case["amplitude"], float(case["alpha"])
        boundary = 1 / n
        def value(x):
            return a * n ** alpha if 0 < x < boundary else 0
        for power, key in ((1, "integral"), (2, "norm2Squared")):
            first, _ = integrate.quad(lambda x: value(x) ** power, 0, boundary, epsabs=1e-11, epsrel=1e-12)
            rest, _ = integrate.quad(lambda x: value(x) ** power, boundary, 1, epsabs=1e-11, epsrel=1e-12)
            assert math.isclose(model[key], first + rest, rel_tol=2e-12, abs_tol=1e-11)


def test_zero_amplitude_and_convergence_distinctions_are_explicit():
    cases = [dict(alpha=alpha, amplitude=a, n=65536) for alpha in ("0", "0.5", "1") for a in (0, 2)]
    rows = node("const l=require('./web/math-measure-lab.js');console.log(JSON.stringify(JSON.parse(process.argv[1]).map(s=>l.build(s))));", cases)
    for case, row in zip(cases, rows, strict=True):
        assert row["convergence"]["pointwise"] and row["convergence"]["almostEverywhere"]
        if case["amplitude"] == 0:
            assert all(row["convergence"].values())
            assert row["nonzeroMeasure"] == 0 and row["intervalMeasure"] > 0
            assert row["probe"]["dominator"] == row["dominatorIntegral"] == 0
        elif case["alpha"] == "0.5":
            assert row["convergence"]["dominated"] and row["convergence"]["l1"]
            assert not row["convergence"]["l2"] and not row["convergence"]["uniform"]
            assert row["norm2"] == 2 and row["dominatorIntegral"] == 4
        elif case["alpha"] == "1":
            assert not row["convergence"]["dominated"] and row["integral"] == 2
            assert "ceil(1/x) − 1" in row["proof"] and "A/(2x)" in row["proof"]
        assert "not a conclusion proved by the finite plot" in row["pointwise"]

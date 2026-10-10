"""Independent world-geometry, product measure and quasistatic work oracles."""
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")


def run(*args):
    result = subprocess.run(["node", "tools/check_integration_cycle_spatial.js", *args], cwd=ROOT,
                            capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


@pytest.fixture(scope="module")
def frames():
    return json.loads(run("--json"))


def test_fixed_loader_and_actual_native_controls():
    result = run()
    assert "independent Carnot path points" in result and "native mounted controls passed" in result
    source = (ROOT / "tools/check_integration_cycle_spatial.js").read_text()
    assert "require('../web/spatial-models.js')" in source
    assert "require('../web/spatial-module-objects.js')" in source
    assert "vm." not in source and "eval(" not in source and "new Function" not in source


def test_product_measure_is_independent_of_squared_l2(frames):
    for row in frames["measure"]:
        s = row["state"]
        n, A, alpha = 2 ** s["indexPower"], Fraction(s["amplitude"]), Fraction(s["alpha"])
        width = Fraction(1, n)
        if A == 0:
            assert not row["faces"]
        else:
            points = [p for f in row["faces"] for p in f["points"]]
            low = [min(p[i] for p in points) for i in range(3)]
            high = [max(p[i] for p in points) for i in range(3)]
            assert low == [0, 0, 0] and high[2] == 1
            assert Fraction(high[0]) == width  # Powers of two have exact binary widths.
            squared_height = A ** 2 * Fraction(n) ** int(2 * alpha)
            assert math.isclose(high[1] ** 2, float(squared_height), rel_tol=2e-14)
            world_volume = math.prod(high[i] - low[i] for i in range(3))
            squared_volume = A ** 2 * Fraction(n) ** int(2 * alpha - 2)
            assert math.isclose(world_volume ** 2, float(squared_volume), rel_tol=2e-14)
            assert math.isclose(row["measure"]["integral"], world_volume, rel_tol=2e-14)
        squared_l2 = A ** 2 * Fraction(n) ** int(2 * alpha - 1)
        assert math.isclose(row["measure"]["norm2Squared"], float(squared_l2), rel_tol=2e-14, abs_tol=1e-15)
        a, b = row["probe"]["rational"]["a"], row["probe"]["rational"]["b"]
        x = Fraction(a, b)
        inside = 0 < x < width
        assert row["probe"]["inside"] is inside
        assert row["probe"]["points"][0][0] == float(x)
        assert row["probe"]["points"][0][1] == (float(A) * n ** float(alpha) if inside else 0)


def test_ideal_gas_paths_calibration_and_independent_work_quadrature(frames):
    integrate = pytest.importorskip("scipy.integrate")
    R, amount, gamma = 8.31446261815324, .1, 5 / 3
    for row in frames["cycle"]:
        s = row["state"]
        assert s["moles"] == amount and s["volume"] == .001 and s["leak"] == 0
        assert row["scales"] == dict(volume=.005, pressure=200000, temperature=1000)
        ratio = math.exp(s["hotHeat"] / (amount * R * s["hot"]))
        factor = (s["hot"] / s["cold"]) ** (1 / (gamma - 1))
        expected = [(.001, s["hot"]), (.001 * ratio, s["hot"]),
                    (.001 * ratio * factor, s["cold"]), (.001 * factor, s["cold"])]
        for corner, (V, T) in zip(row["corners"], expected, strict=True):
            assert math.isclose(corner["V"], V, rel_tol=2e-14)
            assert corner["T"] == T
            assert math.isclose(corner["p"], amount * R * T / V, rel_tol=2e-14)
        names = "ABCD" if s["mode"] == "engine" else "ADCB"
        for i, leg in enumerate(row["legs"]):
            assert leg["from"]["name"] == names[i]
            assert leg["to"]["name"] == names[(i + 1) % 4]
            V0, T0 = leg["from"]["V"], leg["from"]["T"]
            p0 = amount * R * T0 / V0
            if leg["kind"] == "isothermal":
                def pressure(V):
                    return amount * R * T0 / V
            else:
                def pressure(V):
                    return p0 * (V0 / V) ** gamma
            W, _ = integrate.quad(pressure, V0, leg["to"]["V"], epsabs=1e-9, epsrel=2e-12)
            assert math.isclose(leg["Wby"], W, rel_tol=3e-12, abs_tol=1e-9)
            curve = next(p for p in row["curves"] if p["leg"] == i)
            assert len(curve["points"]) == 121
            for j, (q, world) in enumerate(zip(leg["points"], curve["points"], strict=True)):
                V = V0 * math.exp(j / 120 * math.log(leg["to"]["V"] / V0))
                T = T0 if leg["kind"] == "isothermal" else T0 * (V0 / V) ** (gamma - 1)
                assert math.isclose(q["V"], V, rel_tol=3e-14)
                assert math.isclose(q["T"], T, rel_tol=3e-14)
                assert math.isclose(q["p"], pressure(V), rel_tol=3e-14)
                assert all(math.isclose(a, b, rel_tol=3e-14) for a, b in zip(world, [V / .005, pressure(V) / 200000, T / 1000], strict=True))
                assert math.isclose(q["Q"] - q["Wby"], q["deltaU"], abs_tol=1e-9)
        assert row["current"]["leg"] == int(s["leg"])
        selected = row["current"]
        assert all(math.isclose(a, b, rel_tol=3e-14) for a, b in zip(row["marker"]["points"][0],
                   [selected["V"] / .005, selected["p"] / 200000, selected["T"] / 1000], strict=True))

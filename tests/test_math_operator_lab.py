"""Independent Fraction ledgers, spectral distances and nonnormal matrix checks."""
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
    r = subprocess.run(["node", "tools/check_math_operator_lab.js", *args], cwd=ROOT,
                       capture_output=True, text=True, timeout=60, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


@pytest.fixture(scope="module")
def frames():
    return json.loads(run("--json"))


def fraction(p):
    return Fraction(int(p["numerator"]), int(p["denominator"]))


def test_actual_control_updates_and_geometry():
    assert "native mounted control states passed" in run()


def test_exact_sparse_ledgers_and_full_diagonal_spectrum(frames):
    distances = {}
    for m in frames:
        s = m["state"]
        N, k, lam = s["cutoff"], s["index"], Fraction(s["lambdaNumerator"], s["lambdaDenominator"])
        requested = {j: Fraction(v, 4) for j, v in ((k, s["first"]), (k + 1, s["second"])) if v}
        for r in m["comparisons"]:
            accepted = {j: c for j, c in requested.items() if r["kind"] != "matrix" or j <= N}
            output = {}
            for j, c in accepted.items():
                if r["kind"] != "infinite" and (j > N or (s["operator"] == "shift" and j == N)):
                    continue
                output[j + 1 if s["operator"] == "shift" else j] = c if s["operator"] == "shift" else c / j
            residual = {j: output.get(j, 0) - lam * accepted.get(j, 0) for j in output.keys() | accepted.keys()}
            residual = {j: c for j, c in residual.items() if c}
            for key, oracle in (("input", accepted), ("output", output), ("residual", residual)):
                assert {e["index"]: fraction(e) for e in r[key]["entries"]} == oracle
                assert fraction(r[key]["normSquared"]) == sum(c*c for c in oracle.values())
                assert fraction(r[key]["visibleSquared"]) == sum(c*c for j, c in oracle.items() if j <= N)
                assert fraction(r[key]["offscreenSquared"]) == sum(c*c for j, c in oracle.items() if j > N)
            assert fraction(r["excludedInputSquared"]) == sum(c*c for j, c in requested.items() if j not in accepted)
            if s["operator"] == "diagonal":
                # Enumerate an independent reciprocal sequence sufficiently past
                # every positive rational probe, rather than using the runtime's
                # floor/ceil candidate algorithm or its visible cutoff.
                cache_key = (lam, N if r["kind"] != "infinite" else None, r["kind"])
                if cache_key not in distances:
                    values = [Fraction(1, j) for j in range(1, (max(33, lam.denominator + 1) if r["kind"] == "infinite" else N) + 1)]
                    if r["kind"] != "matrix":
                        values.append(Fraction(0))
                    distances[cache_key] = min(abs(v - lam) for v in values)
                distance = distances[cache_key]
                assert fraction(r["spectrum"]["distance"]) == distance
                if distance:
                    assert fraction(r["spectrum"]["inverseNorm"]) == 1 / distance
                assert r["spectrum"]["eigenvalue"] == (distance == 0 and (lam != 0 or r["kind"] == "finite-rank"))


def test_finite_matrices_and_nonnormal_inverse_norm(frames):
    np = pytest.importorskip("numpy")
    checked = set()
    for m in frames:
        s = m["state"]
        N, lam = s["cutoff"], s["lambdaNumerator"] / s["lambdaDenominator"]
        key = (s["operator"], N, lam)
        if key in checked:
            continue
        checked.add(key)
        T = np.diag(1 / np.arange(1, N + 1)) if s["operator"] == "diagonal" else np.diag(np.ones(N - 1), -1)
        finite = m["comparisons"][1]["spectrum"]
        eigenvalues = np.linalg.eigvals(T)
        distance = min(abs(eigenvalues - lam))
        assert math.isclose(float(fraction(finite["distance"])), float(distance), rel_tol=1e-12, abs_tol=1e-15)
        if not finite["inSpectrum"]:
            inverse_norm = np.linalg.norm(np.linalg.inv(T - lam * np.eye(N)), 2)
            if s["operator"] == "diagonal":
                assert math.isclose(finite["inverseNorm"]["value"], float(inverse_norm), rel_tol=1e-12)
            else:
                assert finite["inverseNorm"] is None
                if N == 2 and math.isclose(lam, .4):
                    assert inverse_norm > 1 / distance  # It is not 2.5.

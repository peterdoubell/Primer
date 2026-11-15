"""Independent laws, seeded replay and numerical binomial oracles."""
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_probability_laws_and_mounted_controls():
    result = subprocess.run(["node", "tools/check_math_probability_lab.js"], cwd=ROOT,
                            capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "56 binomial distributions, 210 concentration states and 14 mounted controls" in result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_binomial_log_probabilities_against_independent_scipy_oracle():
    stats = pytest.importorskip("scipy.stats")
    cases = [(n, p) for n in (1, 10, 256, 1000, 6000, 8192)
             for p in (.01, 1 / 6, .5, .99)]
    script = """
      global.window={};require('./web/math-probability-lab.js');
      const api=window.PrimerMathProbabilityLab;
      const cases=JSON.parse(process.argv[1]);
      console.log(JSON.stringify(cases.map(([n,p])=>{
        const d=api.binomial(n,p);const mode=Math.min(n,Math.floor((n+1)*p));
        const indices=[0,1,Math.max(0,mode-1),mode,Math.min(n,mode+1),n-1,n];
        return {n,p,indices,logs:indices.map(k=>d.logs[k])};
      })));
    """
    result = subprocess.run(["node", "-e", script, json.dumps(cases)], cwd=ROOT,
                            capture_output=True, text=True, timeout=30, check=True)
    checked = json.loads(result.stdout)
    for case in checked:
        expected = stats.binom.logpmf(case["indices"], case["n"], case["p"])
        for actual, oracle in zip(case["logs"], expected):
            assert math.isclose(actual, float(oracle), rel_tol=2e-11, abs_tol=2e-9)


def test_pcg_attribution_and_license_are_retained():
    notice = (ROOT / "web/math-probability-lab.LICENSE.txt").read_text()
    source = (ROOT / "web/math-probability-lab.js").read_text()
    assert "Copyright 2014 Melissa O'Neill" in notice
    assert "Version 2.0, January 2004" in notice
    assert "math-probability-lab.LICENSE.txt" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_model_tail_sums_against_independent_scipy_logpmf():
    stats = pytest.importorskip("scipy.stats")
    special = pytest.importorskip("scipy.special")
    cases = [dict(n=n, percent=p, tolerance=e, experiment="bernoulli")
             for n in (10, 256, 1000, 6000, 8192)
             for p in (1, 10, 50, 99) for e in (1, 10, 50)]
    cases += [dict(n=n, tolerance=e, experiment="die")
              for n in (10, 256, 1000, 6000, 8192) for e in (1, 10, 50)]
    script = """
      global.window={};require('./web/math-probability-lab.js');
      const api=window.PrimerMathProbabilityLab;
      console.log(JSON.stringify(JSON.parse(process.argv[1]).map(s=>api.tail(s).logProbability)));
    """
    result = subprocess.run(["node", "-e", script, json.dumps(cases)], cwd=ROOT,
                            capture_output=True, text=True, timeout=30, check=True)
    for case, actual in zip(cases, json.loads(result.stdout)):
        n, e = case["n"], case["tolerance"]
        if case["experiment"] == "die":
            p = 1 / 6
            indices = [k for k in range(n + 1) if 100 * abs(6 * k - n) >= 6 * n * e]
        else:
            p = case["percent"] / 100
            indices = [k for k in range(n + 1) if abs(100 * k - n * case["percent"]) >= n * e]
        oracle = float(special.logsumexp(stats.binom.logpmf(indices, n, p)))
        assert math.isclose(actual, oracle, rel_tol=2e-10, abs_tol=2e-8)

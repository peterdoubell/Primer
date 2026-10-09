"""Second-order ODE maths and interaction regression checks."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_exact_second_order_solutions_and_mounted_controls():
    result = subprocess.run(
        ["node", str(ROOT / "tools" / "check_math_ode_lab.js")],
        cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "432 analytic states against independent RK4" in result.stdout
    assert "15 mounted control states, four regimes, equilibrium and resets passed" in result.stdout

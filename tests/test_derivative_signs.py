"""Independent rational values and sign changes verify the calculus model."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_derivative_signs_and_fixed_perimeter_optimization():
    result = subprocess.run(
        ["node", str(ROOT / "tools/check_derivative_signs.cjs")],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

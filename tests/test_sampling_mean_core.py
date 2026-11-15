"""Exact distribution checks cover all inputs and independent small-n enumeration."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_exact_sampling_distributions():
    result = subprocess.run(
        ["node", str(ROOT / "tools/check_sampling_mean_core.cjs")],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

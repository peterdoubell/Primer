"""Independent counting formulas verify replacement and conditional probabilities."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_exact_events_and_conditioning_for_every_supported_bag():
    result = subprocess.run(
        ["node", str(ROOT / "tools/check_marble_draws.cjs")],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

"""Preserve reaction bookkeeping and the explicitly included emitted particles."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_source_reaction_ledgers():
    result = subprocess.run(
        ["node", str(ROOT / "tools/check_nuclear_balance.cjs")],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

"""Exhaust the finite relation space against a separate set-based oracle."""
from pathlib import Path
import subprocess


def test_quantifier_scope_relations():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(['node', str(root / 'tools/check_quantifier_scope.cjs')],
                            cwd=root, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr

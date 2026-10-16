"""Triangle laws must agree with Cartesian distances and count SSA solutions correctly."""
from pathlib import Path
import json
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js required')
def test_triangle_geometry_and_ambiguity():
    result = subprocess.run(['node', 'tools/verify_triangle_fidelity.cjs'], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['verifiedSolutions'] == 52982

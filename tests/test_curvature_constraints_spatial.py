"""Independent parameter surfaces and Newton-frame force glyphs stay truthful."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js required')
def test_parameter_patch_boundaries_and_newtonian_force_glyphs():
    result = subprocess.run(['node', str(ROOT/'tools/check_curvature_constraints_spatial.js')],
                            cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout+result.stderr
    assert '384 independently parameterized surface states' in result.stdout
    assert '1701 Newtonian hoop states' in result.stdout
    assert 'laboratory/virtual-work distinctions passed' in result.stdout

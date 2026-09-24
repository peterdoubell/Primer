"""Whole-curriculum 3D companions retain exact bindings and numeric geometry."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_module_model_geometry_bindings_controls_and_invariants():
    result = subprocess.run(
        ['node', str(ROOT / 'tools/check_module_models.js')],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '454 lesson bindings, 41 object families' in result.stdout
    assert 'quantitative geometry invariants passed' in result.stdout

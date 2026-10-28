"""Whole-curriculum 3D companions retain exact bindings and numeric geometry."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_plane_shapes_preserve_intrinsic_geometry():
    result = subprocess.run(
        ['node', str(ROOT / 'tools/check_plane_shapes.cjs')], cwd=ROOT,
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"states":1100,"allPassed":true' in result.stdout


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_module_model_geometry_bindings_controls_and_invariants():
    result = subprocess.run(
        ['node', str(ROOT / 'tools/check_module_models.js')],
        cwd=ROOT,
        capture_output=True,
        text=True,
        # The checker verifies the whole curriculum, including costly
        # quantum-well quadrature. Shared CI runners have exceeded 60 seconds;
        # retain every assertion and a bounded limit with execution headroom.
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '462 lesson bindings, 76 object families' in result.stdout
    assert 'quantitative geometry invariants passed' in result.stdout

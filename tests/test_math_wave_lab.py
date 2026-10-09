"""Continuum waves must follow their equations, initial data and boundaries."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_wave_field_equations_independent_evolution_and_mounted_geometry():
    r = subprocess.run(['node', 'tools/check_math_wave_lab.js'], cwd=ROOT, capture_output=True,
                       text=True, check=False, timeout=45)
    assert r.returncode == 0, r.stdout + r.stderr
    assert '11 independent wave/heat PDE evolutions and 21 mounted controls' in r.stdout

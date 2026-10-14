"""Signed sequences, series limits, decay and inverse graphs must match their values."""
from pathlib import Path
import json
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_growth_series_rational_oracles_and_mounted_coordinates():
    result = subprocess.run(['node', 'tools/check_math_growth_series_fidelity.js'], cwd=ROOT,
                            capture_output=True, text=True, check=False, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads(result.stdout)
    assert proof['sequenceStates'] == 14256
    assert proof['exponentialStates'] == 500
    assert proof['geometryStates'] == 264
    assert proof['curveSegments'] > 10000
    assert proof['maxCurveErrorPixels'] < .025

"""Exercise the calculations, independent equations and numerical regressions."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/fluids-fidelity-review-20261016'
pytestmark = pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')


def identities():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in REVIEW.rglob('*') if path.is_file()}


def checked_run(command):
    before = identities()
    environment = os.environ.copy()
    environment.pop('FLUIDS_WRITE_PROOF', None)
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True,
                            check=True, timeout=120)
    assert identities() == before, 'Default numerical verification must not rewrite review evidence'
    receipt = json.loads(result.stdout)
    assert receipt['allPassed'] is True
    assert receipt['sourceSHA256'] == hashlib.sha256((ROOT / 'web/fluids-lab.js').read_bytes()).hexdigest()
    return receipt


def test_core_force_energy_flux_and_ode_checks():
    proof = checked_run(['node', 'tools/check_fluids_core.cjs'])
    assert set(proof['counts']) >= {'continuity', 'hydrostatic', 'pistons', 'hulls', 'pipes',
                                    'settling', 'airfoils', 'plumes', 'rejectedInputs'}
    assert all(proof['counts'][name] > 0 for name in ['continuity', 'hydrostatic', 'pistons',
               'hulls', 'pipes', 'settling', 'airfoils', 'plumes', 'rejectedInputs'])
    assert abs(proof['blasius']['coarseWall'] - .3320573362151963) < 1e-9
    assert abs(proof['blasius']['coarseWall'] - proof['blasius']['fineWall']) < 1e-9


def test_independent_collocation_quadrature_and_adaptive_force_solutions():
    proof = checked_run([sys.executable, 'tools/check_fluids_independent.py'])
    areas = {row['area']: row for row in proof['checks']}
    assert set(areas) == {'continuity and Bernoulli', 'original Venturi preservation', 'hydrostatics',
                          'pistons', 'buoyancy', 'pipe', 'boundary layer', 'settling',
                          'ideal lift', 'plume scaling', 'invalid domains'}
    assert all(row['result'] == 'pass' and row['cases'] > 0 for row in areas.values())
    assert areas['boundary layer']['refinement'] < 1e-7
    assert 'collocation' in areas['pipe']['method']
    assert 'DOP853' in areas['settling']['method']
    assert 'adaptive pressure/circulation' in areas['ideal lift']['method']
    assert '30 kPa' in areas['continuity and Bernoulli']['method']
    assert proof['remainingActionableScientificDefects'] == []

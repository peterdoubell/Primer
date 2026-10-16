"""Run real numerical oracles without changing frozen proof artifacts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/measurement-fidelity-review-20261016'
SOURCE_SHA256 = '8a1d68588bb9689146a5673c1d2f7f7b4fad10213f53c10f47c4d1c35bd537af'
pytestmark = pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required for measurement numerical checks')


def proof_identities():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in REVIEW.rglob('*') if path.is_file()}


def checked_run(command):
    before = proof_identities()
    environment = os.environ.copy()
    environment.pop('MEASUREMENT_WRITE_PROOF', None)
    environment.pop('MEASUREMENT_PROOF_OUTPUT', None)
    completed = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                               capture_output=True, check=True, timeout=60)
    assert proof_identities() == before, 'Default numerical checks must not modify review evidence'
    result = json.loads(completed.stdout)
    assert result['allPassed'] is True
    assert result['sourceSHA256'] == SOURCE_SHA256
    assert hashlib.sha256((ROOT / 'web/measurement-lab.js').read_bytes()).hexdigest() == SOURCE_SHA256
    return result


def test_core_measurement_oracles_check_actual_calculations_without_writing_proofs():
    proof = checked_run(['node', 'tools/check_measurement_core.cjs'])
    assert {name: proof[name] for name in ['propagationCases', 'intervalCases', 'repeatCases', 'fitCases', 'invalidCasesRejected']} == {
        'propagationCases': 1620, 'intervalCases': 324, 'repeatCases': 405,
        'fitCases': 486, 'invalidCasesRejected': 35,
    }
    assert 'weighted modified Gram-Schmidt QR fit and covariance' in proof['methods']
    assert 'explicit repeat covariance sums' in proof['methods']


def test_independent_exact_scientific_oracles_and_both_numerical_regressions():
    proof = checked_run([sys.executable, 'tools/check_measurement_independent.py'])
    checks = {check['area']: check for check in proof['checks']}
    assert all(check['result'] == 'pass' for check in checks.values())
    assert {name: checks[name]['cases'] for name in ['propagation', 'intervals', 'invalid inputs', 'repeat budget', 'weighted known-sigma fitting']} == {
        'propagation': 60, 'intervals': 18, 'invalid inputs': 14,
        'repeat budget': 36, 'weighted known-sigma fitting': 17,
    }
    assert 'no silent residual rescaling' in checks and 'synthetic fit meaning' in checks
    assert proof['requestCount'] == 145
    assert proof['initial_defect']['corrected_in_reviewed_source']
    assert proof['initial_defect']['expected_fitted'] == [8 / 9, 20 / 9, 32 / 9]
    assert proof['initial_defect']['expected_chi_square'] == 1 / 9
    rejection = proof['tiny_spacing_defect']
    assert rejection['corrected_in_reviewed_source'] and rejection['nonfinite_results_returned'] is False
    assert {row['id'] for row in rejection['fixtures']} == {
        'unrepresentable-covariance-1e-155', 'unrepresentable-covariance-1e-160',
    }
    for row in rejection['fixtures']:
        assert row['error']['name'] == 'RangeError' and 'rescale' in row['error']['message'].lower()
    assert proof['remaining_actionable_scientific_defects'] == []
    assert proof['renderer_verified_by_this_review'] is False

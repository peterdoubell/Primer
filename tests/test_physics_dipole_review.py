"""Current dipole display evidence is separate from historical source approvals."""
import hashlib
import json
from pathlib import Path

import pytest

from tools.physics_dipole_runtime_compatibility import before_dipole_bytes

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/physics-dipole-orientation-review-20261014'


def test_only_the_recorded_dipole_renderer_delta_can_restore_historical_bytes():
    proof = json.loads((REVIEW / 'runtime-inverse.json').read_text())
    raw = (ROOT / proof['path']).read_bytes()
    assert hashlib.sha256(before_dipole_bytes(proof['path'], raw)).hexdigest() == proof['before_sha256']
    assert proof['clinical_approval'] is proof['extends_historical_approval'] is False
    with pytest.raises(ValueError, match='Unreviewed'):
        before_dipole_bytes(proof['path'], raw + b'changed')


def test_reader_evidence_covers_current_authored_corners_and_resets():
    proof = json.loads((REVIEW / 'reader-proof.json').read_text())
    assert {(r['id'], r['width']) for r in proof['rows']} == {('phys.1.magnets', 1440), ('phys.1.magnets', 390)}
    assert not proof['errors'] and proof['production_verified'] is False
    digest = hashlib.sha256((ROOT / 'web/lesson-models.js').read_bytes()).hexdigest()
    assert all(r['served_renderer_sha256'] == digest and r['controls'] == 2 and r['checked_states'] == 17 for r in proof['rows'])


def test_exact_model_limits_remain_visible_in_the_shipped_lesson():
    source = (ROOT / 'web/lesson-models.js').read_text()
    assert 'each 1 A m²' in source
    assert 'prescribed snapshots, not free motion' in source
    assert 'At 90° axial force vanishes but sideways force and torque remain' in source
    assert 'Finite bar geometry, induced magnetization and close-contact forces are not solved' in source

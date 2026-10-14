"""Historical curriculum views accept only the four recorded description lines."""
import hashlib
import json
from pathlib import Path

import pytest

from tools import math_growth_runtime_compatibility as bridge

ROOT = Path(__file__).resolve().parents[1]


def test_exact_inverse_restores_only_four_activity_description_lines():
    proof = json.loads((ROOT / bridge.PROOF).read_bytes())
    raw = (ROOT / bridge.PATH).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == bridge.AFTER_SHA
    restored = bridge.before_growth_bytes(bridge.PATH, raw)
    assert hashlib.sha256(restored).hexdigest() == bridge.BEFORE_SHA
    assert bridge.before_growth_bytes(bridge.PATH, restored) == restored
    assert proof['clinical_approval'] is proof['extends_historical_approval'] is False
    assert len(proof['changes']) == 2
    for change in proof['changes']:
        assert change['end'] - change['start'] == 2
        for key in ['before', 'after']:
            lines = change[key].splitlines()
            assert len(lines) == 2
            assert lines[0].lstrip().startswith('"title":')
            assert lines[1].lstrip().startswith('"instructions":')
    from tools.physics_dipole_runtime_compatibility import before_dipole_bytes
    assert before_dipole_bytes(bridge.PATH, raw) == restored


def test_unknown_curriculum_bytes_are_rejected_and_never_normalized():
    raw = (ROOT / bridge.PATH).read_bytes()
    changed = raw + b'changed'
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_growth_bytes(bridge.PATH, changed)
    assert bridge.before_growth_bytes(bridge.PATH, changed, allow_older=True) == changed
    assert bridge.before_growth_bytes('unknown', b'unrelated') == b'unrelated'
    from tools.physics_dipole_runtime_compatibility import before_dipole_bytes
    with pytest.raises(ValueError, match='Unreviewed'):
        before_dipole_bytes(bridge.PATH, changed)
    # Historical consumers that request older views still receive unknown
    # bytes intact, so their fixed SHA assertion cannot accept this mutation.
    from tools.systems_runtime_compatibility import previous_runtime_bytes
    assert previous_runtime_bytes(bridge.PATH, changed) == changed
    assert hashlib.sha256(changed).hexdigest() != bridge.BEFORE_SHA


def test_changed_inverse_evidence_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / bridge.PROOF
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / bridge.PROOF).read_bytes() + b'changed')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        bridge.before_growth_bytes(bridge.PATH, (ROOT / bridge.PATH).read_bytes())

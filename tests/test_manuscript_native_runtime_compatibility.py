"""The hosted allowance cannot silently change prior shared curriculum evidence."""
import hashlib,json
from pathlib import Path
import pytest
from tools import manuscript_native_runtime_compatibility as bridge
ROOT=Path(__file__).resolve().parents[1]

def test_exact_allowance_projection_and_proof_are_checked(tmp_path,monkeypatch):
    proof=bridge.PROOF.read_bytes();assert hashlib.sha256(proof).hexdigest()==bridge.PIN
    row=json.loads(proof)['primer/curriculum.py'];raw=(ROOT/'primer/curriculum.py').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['after']
    before=bridge.before_manuscript_native_bytes('primer/curriculum.py',raw)
    assert hashlib.sha256(before).hexdigest()==row['before']
    assert bridge.before_manuscript_native_bytes('primer/curriculum.py',before)==before
    assert bridge.before_manuscript_native_bytes('primer/curriculum.py',raw+b'unreviewed')==raw+b'unreviewed'
    assert bridge.before_manuscript_native_bytes('unrelated',b'exact')==b'exact'
    changed=tmp_path/'proof.json';changed.write_bytes(proof+b'changed');monkeypatch.setattr(bridge,'PROOF',changed)
    with pytest.raises(ValueError,match='evidence changed'):
        bridge.before_manuscript_native_bytes('primer/curriculum.py',raw)

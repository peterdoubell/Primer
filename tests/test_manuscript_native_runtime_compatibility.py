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


def test_direct_shell_projection_keeps_the_recorded_reader_curriculum_fingerprint():
    from tools.module_mission_compatibility import previous_shell_bytes
    name='primer/curriculum.py';raw=(ROOT/name).read_bytes()
    row=json.loads(bridge.PROOF.read_bytes())[name]
    restored=previous_shell_bytes(name,raw)
    assert hashlib.sha256(restored).hexdigest()==row['before']
    assert previous_shell_bytes(name,restored)==restored
    assert previous_shell_bytes(name,raw+b'foreign')==raw+b'foreign'

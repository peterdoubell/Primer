"""Candidate correspondence preserves bytes and never swallows unrelated changes."""
import hashlib,json
from pathlib import Path
import pytest
from tools import systems_runtime_compatibility as bridge
ROOT=Path(__file__).resolve().parents[1]


def test_every_named_addition_restores_only_its_exact_previous_bytes():
    proof=json.loads((ROOT/bridge.PROOF).read_bytes())
    assert set(proof['files'])=={'primer/curriculum.py','primer/server.py','web/index.html','web/lesson-models.js','data/curriculum/01-mathematics.json'}
    for path,row in proof['files'].items():
        from tools.thoracic_native_runtime_compatibility import previous_runtime_bytes as before_native
        raw=before_native(path,(ROOT/path).read_bytes());assert hashlib.sha256(raw).hexdigest()==row['current_sha256']
        restored=bridge.previous_runtime_bytes(path,raw);assert hashlib.sha256(restored).hexdigest()==row['before_sha256']
        assert bridge.previous_runtime_bytes(path,restored)==restored
        assert bridge.previous_runtime_bytes(path,raw+b'changed')==raw+b'changed'
    assert bridge.previous_runtime_bytes('unknown',b'unrelated')==b'unrelated'


def test_forged_inverse_evidence_is_rejected(tmp_path,monkeypatch):
    p=tmp_path/bridge.PROOF;p.parent.mkdir(parents=True);p.write_bytes((ROOT/bridge.PROOF).read_bytes()+b'changed')
    monkeypatch.setattr(bridge,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='evidence changed'):bridge.previous_runtime_bytes('unknown',b'unrelated')


def test_unrelated_source_mutations_still_reach_and_fail_original_guards():
    from tools.number_theory_runtime_compatibility import pulmonary_product_bytes
    for path in ['primer/server.py','web/lesson-models.js','web/index.html']:
        with pytest.raises(ValueError,match='Unreviewed'):pulmonary_product_bytes(path,(ROOT/path).read_bytes()+b'changed')

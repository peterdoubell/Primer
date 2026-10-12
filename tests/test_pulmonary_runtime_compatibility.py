"""A strict offline comparison cannot waive current UI/clinical/source review."""
import hashlib
import json
from pathlib import Path
import pytest
from tools import pulmonary_runtime_compatibility as compatibility
ROOT=Path(__file__).resolve().parents[1]


def test_exact_named_union_blocks_restore_the_reviewed_main_only():
    proof=json.loads((ROOT/compatibility.PROOF).read_bytes())
    assert hashlib.sha256((ROOT/compatibility.PROOF).read_bytes()).hexdigest()==compatibility.PROOF_SHA256
    assert set(proof['files'])==set(compatibility.PINS)=={'primer/server.py','primer/module_media.py','web/lesson-models.js','primer/source_native_inspectors.py'}
    assert proof['historical_approval_extended'] is proof['clinical_approval'] is proof['fine_anatomical_approval'] is False
    for path,(before,after) in compatibility.PINS.items():
        raw=(ROOT/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==after
        restored=compatibility.restore_main_runtime_bytes(path,raw)
        assert hashlib.sha256(restored).hexdigest()==before
        assert compatibility.restore_main_runtime_bytes(path,restored)==restored
    app=compatibility.restore_main_runtime_bytes('web/app.js',(ROOT/'web/app.js').read_bytes())
    assert hashlib.sha256(app).hexdigest()=='d77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0'
    assert compatibility.restore_main_runtime_bytes('unknown',b'unrelated')==b'unrelated'


@pytest.mark.parametrize('path',['primer/server.py','primer/module_media.py','web/lesson-models.js','primer/source_native_inspectors.py','web/app.js'])
def test_mutated_current_file_cannot_reuse_prior_proof(path):
    with pytest.raises(ValueError,match='Unreviewed'):
        compatibility.restore_main_runtime_bytes(path,(ROOT/path).read_bytes()+b'changed')


def test_changed_inverse_evidence_cannot_restore_current_source(tmp_path,monkeypatch):
    target=tmp_path/compatibility.PROOF;target.parent.mkdir(parents=True)
    target.write_bytes((ROOT/compatibility.PROOF).read_bytes()+b'changed')
    monkeypatch.setattr(compatibility,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='inverse evidence changed'):
        compatibility.restore_main_runtime_bytes('primer/server.py',(ROOT/'primer/server.py').read_bytes())

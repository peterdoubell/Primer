"""Immutable evidence is data; relocation cannot grant approval or accept changed bytes."""
import hashlib
import json
from pathlib import Path
import pytest
from tools import qft_evidence_storage as storage

ROOT = Path(__file__).resolve().parents[1]

def test_exact_seven_recorded_artifacts_and_original_receipt_pins_are_preserved():
    manifest = json.loads((ROOT/'docs/physics-qft-integrated-reader-review-20261011/evidence-storage-relocations.json').read_text())
    assert len(manifest['rows']) == len(storage.RELOCATIONS) == 7
    assert manifest['runtime_security_approval_granted'] is False
    for row in manifest['rows']:
        record = storage.RELOCATIONS[row['historical_path']]
        assert record == {'data_path':row['inert_data_path'], 'sha256':row['sha256'], 'bytes':row['bytes']}
        assert not (ROOT/row['historical_path']).exists()
        raw = storage.relocated_evidence_bytes(row['historical_path'],row['sha256'])
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    review = json.loads((ROOT/'docs/physics-qft-integrated-science-review-20261011/representability-scientific-amendment.json').read_text())
    for path, pin in review['evidence'].items():
        raw = storage.relocated_evidence_bytes(path,pin) if path in storage.RELOCATIONS else (ROOT/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==pin


def test_unknown_paths_wrong_pins_and_mutated_data_are_rejected(tmp_path,monkeypatch):
    path,row = next(iter(storage.RELOCATIONS.items()))
    with pytest.raises(ValueError,match='Unknown'):
        storage.relocated_evidence_bytes('../unrelated',row['sha256'])
    with pytest.raises(ValueError,match='Unknown'):
        storage.relocated_evidence_bytes(path,'0'*64)
    target = tmp_path/row['data_path'];target.parent.mkdir(parents=True)
    target.write_bytes((ROOT/row['data_path']).read_bytes()+b'changed')
    monkeypatch.setattr(storage,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='data changed'):
        storage.relocated_evidence_bytes(path,row['sha256'])

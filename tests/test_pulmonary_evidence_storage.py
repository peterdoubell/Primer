"""Inert source references retain exact bytes and reject substitutions."""
from pathlib import Path
import hashlib
import json
import pytest
from tools import pulmonary_evidence_storage as storage
ROOT=Path(__file__).resolve().parents[1]


def test_five_historical_source_bytes_and_paths_resolve_exactly():
    manifest=json.loads((ROOT/'docs/pulmonary-release-integration-review-20261012/evidence-storage-relocations.json').read_text())
    assert len(manifest['rows'])==len(storage.RELOCATIONS)==5
    assert not manifest['active_checkers_moved'] and not manifest['historical_approval_extended']
    for row in manifest['rows']:
        assert storage.RELOCATIONS[row['historical_path']]=={k:row[k] for k in ['data_path','sha256','bytes']}
        assert not (ROOT/row['historical_path']).exists()
        raw=storage.historical_evidence_bytes(row['historical_path'],row['sha256'])
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']


def test_unknown_paths_and_wrong_pins_fail_closed():
    path,row=next(iter(storage.RELOCATIONS.items()))
    with pytest.raises(ValueError,match='Unknown'):
        storage.historical_evidence_bytes('../unrelated',row['sha256'])
    with pytest.raises(ValueError,match='Unknown'):
        storage.historical_evidence_bytes(path,'0'*64)


@pytest.mark.parametrize('mutation',['bytes','leaf_symlink','parent_symlink'])
def test_mutation_and_symlinks_cannot_substitute_evidence(tmp_path,monkeypatch,mutation):
    path,row=next(iter(storage.RELOCATIONS.items()));target=tmp_path/row['data_path']
    target.parent.mkdir(parents=True);original=(ROOT/row['data_path']).read_bytes()
    if mutation=='bytes':target.write_bytes(original+b'changed')
    elif mutation=='leaf_symlink':
        elsewhere=tmp_path/'elsewhere.txt';elsewhere.write_bytes(original);target.symlink_to(elsewhere)
    else:
        elsewhere=tmp_path/'outside';elsewhere.mkdir();(elsewhere/target.name).write_bytes(original)
        target.parent.rmdir();target.parent.symlink_to(elsewhere,target_is_directory=True)
    monkeypatch.setattr(storage,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='changed|symlink'):
        storage.historical_evidence_bytes(path,row['sha256'])

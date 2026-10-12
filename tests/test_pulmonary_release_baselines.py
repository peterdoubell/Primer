"""Historical byte fixtures work without Git history and cannot admit other data."""
import hashlib
from pathlib import Path
import pytest
from tools import pulmonary_release_baselines as baseline


@pytest.mark.parametrize('name', sorted(baseline.BASELINES))
def test_frozen_baseline_has_exact_original_bytes(name):
    raw=baseline.read_baseline(name);row=baseline.BASELINES[name]
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']


@pytest.mark.parametrize('name',['unknown.json','../vercel.json','/vercel.json'])
def test_unknown_or_nonliteral_name_is_rejected(name):
    with pytest.raises(ValueError,match='Unknown'):baseline.read_baseline(name)


def test_mutation_and_missing_data_cannot_use_current_files(tmp_path,monkeypatch):
    row=baseline.BASELINES['vercel.json'];path=tmp_path/row['file'];path.parent.mkdir(parents=True);path.write_bytes(baseline.read_baseline('vercel.json')+b'\n')
    (tmp_path/'vercel.json').write_bytes(baseline.read_baseline('vercel.json'))
    monkeypatch.setattr(baseline,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='bytes changed'):baseline.read_baseline('vercel.json')
    path.unlink()
    with pytest.raises(ValueError,match='regular file'):baseline.read_baseline('vercel.json')


@pytest.mark.parametrize('parent',[False,True])
def test_leaf_or_parent_symlink_is_rejected(tmp_path,monkeypatch,parent):
    raw=baseline.read_baseline('vercel.json');relative=Path(baseline.BASELINES['vercel.json']['file'])
    actual=tmp_path/'real';actual.mkdir();(actual/'vercel.json.txt').write_bytes(raw)
    target=tmp_path/relative
    if parent:
        target.parent.parent.mkdir(parents=True);target.parent.symlink_to(actual,target_is_directory=True)
    else:
        target.parent.mkdir(parents=True);target.symlink_to(actual/'vercel.json.txt')
    monkeypatch.setattr(baseline,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='symlink'):baseline.read_baseline('vercel.json')

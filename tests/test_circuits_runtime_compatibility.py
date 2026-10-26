"""Recorded changes cannot silently alter the evidence for prior releases."""
import copy
from pathlib import Path
import pytest
from tools import circuits_runtime_compatibility as bridge
ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('path', sorted(bridge.PATHS))
def test_exact_current_delta_recovers_base_and_rejects_foreign_edits(path):
    row = bridge.reviewed()['files'][path]
    raw = (ROOT / path).read_bytes()
    from tools.percentage_runtime_compatibility import before_percentage_bytes
    assert bridge.sha(before_percentage_bytes(path, raw, allow_older=True)) == row['after_sha256']
    before = bridge.before_circuits_bytes(path, raw)
    assert bridge.sha(before) == row['before_sha256']
    assert bridge.before_circuits_bytes(path, before) == before
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_circuits_bytes(path, raw + b'\nunreviewed\n')
    assert bridge.before_circuits_bytes(path, raw + b'\n', allow_older=True) == raw + b'\n'

@pytest.mark.parametrize('side', ['before', 'after'])
def test_literal_and_restored_hash_are_both_checked(monkeypatch, side):
    proof = copy.deepcopy(bridge.reviewed())
    proof['files']['web/index.html']['changes'][0][side] += 'foreign'
    monkeypatch.setattr(bridge, 'reviewed', lambda: proof)
    with pytest.raises(ValueError, match='literal|baseline'):
        bridge.before_circuits_bytes('web/index.html', (ROOT / 'web/index.html').read_bytes())


def test_unrelated_paths_are_preserved():
    assert bridge.before_circuits_bytes('unrelated', b'exact') == b'exact'

def test_proof_bytes_are_checked_before_use(tmp_path, monkeypatch):
    target = tmp_path / bridge.PROOF
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / bridge.PROOF).read_bytes() + b'\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        bridge.reviewed()

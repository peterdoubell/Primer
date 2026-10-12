"""Bounded historical proof preservation cannot hide unrelated byte/semantic edits."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from tools import qft_runtime_compatibility as compatibility

ROOT = Path(__file__).resolve().parents[1]


def test_each_named_current_and_historical_pair_has_exact_recorded_bytes():
    for path, row in compatibility.FILES.items():
        current = (ROOT/path).read_bytes()
        assert hashlib.sha256(compatibility.restore_main_runtime_bytes(path,current)).hexdigest() == row['current_sha256']
        old = compatibility.historical_runtime_bytes(path, current)
        assert hashlib.sha256(old).hexdigest() == row['baseline_sha256']
    assert compatibility.historical_runtime_bytes('unknown-file', b'unrelated') == b'unrelated'


@pytest.mark.parametrize('path', ['primer/server.py', 'web/spatial-models.js', 'web/lesson-state.js'])
def test_current_byte_mutation_cannot_reuse_historical_approval(path):
    with pytest.raises(ValueError, match='Unreviewed QFT compatibility byte change'):
        compatibility.historical_runtime_bytes(path, (ROOT/path).read_bytes()+b'changed')


@pytest.mark.parametrize('path', ['data/curriculum/03-physics.json', 'data/module-models.json'])
def test_even_forged_new_hash_cannot_hide_unrelated_semantic_change(path, monkeypatch):
    value = json.loads((ROOT/path).read_text())
    key = 'nodes' if 'curriculum/' in path else 'models'
    identity = 'id' if key == 'nodes' else 'node_id'
    row = next(row for row in value[key] if row[identity] != 'phys.5.qft')
    row['title'] = 'An unrelated changed lesson'
    raw = json.dumps(value).encode()
    revised = copy.deepcopy(compatibility.FILES[path])
    revised['current_sha256'] = hashlib.sha256(raw).hexdigest()
    monkeypatch.setitem(compatibility.FILES, path, revised)
    with pytest.raises(ValueError, match='Unrelated physics/binding change'):
        compatibility.historical_runtime_bytes(path, raw)

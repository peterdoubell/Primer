"""New shape geometry cannot silently inherit a historical scientific approval."""
import hashlib
import json
from pathlib import Path
import pytest
from tools.plane_shapes_runtime_compatibility import before_shapes_bytes, reviewed

ROOT = Path(__file__).resolve().parents[1]


def test_exact_inverse_is_idempotent_and_rejects_foreign_bytes():
    for path, row in reviewed()['files'].items():
        raw = (ROOT / path).read_bytes()
        restored = before_shapes_bytes(path, raw)
        assert hashlib.sha256(restored).hexdigest() == row['before_sha256']
        assert before_shapes_bytes(path, restored) == restored
        with pytest.raises(ValueError, match='Unreviewed'):
            before_shapes_bytes(path, raw + b'changed')
    assert before_shapes_bytes('unrelated', b'unchanged') == b'unchanged'


def test_only_the_shapes_binding_changes_in_the_manifest():
    path = 'data/module-models.json'
    current = json.loads((ROOT / path).read_bytes())['models']
    prior = json.loads(before_shapes_bytes(path, (ROOT / path).read_bytes()))['models']
    assert [a['node_id'] for a, b in zip(current, prior, strict=True) if a != b] == ['math.0.shapes']
    assert next(a for a in current if a['node_id'] == 'math.0.shapes')['family'] == 'plane-shapes'

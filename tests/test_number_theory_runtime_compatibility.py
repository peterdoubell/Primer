"""Fixed union correspondence cannot hide changed source or reuse forged evidence."""
import hashlib
import json
from pathlib import Path
import pytest
from tools import number_theory_runtime_compatibility as bridge
from tools.systems_runtime_compatibility import previous_runtime_bytes
ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('view',['pulmonary_views','math_views'])
def test_every_fixed_product_inverse_is_exact_and_idempotent(view):
    proof=json.loads((ROOT/bridge.PRODUCT_PROOF).read_bytes())
    for path,row in proof[view].items():
        raw=(ROOT/path).read_bytes();restored=bridge.product_view(path,raw,view)
        assert hashlib.sha256(previous_runtime_bytes(path,raw)).hexdigest()==row['current_sha256']
        assert hashlib.sha256(restored).hexdigest()==row['baseline_sha256']
        assert bridge.product_view(path,restored,view)==restored
        with pytest.raises(ValueError,match='Unreviewed'):bridge.product_view(path,raw+b'changed',view)
    assert bridge.product_view('unknown',b'unrelated',view)==b'unrelated'


def test_self_oracle_inverse_preserves_every_original_byte():
    proof=json.loads((ROOT/bridge.TEST_PROOF).read_bytes())
    for path,row in proof['files'].items():
        raw=(ROOT/path).read_bytes();restored=bridge.math_test_bytes(path,raw)
        assert restored==(ROOT/row['baseline_copy']).read_bytes()
        with pytest.raises(ValueError,match='Unreviewed'):bridge.math_test_bytes(path,raw+b'changed')
    assert bridge.math_test_bytes('unknown',b'unrelated')==b'unrelated'


@pytest.mark.parametrize('kind',['product','test'])
def test_changed_fixed_evidence_fails_closed(tmp_path,monkeypatch,kind):
    relative=bridge.PRODUCT_PROOF if kind=='product' else bridge.TEST_PROOF
    p=tmp_path/relative;p.parent.mkdir(parents=True);p.write_bytes((ROOT/relative).read_bytes()+b'changed')
    monkeypatch.setattr(bridge,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='evidence changed'):
        if kind=='product':bridge.product_view('unknown',b'unrelated','math_views')
        else:bridge.math_test_bytes('unknown',b'unrelated')

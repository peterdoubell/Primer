"""Historical byte views cannot approve or conceal unrelated source changes."""
from pathlib import Path
import copy
import hashlib
import json
import pytest
from tools import holiatlas_runtime_compatibility as bridge

ROOT = Path(__file__).resolve().parents[1]


def test_exact_inverse_recovers_the_complete_base_and_rejects_unknown_changes():
    for path, row in bridge.reviewed()['files'].items():
        raw = (ROOT/path).read_bytes()
        previous = bridge.before_holiatlas_bytes(path, raw)
        assert hashlib.sha256(previous).hexdigest() == row['before_sha256']
        assert bridge.before_holiatlas_bytes(path, previous) == previous
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_holiatlas_bytes(path, raw + b'foreign change')


def test_ledger_inverse_removes_only_the_exact_atlas_append():
    raw = (ROOT / bridge.LEDGER_PATH).read_bytes()
    proof = bridge.reviewed_ledger()
    restored = bridge.before_holiatlas_bytes(bridge.LEDGER_PATH, raw)
    assert hashlib.sha256(restored).hexdigest() == proof['before_sha256']
    assert bridge.before_holiatlas_bytes(bridge.LEDGER_PATH, restored) == restored
    current, prior = json.loads(raw), json.loads(restored)
    assert current['refreshes'][:-1] == prior['refreshes']
    assert current['refreshes'][-1]['id'] == proof['source_refresh_id']
    assert {k: v for k, v in current.items() if k != 'refreshes'} == {
        k: v for k, v in prior.items() if k != 'refreshes'}
    assert proof['runtime_inverse_sha256'] == bridge.PROOF_SHA256


@pytest.mark.parametrize('mutation', ['duplicate', 'historical', 'approval', 'format'])
def test_ledger_inverse_rejects_changed_or_duplicated_entries(mutation):
    raw = (ROOT / bridge.LEDGER_PATH).read_bytes()
    ledger = json.loads(raw)
    if mutation == 'duplicate':
        ledger['refreshes'].append(copy.deepcopy(ledger['refreshes'][-1]))
    elif mutation == 'historical':
        ledger['refreshes'][0]['id'] += '-unreviewed'
    elif mutation == 'approval':
        ledger['refreshes'][-1]['clinical_approval'] = True
    changed = raw + b'\n' if mutation == 'format' else json.dumps(ledger).encode()
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_holiatlas_bytes(bridge.LEDGER_PATH, changed)
    assert bridge.before_holiatlas_bytes(bridge.LEDGER_PATH, changed, allow_older=True) == changed


def test_ledger_proof_is_pinned_separately_from_the_runtime_proof(tmp_path, monkeypatch):
    proof = tmp_path / bridge.LEDGER_PROOF
    proof.parent.mkdir(parents=True)
    proof.write_bytes((ROOT / bridge.LEDGER_PROOF).read_bytes() + b'\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        bridge.reviewed_ledger()


def test_only_the_exact_single_source_descriptor_can_be_removed():
    item = bridge.reviewed()['source_inspector_addition']
    fields = {'source_native_inspectors': [item], 'patient_observation': 'must remain'}
    assert bridge.before_holiatlas_reference_fields('ra.brain-anatomy', fields) == {
        'source_native_inspectors': [], 'patient_observation': 'must remain'}
    assert fields['source_native_inspectors'] == [item]
    for mutation in ['duplicate', 'approval', 'caption']:
        bad = copy.deepcopy(fields)
        if mutation == 'duplicate':
            bad['source_native_inspectors'].append(copy.deepcopy(item))
        elif mutation == 'approval':
            bad['source_native_inspectors'][0]['clinical_approval'] = True
        else:
            bad['source_native_inspectors'][0]['caption'] += 'unreviewed'
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_holiatlas_reference_fields('ra.brain-anatomy', bad)

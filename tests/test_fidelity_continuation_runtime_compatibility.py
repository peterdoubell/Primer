"""Current fidelity work cannot rewrite or silently extend historical evidence."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools import fidelity_continuation_runtime_compatibility as bridge
from tools.current_labs_runtime_compatibility import before_current_labs_bytes

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('path', sorted(bridge.PATHS | {bridge.LEDGER_PATH}))
def test_inverse_restores_exact_prior_bytes_and_rejects_unknown_changes(path):
    row = bridge.reviewed_ledger() if path == bridge.LEDGER_PATH else bridge.reviewed()['files'][path]
    raw = (ROOT / path).read_bytes()
    assert sha(before_current_labs_bytes(path, raw, allow_older=True)) == row['after_sha256']
    restored = bridge.before_continuation_bytes(path, raw)
    assert sha(restored) == row['before_sha256']
    assert bridge.before_continuation_bytes(path, restored) == restored
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_continuation_bytes(path, raw + b'\nunreviewed change\n')
    assert bridge.before_continuation_bytes(path, raw + b'\n', allow_older=True) == raw + b'\n'


def test_only_the_recorded_brain_descriptor_is_replaced_before_historical_removal():
    from tools.holiatlas_runtime_compatibility import before_holiatlas_reference_fields
    replacement = bridge.reviewed()['source_inspector_replacement']
    fields = {'source_native_inspectors': [{'id': 'unrelated', 'value': 7}, replacement['after']],
              'patient_observation': 'preserve'}
    expected = copy.deepcopy(fields)
    expected['source_native_inspectors'][1] = replacement['before']
    assert bridge.before_continuation_reference_fields('ra.brain-anatomy', fields) == expected
    assert fields['source_native_inspectors'][1] == replacement['after']
    assert bridge.before_continuation_reference_fields('ra.brain-anatomy', expected) == expected
    assert bridge.before_continuation_reference_fields('unrelated', fields) == fields
    assert before_holiatlas_reference_fields('ra.brain-anatomy', fields) == {
        'source_native_inspectors': [{'id': 'unrelated', 'value': 7}], 'patient_observation': 'preserve'}


@pytest.mark.parametrize('mutation', ['duplicate', 'approval', 'caption', 'mixed'])
def test_source_descriptor_drift_and_duplicates_are_rejected(mutation):
    replacement = bridge.reviewed()['source_inspector_replacement']
    fields = {'source_native_inspectors': [copy.deepcopy(replacement['after'])]}
    if mutation == 'duplicate':
        fields['source_native_inspectors'].append(copy.deepcopy(replacement['after']))
    elif mutation == 'mixed':
        fields['source_native_inspectors'].append(copy.deepcopy(replacement['before']))
    elif mutation == 'approval':
        fields['source_native_inspectors'][0]['clinical_approval'] = True
    else:
        fields['source_native_inspectors'][0]['caption'] += ' unreviewed'
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_continuation_reference_fields('ra.brain-anatomy', fields)


def test_ledger_addition_is_explicitly_native_and_preserves_all_prior_entries():
    raw = (ROOT / bridge.LEDGER_PATH).read_bytes()
    current = json.loads(raw)
    prior = json.loads(bridge.before_continuation_bytes(bridge.LEDGER_PATH, raw))
    assert current['refreshes'][:-1] == prior['refreshes']
    assert {k: v for k, v in current.items() if k != 'refreshes'} == {
        k: v for k, v in prior.items() if k != 'refreshes'}
    step = current['refreshes'][-1]
    assert step['id'] == bridge.REFRESH_ID
    assert step['native_presentation_code_touched'] is True
    assert step['native_decoder_mesh_CT_renderer_code_touched'] is True
    assert step['canonical_lesson_data_changed'] is True
    assert set(step['native_runtime_files']) == bridge.PATHS
    assert step['files'] == {}
    for mutation in ('duplicate', 'historical', 'approval'):
        changed = copy.deepcopy(current)
        if mutation == 'duplicate':
            changed['refreshes'].append(copy.deepcopy(step))
        elif mutation == 'historical':
            changed['refreshes'][0]['id'] += '-unreviewed'
        else:
            changed['refreshes'][-1]['clinical_approval'] = True
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_continuation_bytes(bridge.LEDGER_PATH, json.dumps(changed).encode())


def test_physics_inverse_preserves_all_ten_questions_and_other_lessons():
    path = 'data/curriculum/03-physics.json'
    current = json.loads(before_current_labs_bytes(path, (ROOT / path).read_bytes()))
    prior = json.loads(bridge.before_continuation_bytes(path, (ROOT / path).read_bytes()))
    changed = [a['id'] for a, b in zip(current['nodes'], prior['nodes'], strict=True) if a != b]
    assert changed == ['phys.3.energy-work']
    a = next(n for n in current['nodes'] if n['id'] == changed[0])
    b = next(n for n in prior['nodes'] if n['id'] == changed[0])
    assert len(a['quiz']) == 10 and a['quiz'] == b['quiz']
    assert {k: v for k, v in a.items() if k not in {'lesson', 'learning_outcomes'}} == b


@pytest.mark.parametrize('path,constant,reader', [
    (bridge.PROOF, 'PROOF_SHA256', bridge.reviewed),
    (bridge.LEDGER_PROOF, 'LEDGER_PROOF_SHA256', bridge.reviewed_ledger),
])
def test_proof_bytes_and_scope_are_bound_before_use(tmp_path, monkeypatch, path, constant, reader):
    file = tmp_path / path
    file.parent.mkdir(parents=True)
    raw = (ROOT / path).read_bytes()
    file.write_bytes(raw + b'\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        reader()
    proof = json.loads(raw)
    proof['extends_historical_approval'] = True
    changed = json.dumps(proof).encode()
    file.write_bytes(changed)
    monkeypatch.setattr(bridge, constant, sha(changed))
    with pytest.raises(ValueError, match='scope'):
        reader()


@pytest.mark.parametrize('side', ['before', 'after'])
def test_inverse_verifies_literal_delta_and_restored_baseline(monkeypatch, side):
    proof = copy.deepcopy(bridge.reviewed())
    proof['files']['web/index.html']['changes'][0][side] += '\nchanged\n'
    monkeypatch.setattr(bridge, 'reviewed', lambda: proof)
    with pytest.raises(ValueError, match='literal|baseline'):
        bridge.before_continuation_bytes('web/index.html', (ROOT / 'web/index.html').read_bytes())


def test_current_readers_are_validated_separately_from_the_inverse():
    readers = bridge.validate_current()
    assert set(readers) == bridge.READER_PATHS
    assert all(reader['allPassed'] and not reader['productionVerified'] for reader in readers.values())

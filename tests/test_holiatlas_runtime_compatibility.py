"""Historical byte views cannot approve or conceal unrelated source changes."""
from pathlib import Path
import copy
import hashlib
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

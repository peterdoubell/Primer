"""Historical comparisons restore only the exact scoped thoracic delta."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from tools import thoracic_data_compatibility as bridge
from tools.anatomy_sources import integrate_acute_stroke_sources as stroke
from tools.thoracic_motion_ui_compatibility import validate_refresh

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    'data/radiology/investigation-overrides-non-msk.json',
    'data/radiology/radiology-open-images.json',
    'data/radiology/radiology-asset-evidence.json',
    'data/radiology/reporting-steps/abdomen.json',
    'tools/anatomy_sources/pulmonary_ui_compatibility.py',
]


@pytest.mark.parametrize('path', PATHS)
def test_exact_inverse_preserves_previous_file_and_rejects_other_raw_edits(path):
    raw = (ROOT / path).read_bytes()
    proof = bridge.reviewed()
    assert set(proof['files']) == set(PATHS)
    restored = bridge.restore_raw(path, raw)
    assert hashlib.sha256(restored).hexdigest() == proof['files'][path]['before_sha256']
    assert bridge.restore_raw(path, restored) == restored
    with pytest.raises(ValueError, match='whole-file'):
        bridge.restore_raw(path, raw + b'\n')


def test_semantic_inverse_preserves_unrelated_drift_instead_of_hiding_it():
    path = 'data/radiology/investigation-overrides-non-msk.json'
    raw = (ROOT / path).read_text()
    data = json.loads(raw)
    tokens = stroke.unrelated_tokens(raw, Path(path), set())
    other = next(key for key in data if key != bridge.CASE)
    data[other]['unreviewed_extra'] = True
    restored, _ = bridge.restore_view(path, data, tokens)
    assert restored[other]['unreviewed_extra'] is True
    assert restored[bridge.CASE] == bridge.reviewed()['files'][path]['scoped_values']['before']
    data[bridge.CASE]['unreviewed_extra'] = True
    with pytest.raises(ValueError, match='scoped'):
        bridge.restore_view(path, data, tokens)


def test_changed_raw_value_token_or_effective_contract_is_rejected():
    path = 'data/radiology/investigation-overrides-non-msk.json'
    raw = (ROOT / path).read_text()
    tokens = stroke.unrelated_tokens(raw, Path(path), set())
    tokens[bridge.CASE] = '0' * 64
    with pytest.raises(ValueError, match='token'):
        bridge.restore_view(path, json.loads(raw), tokens)
    contract = copy.deepcopy(bridge.reviewed()['contract']['after'])
    contract['reporting']['protocol'].append('Unreviewed claim')
    with pytest.raises(ValueError, match='contract'):
        bridge.restore_contract(bridge.CASE, contract)


@pytest.mark.parametrize('field,value', [('clinical_approval', True), ('native_decoder_mesh_CT_renderer_code_touched', True), ('native_presentation_change_scope', 'all_rendering')])
def test_ui_refresh_cannot_extend_clinical_or_native_geometry_approval(field, value):
    ledger = json.loads((ROOT / 'data/radiology/ui-presentation-refreshes.json').read_text())
    step = copy.deepcopy(ledger['refreshes'][-1])
    validate_refresh(step)
    step[field] = value
    with pytest.raises(ValueError, match='scope'):
        validate_refresh(step)

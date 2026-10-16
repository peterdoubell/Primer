"""Historical evidence stays exact when the separate SPL source is added."""
import copy
import hashlib
from pathlib import Path

import pytest
from tools.spl_reporting_runtime_compatibility import before_reporting_bytes

from primer.curriculum import Curriculum
from tools.spl_limbic_runtime_compatibility import PATHS, before_spl_bytes, before_spl_lesson_fields, before_spl_reference_fields, reviewed

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('path', sorted(PATHS))
def test_exact_historical_reconstruction_rejects_unreviewed_bytes(path):
    raw = before_reporting_bytes(path, (ROOT / path).read_bytes())
    row = reviewed()['files'][path]
    assert hashlib.sha256(raw).hexdigest() == row['after_sha256']
    prior = before_spl_bytes(path, raw)
    assert hashlib.sha256(prior).hexdigest() == row['before_sha256']
    assert before_spl_bytes(path, prior) == prior
    with pytest.raises(ValueError, match='Unreviewed SPL'):
        before_spl_bytes(path, raw + b'\n')


@pytest.mark.parametrize('module_id', ['rad.5.epilepsy-mri', 'rad.5.dementia'])
def test_source_wrapper_meaning_is_reversed_without_removing_other_media(module_id):
    node = copy.deepcopy(Curriculum().nodes[module_id])
    fields = {'lesson_media': node['lesson_media']}
    row = reviewed()['lessons'][module_id]
    assert row['after'] in fields['lesson_media']
    prior = before_spl_lesson_fields(module_id, fields)
    assert row['before'] in prior['lesson_media']
    assert len(prior['lesson_media']) == len(fields['lesson_media'])
    assert [item for item in prior['lesson_media'] if item['id'] != row['before']['id']] == [
        item for item in fields['lesson_media'] if item['id'] != row['after']['id']]
    assert before_spl_lesson_fields(module_id, prior) == prior
    changed = copy.deepcopy(fields)
    target = next(item for item in changed['lesson_media'] if item['id'] == row['after']['id'])
    target['instructions'] += ' Unreviewed anatomical approval.'
    with pytest.raises(ValueError, match='Unreviewed SPL lesson'):
        before_spl_lesson_fields(module_id, changed)


def test_reference_inverse_only_removes_the_exact_reviewed_new_source():
    addition = reviewed()['source_inspector_addition']
    existing = {'id': 'existing-source', 'caption': 'Unchanged earlier source'}
    fields = {'source_native_inspectors': [existing, addition], 'other_field': 'retained'}
    expected = {'source_native_inspectors': [existing], 'other_field': 'retained'}
    assert before_spl_reference_fields('ra.mri-epilepsy', fields) == expected
    assert before_spl_reference_fields('ra.mri-epilepsy', expected) == expected
    duplicate = {'source_native_inspectors': [existing, addition, addition]}
    with pytest.raises(ValueError, match='Unreviewed SPL source'):
        before_spl_reference_fields('ra.mri-epilepsy', duplicate)
    altered = copy.deepcopy(fields)
    altered['source_native_inspectors'][1]['clinical_approval'] = True
    with pytest.raises(ValueError, match='Unreviewed SPL source'):
        before_spl_reference_fields('ra.mri-epilepsy', altered)


def test_ui_refresh_requires_the_current_reader_and_cannot_extend_native_approval():
    import json
    from tools.spl_limbic_runtime_compatibility import validate_refresh
    ledger = json.loads((ROOT / 'data/radiology/ui-presentation-refreshes.json').read_text())
    step = next(row for row in ledger['refreshes'] if row['id'] == '2026-10-16-spl-native-limbic-reference')
    assert len(validate_refresh(step)['cases']) == 24
    for key, value in [('clinical_approval', True), ('fine_anatomical_approval', True),
                       ('reopens_or_extends_any_review', True), ('native_decoder_mesh_CT_renderer_code_touched', True),
                       ('existing_reporting_guides_retained', False), ('native_presentation_change_scope', 'unreviewed')]:
        invalid = copy.deepcopy(step)
        invalid[key] = value
        with pytest.raises(ValueError, match='scope'):
            validate_refresh(invalid)
    invalid = copy.deepcopy(step)
    invalid['spl_reader_smoke']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='scope'):
        validate_refresh(invalid)

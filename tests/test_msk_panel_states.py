"""Explicit panel states cannot contradict a credited depiction claim."""
import copy
import json
from pathlib import Path

import pytest

from tools.check_msk_fidelity import inspect_binding

ROOT = Path(__file__).resolve().parents[1]
TARGET = {'id': 'fixture.structure', 'modality_scope': ['MRI'], 'context_requirements': []}


def asset(claim='normal_anatomical_reference', states=None, selected=None):
    return {'kind': 'clinical_image', 'modality': 'MRI',
            'source_context': {'depicted_state': claim,
                               'selected_panels': selected or ['a'],
                               'panel_types': {'a': 'MRI', 'b': 'MRI'},
                               'panel_states': {'a': 'normal_anatomy', 'b': 'ligamentum_flavum_hypertrophy'} if states is None else states},
            'representation_selection': {'kind': 'clinical_image', 'panels': selected or ['a']}}


@pytest.mark.parametrize('claim,states,selected,expected', [
    ('normal_anatomical_reference', {'a': 'normal_anatomy'}, ['a'], None),
    ('normal_variant', {'a': 'normal_anatomy', 'b': 'normal_variant'}, ['a', 'b'], None),
    ('normal_anatomy', {'a': 'ligamentum_flavum_hypertrophy'}, ['a'], 'source_context_selected_panel_state_mismatch'),
    ('ligamentum_flavum_hypertrophy', {'a': 'normal_anatomy'}, ['a'], 'source_context_selected_panel_state_mismatch'),
    ('ligamentum_flavum_hypertrophy', {'a': 'ligamentum_flavum_hypertrophy'}, ['a'], None),
    ('normal_anatomical_reference', {'a': 'unknown'}, ['a'], 'source_context_selected_panel_state_unresolved'),
    ('normal_anatomical_reference', {}, ['a'], 'source_context_selected_panel_state_unresolved'),
    ('unknown', {'a': 'unknown'}, ['a'], None),
    ('mixed', {'a': 'normal_anatomy', 'b': 'ligamentum_flavum_hypertrophy'}, ['a', 'b'], None),
])
def test_uniform_claim_matches_each_explicit_credited_panel(claim, states, selected, expected):
    issues = inspect_binding(asset(claim, states, selected), TARGET)
    assert issues == ([] if expected is None else [expected])


@pytest.mark.parametrize('states', [[], 'normal', {'a': ''}, {'a': None}, {'a': ['normal_anatomy']}, {'': 'normal_anatomy'}])
def test_malformed_panel_states_fail_without_guessing(states):
    assert 'source_context_panel_states_invalid' in inspect_binding(asset(states=states), TARGET)


def test_states_without_a_panel_selection_cannot_pass():
    value = asset()
    value['source_context'].pop('selected_panels')
    assert 'source_context_panel_selection_invalid' in inspect_binding(value, TARGET)


@pytest.mark.parametrize('claim', ['unknown', 'mixed'])
def test_nonuniform_or_unknown_context_does_not_satisfy_a_normal_target(claim):
    target = copy.deepcopy(TARGET)
    target['context_requirements'] = [{'depicted_state': 'normal_anatomical_reference'}]
    issues = inspect_binding(asset(claim), target)
    assert any(issue in issues for issue in ['source_context_depicted_state_unresolved',
                                            'source_context_depicted_state_mismatch'])


@pytest.mark.parametrize('panel', list('cdefgh'))
def test_lesser_plate_pathology_cannot_replace_the_intact_third_mtp_panels(panel):
    ledger = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())
    original = next(item for item in ledger['assets'] if item['id'] == 'open-lesser-mtp3-plantar-plate-mri-siddle-fig1')
    assert inspect_binding(original, TARGET) == []
    changed = copy.deepcopy(original)
    changed['source_context']['selected_panels'] = [panel]
    changed['representation_selection']['panels'] = [panel]
    assert changed['sha256'] == original['sha256']
    assert 'source_context_selected_panel_state_mismatch' in inspect_binding(changed, TARGET)

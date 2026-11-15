"""Wall patterns, collapsed segments and unacquired contrast cannot create anatomical or diagnostic certainty."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(r for r in data['investigations'] if r['investigation_id'] == 'ra.ct-bowel-wall')
    return {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': [item['investigation_id']]}}, item


def test_complete_wall_distribution_and_pattern_scope_matches_effective_reader():
    data, item = inventory(); ref = detail(Curriculum(), resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data, {item['investigation_id']: ref['reporting']})
    assert item['source_contract_sha256'] == digest({k: ref.get(k) for k in ['reporting', 'report_templates', 'walkthrough', 'reading']})
    leaves = {r['id']: r for r in requirements_for(item)}
    assert len(leaves) == 405
    for name in ['segment_duodenum_fourth.complete_source_extent', 'segment_hepatic_flexure.inner_wall_band_if_resolved',
                 'segment_terminal_ileum.antimesenteric_border', 'morphology.orthogonal_measurement_plane',
                 'pattern_stratified_target.observable_wall_bands', 'vessel_vasa_recta_if_resolved.bowel_interface',
                 'positive_examples.symmetric_neoplastic_example', 'positive_examples.non_ibd_fat_example']:
        assert 'bowel_wall.' + name in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']} == set(range(5))
    result = audit(data, {'assets': [{'id': 'parent', 'kind': 'model', 'investigation_ids': [item['investigation_id']],
                                    'structure_ids': ['bowel_wall.morphology', 'bowel_wall.pattern_stratified_target']}]}, expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements'] == 1215
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': 1215}


def test_normal_reference_cannot_supply_positive_wall_patterns_or_overlap_examples():
    _, item = inventory(); leaves = {r['id']: r for r in requirements_for(item)}
    normal = {'kind': 'clinical_image', 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    for name in ['pattern_white_attenuation.affected_region', 'neoplastic.symmetric_wall_if_present']:
        assert 'source_context_purpose_mismatch' in inspect_binding(normal, leaves['bowel_wall.' + name])


def test_normal_presets_preserve_actual_wall_distension_and_vessel_assessment_limits():
    ref = detail(Curriculum(), resolve('ra.ct-bowel-wall'))['radiology_reference']; steps = ref['walkthrough']['steps']
    assert 'unassessed' in str(steps[0]['normal']) and 'distension' in str(steps[0]['normal'])
    assert 'unassessed' in str(steps[3]['normal']) and 'actual opacification' in str(steps[3]['normal'])
    assert 'vessels patent' not in str(steps[3]['normal'])
    assert 'unassessed' in str(steps[4]['normal'])
    template = ref['report_templates'][0]['sections']
    assert 'unassessed' in next(r['body'] for r in template if r['heading'] == 'ENHANCEMENT PATTERN')
    assert 'baseline attenuation' in steps[2]['look']


def test_reader_retains_diagnostic_overlap_without_importing_universal_length_cutoffs():
    ref = detail(Curriculum(), resolve('ra.ct-bowel-wall'))['radiology_reference']; steps = ref['walkthrough']['steps']
    assert 'differ between teaching frameworks' in steps[0]['tip']
    assert not any('under 5 cm' in r or '5–10 cm' in r for r in steps[0]['findings'])
    assert 'Neoplasia is not excluded by symmetry alone' in steps[1]['findings'][0]
    assert 'pattern is nonspecific' in steps[2]['findings'][1]
    assert 'does not diagnose chronic inflammatory bowel disease' in steps[2]['findings'][3]
    assert len(ref['reporting']['sources']) == 3
    assert any('Immediately communicate' in r for r in ref['reporting']['escalation'])
    assert any('thickness' in r and 'diagnostic cutoffs' in r for r in ref['learning_points'])


def test_intramural_fat_requires_the_actual_feature_without_assuming_pathological_ibd():
    _, item = inventory(); leaves = {r['id']: r for r in requirements_for(item)}
    normal = {'kind': 'clinical_image', 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    requirement = leaves['bowel_wall.positive_examples.non_ibd_fat_example']
    assert 'source_context_depicted_state_mismatch' in inspect_binding(normal, requirement)
    observed_fat = {**normal, 'source_context': {'depicted_state': 'intramural_fat_non_ibd_source_context'}}
    issues = inspect_binding(observed_fat, requirement)
    assert 'source_context_purpose_mismatch' not in issues and 'source_context_depicted_state_mismatch' not in issues

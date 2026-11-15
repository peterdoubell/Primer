"""Actual bowel lesion extent and source phases cannot be replaced by negative presets or histology-like patterns."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(r for r in data['investigations'] if r['investigation_id'] == 'ra.ct-small-bowel-tumours')
    return {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': [item['investigation_id']]}}, item


def test_complete_lesion_host_vessel_and_spread_scope_matches_reader_contract():
    data, item = inventory(); ref = detail(Curriculum(), resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data, {item['investigation_id']: ref['reporting']})
    assert item['source_contract_sha256'] == digest({k: ref.get(k) for k in ['reporting', 'report_templates', 'walkthrough', 'reading']})
    leaves = {r['id']: r for r in requirements_for(item)}; assert len(leaves) == 329
    for suffix in ['segment_duodenum_fourth.outer_wall_band_if_resolved','each_primary.bowel_origin_interface',
                   'each_primary.adjacent_origin_interface','components.source_lumen_communication',
                   'luminal_effect.invaginated_mesentery','vessel_sma_and_actual_branches.branch_or_confluence',
                   'host_pancreatic_head_if_relevant.unassessed_invasion_boundary','spread_observations.each_hepatic_lesion',
                   'positive_examples.similarly_enhancing_small_lesion_example']:
        assert 'small_bowel_tumour.' + suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']} == set(range(5))
    result = audit(data, {'assets': [{'id':'parent','kind':'model','investigation_ids':[item['investigation_id']],
                                    'structure_ids':['small_bowel_tumour.each_primary','small_bowel_tumour.components']}]}, expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements'] == 987 and result['counts'] == {'verified':0,'unverified':0,'missing':987}


def test_normal_anatomy_does_not_provide_mass_components_or_staging_examples():
    _, item = inventory(); leaves = {r['id']: r for r in requirements_for(item)}
    normal = {'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    for suffix in ['each_primary.complete_lesion','components.solid_region','spread_observations.each_hepatic_lesion']:
        assert 'source_context_purpose_mismatch' in inspect_binding(normal, leaves['small_bowel_tumour.'+suffix])


def test_negative_presets_retain_bowel_vascular_and_spread_coverage_limits():
    ref = detail(Curriculum(), resolve('ra.ct-small-bowel-tumours'))['radiology_reference']; steps = ref['walkthrough']['steps']
    for index in [0,2,3,4]:
        assert 'unassessed' in str(steps[index]['normal'])
    assert 'No small-bowel mass' not in str(steps[0]['normal'])
    assert 'No liver or peritoneal metastases' not in str(steps[4]['normal'])
    assert 'actual coverage/opacification' in str(steps[3]['normal'])
    assert 'unassessed' in next(s['body'] for s in ref['report_templates'][0]['sections'] if s['heading']=='MORPHOLOGY')


def test_reader_does_not_assign_histology_grade_or_invasion_from_source_patterns():
    ref = detail(Curriculum(), resolve('ra.ct-small-bowel-tumours'))['radiology_reference']; steps = ref['walkthrough']['steps']
    assert 'not histological or risk proof' in steps[1]['findings'][1]
    assert 'molecular/mitotic grade' in steps[1]['tip']
    assert 'similarly enhancing lesion' in steps[1]['look']
    assert 'microscopic spread is not excluded' in steps[4]['look']
    assert len(ref['reporting']['sources']) == 3
    assert any('Communicate suspected' in r for r in ref['reporting']['escalation'])
    assert all('foreign body' not in p.lower() for p in ref['learning_points'][:5])

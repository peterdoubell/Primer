"""IUS reporting requires actual acoustic, Doppler and dynamic source evidence."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(r for r in data['investigations'] if r['investigation_id'] == 'ra.ultrasound-ibd')
    return {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': [item['investigation_id']]}}, item


def test_full_ius_scope_matches_reporting_and_leaves_all_new_coverage_missing():
    data, item = inventory()
    ref = detail(Curriculum(), resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data, {item['investigation_id']: ref['reporting']})
    assert item['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    leaves = {r['id']: r for r in requirements_for(item)}
    assert len(leaves) == 355
    for suffix in ['segment_terminal_ileum.fifth_acoustic_band_if_resolved', 'mural_findings.unresolved_band_or_histology_limit', 'doppler.settings_scale_gain_source', 'dynamics.compression_after_same_site', 'narrowing.actual_persistence_source', 'tracts.unresolved_endpoint_limit', 'collections.host_organ_interface', 'postoperative.neoterminal_ileum', 'mimics.diverticular_neck_if_resolved', 'comparison.technique_and_compression_correspondence', 'acquisition.deep_pelvic_limit']:
        assert 'ius_ibd.' + suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']} == set(range(5))
    result = audit(data, {'assets': [{'id': 'parent', 'kind': 'model', 'investigation_ids': [item['investigation_id']], 'structure_ids': ['ius_ibd.tracts', 'ius_ibd.doppler']}]}, expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements'] == 1065
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': 1065}


def test_mri_and_normal_reference_cannot_supply_ultrasound_positive_tracts():
    _, item = inventory()
    leaves = {r['id']: r for r in requirements_for(item)}
    mri = {'kind': 'clinical_image', 'modality': 'MRI', 'source_context': {'depicted_state': 'actual_penetrating_disease'}}
    target = leaves['ius_ibd.tracts.full_source_visible_course']
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(mri, target)
    normal = {**mri, 'modality': 'Ultrasound', 'source_context': {'depicted_state': 'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal, target)


def test_presets_preserve_unassessed_dynamics_doppler_histology_and_comparison():
    ref = detail(Curriculum(), resolve('ra.ultrasound-ibd'))['radiology_reference']
    steps = ref['walkthrough']['steps']
    assert all('unassessed' in str(s['normal']) for s in steps)
    assert 'unavailable' in str(steps[4]['normal'])
    assert 'No alternative cause; no change' not in str(steps[4]['normal'])
    assert 'Normal peristalsis; no stenosis' not in str(steps[3]['normal'])
    assert 'does not establish histological transmural inflammation' in steps[1]['findings'][1]
    assert 'acoustic interfaces' in steps[1]['tip']
    assert 'Missing or inadequate Doppler remains unassessed' in steps[2]['look']
    assert 'static figure cannot prove motion' in steps[3]['tip']
    assert any('dedicated perianal' in s for s in ref['reporting']['pitfalls'])
    assert any('Communicate suspected obstruction' in s for s in ref['reporting']['escalation'])

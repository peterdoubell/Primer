"""Wall/material coverage and real dynamic observations cannot be supplied by a parent mesh."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.ultrasound-gallbladder')
    return {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': [item['investigation_id']]}}, item


def test_complete_gallbladder_reporting_scope_preserves_layers_and_complications():
    data, item = inventory(); ref = detail(Curriculum(), resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data, {item['investigation_id']: ref['reporting']})
    assert item['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    leaves = {r['id']: r for r in requirements_for(item)}
    assert len(leaves) == 220
    for name in ('neck.outer_wall_margin', 'wall_layers.intramural_cystic_space', 'contents.intraluminal_membrane',
                 'complications.complete_fistulous_tract_if_visible', 'vascular.wall_flow_sampling_region', 'ultrasound.focal_pressure_site'):
        assert 'gallbladder.' + name in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']} == set(range(5))
    result = audit(data, {'assets': [{'id': 'parent', 'kind': 'model', 'investigation_ids': [item['investigation_id']],
                                     'structure_ids': ['gallbladder.whole', 'gallbladder.wall_layers']}]},
                   expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements'] == 660
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': 660}


def test_normal_anatomy_and_ct_do_not_supply_wall_disruption_or_ultrasound_observations():
    _, item = inventory(); leaves = {r['id']: r for r in requirements_for(item)}
    asset = {'kind': 'clinical_image', 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(asset, leaves['gallbladder.wall_layers.wall_layer_disruption'])
    assert 'source_context_purpose_mismatch' in inspect_binding(asset, leaves['gallbladder.contents.each_stone'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves['gallbladder.ultrasound.shadow_source'])
    assert {'mobility', 'compressibility', 'tenderness', 'vascularity'}.issubset({r['observation'] for r in item['functional_evidence_requirements']})


def test_unassessed_tenderness_is_not_prefilled_as_a_negative_murphy_sign():
    ref = detail(Curriculum(), resolve('ra.ultrasound-gallbladder'))['radiology_reference']
    step = ref['walkthrough']['steps'][3]
    assert 'not assessed or unreliable' in str(step['normal'])
    assert 'Sonographic Murphy sign negative' not in str(step['normal'])
    assert 'Static images cannot prove tenderness response' in step['tip']
    assert 'diameter alone does not establish hydrops' in ref['walkthrough']['steps'][1]['look']
    assert len(ref['reporting']['sources']) == 5
    assert any('histological layers' in p for p in ref['reporting']['pitfalls'])

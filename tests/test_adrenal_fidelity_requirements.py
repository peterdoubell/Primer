"""Adrenal source scope must preserve composition, modalities and clinical eligibility."""
import json
from pathlib import Path

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.adrenal-lesions')
    return {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': ['ra.adrenal-lesions']}}, item


def test_complete_adrenal_inventory_matches_reader_and_rejects_parent_only_credit():
    data, item = inventory()
    ref = detail(Curriculum(), resolve('ra.adrenal-lesions'))['radiology_reference']
    validate_reporting_snapshots(data, {'ra.adrenal-lesions': ref['reporting']})
    assert item['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    leaves = {r['id']: r for r in requirements_for(item)}
    assert len(leaves) == 224
    for name in ('right_gland.medial_limb', 'left_gland.lateral_limb', 'left_veins.enhancing_thrombus_boundary',
                 'lesion.haemorrhagic_component', 'extent.ivc_tumour_thrombus', 'mri.opposed_phase_matching_region'):
        assert 'adrenal.' + name in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']} == set(range(5))
    result = audit(data, {'assets': [{'id': 'gland', 'kind': 'model', 'investigation_ids': ['ra.adrenal-lesions'],
                                    'structure_ids': ['adrenal.right_gland', 'adrenal.left_gland']}]},
                   expected_catalog_ids={'ra.adrenal-lesions'})
    assert result['representation_requirements'] == 672
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': 672}


def test_normal_anatomy_and_ct_cannot_supply_positive_pathology_or_mri():
    _, item = inventory()
    leaves = {r['id']: r for r in requirements_for(item)}
    asset = {'kind': 'clinical_image', 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(asset, leaves['adrenal.lesion.enhancing_nodule'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves['adrenal.mri.diffuse_signal_loss'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves['adrenal.pet.liver_reference_region'])


def test_adrenal_frameworks_growth_and_biopsy_are_not_unqualified_imaging_rules():
    n = Curriculum().nodes['rad.5.adrenal']
    r = n['reference']
    assert 'Seow 2025' in r['classify']['note'] and 'distinct' in r['classify']['note']
    assert '>20% AND ≥5 mm' in r['measure'][4]['cutoff']
    assert 'additional imaging' in r['classify']['rows'][1][2]
    assert n['quiz'][6]['answer'] == '69.7' and n['quiz'][7]['answer'] == '53.1'
    assert 'does not diagnose adenoma' in n['quiz'][6]['explain']
    ref = detail(Curriculum(), resolve('ra.adrenal-lesions'))['radiology_reference']
    steps = ref['walkthrough']['steps']
    assert 'Small fat foci' in steps[1]['tip']
    assert 'AND at least 5 mm' in steps[4]['tip']
    assert 'Stable size compared' not in str(steps[4]['normal'])
    assert any('histology would change management' in p for p in ref['reporting']['pitfalls'])


def test_adrenal_morphology_and_venous_extent_do_not_select_kidneys_or_arteries():
    ref = detail(Curriculum(), resolve('ra.adrenal-lesions'))['radiology_reference']
    steps = ref['walkthrough']['steps']
    assert steps[1]['parts'] == [] and steps[4]['parts'] == []
    assert 'kidney meshes cannot represent' in steps[1]['tip']
    assert 'renal arteries cannot stand for veins' in steps[4]['tip']
    assert 'conceptual' in ref['walkthrough']['spatial_model']['instructions']

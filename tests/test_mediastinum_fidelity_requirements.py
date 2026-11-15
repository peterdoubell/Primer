import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    inv = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.ct-mediastinum')
    return {**data, 'investigations': [inv], 'scope': {'catalog_investigation_ids': ['ra.ct-mediastinum']}}, inv


def test_all_effective_mediastinal_report_fields_are_preserved():
    data, inv = inventory(); ref = detail(Curriculum(), resolve('ra.ct-mediastinum'))['radiology_reference']
    validate_reporting_snapshots(data, {'ra.ct-mediastinum': ref['reporting']})
    assert inv['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    assert {r['checklist_index'] for s in inv['structures'] for r in s['report_refs']} == set(range(5))
    assert {n for s in inv['structures'] for n in s['walkthrough_step_indices']} == set(range(5))


def test_boundaries_smaller_interfaces_and_conditional_sites_remain_required():
    _, inv = inventory(); leaves = {r['id']: r for r in requirements_for(inv)}
    assert len(leaves) == 326
    for target in ('prevascular.anterior_pericardium', 'visceral.visceral_paravertebral_plane',
                   'paravertebral.posterior_chest_wall', 'vascular_anatomy.svc_wall',
                   'vascular_anatomy.extrapericardial_hilar_vessels', 'neural_spinal.neural_foramen',
                   'cardiac_pericardial.superior_recess', 'esophageal_lymphatic.thoracic_duct',
                   'mass_composition.mural_nodule', 'nodal_disease.suspected_necrosis',
                   'developmental_variants.immature_thymus', 'post_treatment.resection_bed'):
        assert 'mediastinum.' + target in leaves
    for station in ('1r', '1l', '2r', '2l', '3a', '3p', '4r', '4l', '5', '6', '7', '8r', '8l',
                    '9r', '9l', '10r', '10l', '11r', '11l', '12r', '12l', '13r', '13l', '14r', '14l'):
        assert 'mediastinum.station_' + station + '.adjacent_anatomical_boundaries' in leaves
    assert leaves['mediastinum.neural_spinal.cord']['modality_scope'] == ['CT', 'MRI']
    assert len(inv['functional_evidence_requirements']) == 6


def test_a_parent_mediastinum_model_cannot_cover_stations_or_mass_interfaces():
    data, _ = inventory()
    result = audit(data, {'assets': [{'id': 'gross-mediastinum', 'kind': 'model', 'investigation_ids': ['ra.ct-mediastinum'],
        'structure_ids': ['mediastinum.prevascular', 'mediastinum.station_7', 'mediastinum.mass_extent']}]}, expected_catalog_ids={'ra.ct-mediastinum'})
    assert result['representation_requirements'] == 978
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': 978}
    assert not result['clinical_commercial_ready']


def test_normal_anatomy_cannot_cover_positive_mass_nodal_or_invasion_findings():
    _, inv = inventory(); leaves = {r['id']: r for r in requirements_for(inv)}
    asset = {'kind': 'clinical_image', 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    for target in ('mass_extent.whole_extent', 'nodal_disease.suspected_necrosis', 'compression_invasion.pericardium', 'vascular_lesion.thrombus'):
        assert 'source_context_purpose_mismatch' in inspect_binding(asset, leaves['mediastinum.' + target])
    issues = {i['code'] for i in inv['source_scope_issues']}
    assert 'compartment_definition_reconciliation_pending' in issues
    assert 'nodal_source_identity_and_extent_pending' in issues

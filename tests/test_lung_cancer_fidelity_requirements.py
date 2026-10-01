import json
from pathlib import Path

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    inv = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.ct-lung-cancer')
    return {**data, 'investigations': [inv], 'scope': {'catalog_investigation_ids': ['ra.ct-lung-cancer']}}, inv


def test_staging_inventory_preserves_the_effective_report_and_source_contract():
    data, inv = inventory()
    ref = detail(Curriculum(), resolve('ra.ct-lung-cancer'))['radiology_reference']
    validate_reporting_snapshots(data, {'ra.ct-lung-cancer': ref['reporting']})
    assert inv['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    assert {r['checklist_index'] for s in inv['structures'] for r in s['report_refs']} == set(range(5))
    assert {n for s in inv['structures'] for n in s['walkthrough_step_indices']} == set(range(5))


def test_named_nodal_stations_and_small_invasion_interfaces_cannot_disappear():
    _, inv = inventory()
    leaves = {r['id']: r for r in requirements_for(inv)}
    assert len(leaves) == 281
    codes = ['1r', '1l', '2r', '2l', '3a', '3p', '4r', '4l', '5', '6', '7']
    codes += [str(n) + side for n in (8, 9, 10, 11, 12, 13, 14) for side in ('r', 'l')]
    for code in codes:
        assert 'lung_cancer.station_' + code + '.adjacent_anatomical_boundaries' in leaves
    assert 'lung_cancer.station_11_right_optional.11s' in leaves
    assert 'lung_cancer.station_11_right_optional.11i' in leaves
    for target in ('apical_neural_spinal.stellate_ganglion', 'apical_neural_spinal.brachial_plexus_divisions',
                   'mediastinal_landmarks.intrapericardial_pulmonary_veins', 'invasion.adjacent_lobe',
                   'cystic.wall_nodule', 'bone_metastatic.medullary_extent', 'post_treatment.bronchial_stump'):
        assert 'lung_cancer.' + target in leaves
    assert not any('station_3b' in k or 'station_11_left_optional' in k for k in leaves)
    assert leaves['lung_cancer.other_metastatic.brain']['modality_scope'] == ['CT', 'MRI']
    assert leaves['lung_cancer.apical_neural_spinal.brachial_plexus_divisions']['modality_scope'] == ['CT', 'MRI']


def test_parent_mediastinum_model_cannot_cover_nodes_or_invasion():
    data, _ = inventory()
    report = audit(data, {'assets': [{'id': 'gross-mediastinum', 'kind': 'model',
        'investigation_ids': ['ra.ct-lung-cancer'], 'structure_ids': ['lung_cancer.suspicious_nodes']}]},
        expected_catalog_ids={'ra.ct-lung-cancer'})
    assert report['representation_requirements'] == 843
    assert report['counts'] == {'verified': 0, 'unverified': 0, 'missing': 843}
    assert not report['clinical_commercial_ready']


def test_normal_source_cannot_supply_positive_tumour_or_nodal_disease():
    _, inv = inventory()
    leaves = {r['id']: r for r in requirements_for(inv)}
    asset = {'kind': 'clinical_image', 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    for key in ('lung_cancer.primary.entire_lesion', 'lung_cancer.suspicious_nodes.individual_node_extent',
                'lung_cancer.invasion.great_vessel', 'lung_cancer.pleural_metastatic.pleural_deposits'):
        assert 'source_context_purpose_mismatch' in inspect_binding(asset, leaves[key])
    assert any(i['code'] == 'complete_staging_acquisitions_pending' for i in inv['source_scope_issues'])

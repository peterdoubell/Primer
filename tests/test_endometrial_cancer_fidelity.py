"""Actual endometrial MRI scope cannot become inferred stage or tissue coverage."""
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]
INV = 'ra.mri-endometrial-cancer'


@pytest.fixture(scope='module')
def reference():
    return detail(Curriculum(), resolve(INV))['radiology_reference']


def test_actual_assessment_preserves_same_wall_measurements_and_missing_inputs(reference):
    guide, walk = reference['reporting'], reference['walkthrough']
    assert len(guide['checklist']) == len(walk['steps']) == 9
    assert walk['preset_mode'] == 'assessment-prompts'
    assert reference['key_images'] == [] and walk['start']['module_illustrations'] is False
    assert [heading for step in walk['steps'] for heading in step['sections']] == [row['heading'] for row in guide['template_sections']]
    for step in walk['steps']:
        assert not step['parts']
        assert all('[__]' in text for text in step['normal'].values())
        assert not any(text.lower().startswith(('no ', 'normal ')) for text in step['normal'].values())
    depth = next(m for m in guide['measurements'] if m['name'] == 'Myometrial invasion')
    assert 'same actual site' in depth['method'] and 'Exactly 50%' in depth['pitfall']
    assert '≥50%' in depth['pitfall']
    assert any('multiphase' in text and 'excluding any myometrial invasion' in text for text in guide['protocol'])
    assert any('reduced confidence' in text for text in guide['protocol'])
    assert any('LVSI' in text and 'molecular' in text for text in guide['pitfalls'])
    assert 'not supplied' in walk['steps'][8]['normal']['COMPARISON AND TREATMENT CONTEXT']
    assert 'serial behaviour' in walk['steps'][8]['detail']
    assert guide['classification'] is None and guide['criteria_table'] is None


def test_licensed_whole_figures_keep_cases_phases_and_roles_separate(reference):
    rows = reference['structure_atlas']
    assert len(rows) == 36
    ids = {row['id'] for row in rows}
    assert {image for step in reference['walkthrough']['steps'] for image in step['images']} == ids
    assert all(row['license'] in {'CC BY 4.0', 'CC BY 3.0'} for row in rows)
    assert all(not row['source_context']['current_patient_findings'] for row in rows)
    assert all(not row['source_context']['native_acquisition_arrays_included'] for row in rows)
    assert all(not row['source_context']['different_figures_assumed_same_patient'] for row in rows)
    assert all(not row['source_context']['source_panels_independently_registered'] for row in rows)
    recurrence = reference['walkthrough']['steps'][8]['images']
    assert recurrence == ['open-endometrial-cancer-pmc7643338-fig2', 'open-endometrial-cancer-pmc7643338-fig3', 'open-endometrial-cancer-pmc8648287-fig5']
    assert 'open-endometrial-cancer-esr2026-fig5' in reference['walkthrough']['steps'][7]['images']
    assert 'open-endometrial-cancer-pmc11119523-fig5' in reference['walkthrough']['steps'][1]['images']
    held = json.loads((ROOT/'docs/endometrial-held-legacy-images.json').read_text())
    assert len(held['legacy_images']) == 2 and not held['clinical_approval']
    assert 'tumor-length' in held['legacy_images'][1]['src']


def test_named_fine_scope_requires_real_layers_sites_and_uncertain_extent(reference):
    data = json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(item for item in data['investigations'] if item['investigation_id'] == INV)
    validate_reporting_snapshots({**data, 'investigations': [item]}, {INV: reference['reporting']})
    assert item['source_contract_sha256'] == digest({key: reference.get(key) for key in ['reporting', 'report_templates', 'walkthrough', 'reading']})
    leaves = {row['id'] for row in requirements_for(item)}
    assert len(item['structures']) == 187 and len(leaves) == 904
    for side in ['left', 'right']:
        for suffix in ['uterine.uterine_cornu.source_resolution_unresolved_or_unacquired_extent',
                       'adnexal_layer.source_visible_ovarian_capsular_interface.thickness_or_explicitly_unresolved_layer',
                       'node_station.common_iliac.actual_covered_identity_and_extent']:
            assert 'endometrial_cancer.'+side+'.'+suffix in leaves
    for suffix in ['central_layer.source_visible_junctional_zone.source_inner_and_outer_boundaries',
                   'central_layer.subserosal_interface.thickness_or_explicitly_unresolved_layer',
                   'measure.myometrial_depth.local_outer_wall_reference',
                   'nodes.actual_renal_vessel_reference.source_endpoints_and_boundaries',
                   'spread.covered_extrapelvic_peritoneal_surface.source_resolution_unresolved_or_unacquired_extent',
                   'adjacent_layer.actual_contacted_bowel_segment.source_visible_mucosal_luminal_interface.source_resolution_and_uncertainty']:
        assert 'endometrial_cancer.'+suffix in leaves
    assert {i for group in item['structures'] for i in group['walkthrough_step_indices']} == set(range(9))
    scoped = {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': [INV]}}
    report = audit(scoped, {'assets': [{'id': 'gross-only', 'kind': 'model', 'investigation_ids': [INV],
                                      'structure_ids': ['endometrial_cancer.central.whole_uterine_body_and_orientation']}]}, expected_catalog_ids={INV})
    assert report['representation_requirements'] == 2712 and report['counts']['missing'] == 2712


def test_primary_staging_and_original_atlas_remain_independent(reference):
    assert reference['source_anatomy_references'] == detail(Curriculum(), resolve('ra.mri-cervical-cancer'))['radiology_reference']['source_anatomy_references']
    source = reference['source_anatomy_references'][0]
    assert source['atlas'] == 'hra-female-pelvis-v1.10' and source['initial_cropped'] is False
    assert 'unverified' in source['population_note'] and not source.get('patient_registration')
    manifest = json.loads((ROOT/'web/anatomy'/source['atlas']/'manifest.json').read_text())
    assert not manifest['clinical_approval'] and not manifest['every_structure_approved']
    system = reference['cancer_staging'][0]
    assert system['id'] == 'endometrium-figo2023'
    assert '2023' in system['version']
    rows = [row for table in system['tables'] for row in table['rows']]
    ivc = next(row for row in rows if row['category'] == 'IVC')
    assert 'renal vessels' in ivc['criteria']
    assert any('primary FIGO identifies these as IVC' in text for text in reference['reporting']['pitfalls'])
    evidence = json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())
    assets = [asset for asset in evidence['assets'] if asset['id'].startswith('open-endometrial-cancer-')]
    assert len(assets) == 36
    assert all(asset['anatomical_review']['status'] == 'pending' and not asset['requirement_coverage'] for asset in assets)

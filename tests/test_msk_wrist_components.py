"""Wrist parent labels cannot conceal missing clinically relevant components."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from primer import radiology_catalog
from primer.curriculum import Curriculum

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / 'data/radiology/msk-structure-requirements.json'
WRIST_IDS = ('ra.wrist-instability', 'ra.wrist-fractures')
OKORO = 'https://doi.org/10.3390/life13071426'
CEREZAL = 'https://link.springer.com/article/10.1186/s13244-026-02356-8'
COMPONENTS = {
    'wrist.scapholunate_interosseous_ligament': (
        'dorsal_component', 'volar_component', 'proximal_membranous_component'),
    'wrist.lunotriquetral_interosseous_ligament': (
        'dorsal_component', 'volar_component', 'proximal_membranous_component'),
    'wrist.triangular_fibrocartilage_complex': (
        'articular_disc', 'radial_attachment', 'ulnar_styloid_attachment',
        'foveal_attachment', 'dorsal_radioulnar_ligament',
        'volar_radioulnar_ligament', 'dorsal_capsular_attachment',
        'volar_capsular_attachment', 'ulnolunate_ligament',
        'ulnotriquetral_ligament', 'ulnocapitate_ligament',
        'ulnomeniscal_homologue', 'ecu_subsheath'),
}
CONDITION = ('Anatomical support for injury mechanisms; routine radiographs show '
             'indirect alignment/avulsion signs, not ligament or TFCC fibre continuity.')

spec = importlib.util.spec_from_file_location('wrist_fidelity', ROOT / 'tools/check_msk_fidelity.py')
fidelity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fidelity)


@pytest.fixture(scope='module')
def requirements():
    return json.loads(REQUIREMENTS.read_text())


def investigation(requirements, identifier):
    return next(row for row in requirements['investigations']
                if row['investigation_id'] == identifier)


@pytest.mark.parametrize('identifier', WRIST_IDS)
def test_each_wrist_complex_requires_its_source_supported_components(requirements, identifier):
    item = investigation(requirements, identifier)
    selected = {s['id']: s for s in item['structures'] if s['id'] in COMPONENTS}
    assert set(selected) == set(COMPONENTS)
    for parent, suffixes in COMPONENTS.items():
        parts = selected[parent]['required_parts']
        expected = [parent + '.' + suffix for suffix in suffixes]
        assert [p['id'] for p in parts] == expected
        assert len({p['id'] for p in parts}) == len(parts)
        for part in parts:
            assert part['name'].strip()
            assert set(part) == {'id', 'name', 'source_urls'}
            assert part['source_urls'] == [CEREZAL if 'triangular_fibrocartilage' in parent else OKORO]


def test_same_anatomy_uses_the_same_component_ids_in_both_wrist_paths(requirements):
    paths = []
    for identifier in WRIST_IDS:
        paths.append({s['id']: s['required_parts']
                      for s in investigation(requirements, identifier)['structures']
                      if s['id'] in COMPONENTS})
    assert paths[0] == paths[1]


@pytest.mark.parametrize('identifier', WRIST_IDS)
def test_component_targets_inherit_conditional_direct_soft_tissue_scope(requirements, identifier):
    item = investigation(requirements, identifier)
    leaves = fidelity.requirements_for(item)
    for structure in item['structures']:
        if structure['id'] not in COMPONENTS:
            continue
        assert structure['modality_scope'] == ['MRI', 'MR arthrography']
        assert structure['image_visibility'] == 'indirect_on_radiography_direct_only_with_suitable_soft_tissue_imaging'
        assert structure['condition'] == CONDITION
        assert structure['laterality'] == 'examined_side'
        assert structure['requirement_basis'] == 'anatomical_decomposition_of_report_field'
        assert structure['requires_site_instantiation'] is False
        for leaf in [p for p in leaves if p['parent_id'] == structure['id']]:
            assert leaf['condition'] == CONDITION
            assert leaf['report_refs'] == structure['report_refs']
            assert leaf['laterality'] == structure['laterality']


@pytest.mark.parametrize('identifier', WRIST_IDS)
def test_parent_only_assets_cannot_satisfy_actual_wrist_components(requirements, identifier, tmp_path):
    item = copy.deepcopy(investigation(requirements, identifier))
    item['structures'] = [s for s in item['structures'] if s['id'] in COMPONENTS]
    expected = {parent + '.' + suffix for parent, suffixes in COMPONENTS.items() for suffix in suffixes}
    assert {p['id'] for p in fidelity.requirements_for(item)} == expected
    # Only parent names are supplied. No fixture represents clinical approval.
    evidence = {'assets': [{'id': 'whole-parent-label-only', 'kind': 'model',
                           'structure_ids': list(COMPONENTS),
                           'investigation_ids': [identifier]}]}
    req = {'clinical_validation_status': requirements['clinical_validation_status'],
           'scope': {'catalog_investigation_ids': [identifier]},
           'investigations': [item]}
    result = fidelity.audit(req, evidence, tmp_path)
    assert result['representation_requirements'] == len(expected) * 3
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': len(expected) * 3}
    assert not result['clinical_commercial_ready']


def test_component_additions_do_not_create_new_patient_reporting_fields(requirements):
    curriculum = Curriculum()
    selected = []
    reporting = {}
    for identifier in WRIST_IDS:
        item = investigation(requirements, identifier)
        detail = radiology_catalog.detail(curriculum, radiology_catalog.resolve(identifier))
        assert detail['modality'] == ('Radiography' if identifier == 'ra.wrist-instability' else 'Multimodality')
        assert item['modality'] == detail['modality']
        guide = detail['radiology_reference']['reporting']
        selected.append(item)
        reporting[identifier] = guide
        for structure in item['structures']:
            if structure['id'] not in COMPONENTS:
                continue
            assert [r['checklist_index'] for r in structure['report_refs']] == [2, 3]
            assert structure['source_urls'] == [
                'https://radiologyassistant.nl/musculoskeletal/wrist/' +
                ('carpal-instability' if identifier == 'ra.wrist-instability' else 'fractures')]
    fidelity.validate_reporting_snapshots({'investigations': selected}, reporting)

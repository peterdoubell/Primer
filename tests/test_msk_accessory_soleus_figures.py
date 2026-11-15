"""Keep the two symptomatic ASM cases and their mixed panels explicit."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from primer.radiology_catalog import _structure_atlases
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, requirements_for

ROOT = Path(__file__).resolve().parents[1]


def records():
    assets = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    ankle = next(i for i in requirements['investigations'] if i['investigation_id'] == 'ra.mri-ankle')
    return {a['id']: a for a in assets}, {r['id']: r for r in requirements_for(ankle)}


@pytest.mark.parametrize('figure,age,pattern,panels', [(1,25,'muscular',list('cdef')), (3,31,'tendinous',list('bcdef'))])
def test_preserved_soleus_cases_keep_partial_extent_and_context(figure, age, pattern, panels):
    assets, requirements = records()
    identifier = f'open-ankle-accessory-soleus-plecko-fig{figure}'
    image = next(i for i in _structure_atlases()['ra.mri-ankle'] if i['id'] == identifier)
    asset = assets[identifier]
    raw = (ROOT / asset['local_path']).read_bytes()
    prior = asset['prior_repository_preview']
    assert hashlib.sha256((ROOT / 'docs/msk-accessory-soleus-source-review' / Path(prior['path']).name).read_bytes()).hexdigest() == prior['sha256']
    assert hashlib.sha256(raw).hexdigest() == asset['sha256'] == image['sha256']
    context = asset['source_context']
    assert context['population'] == {'life_stage':'adult','sex':'female','age_years':age}
    assert context['laterality'] == 'right'
    assert context['distal_insertion_pattern'] == pattern
    assert context['selected_panels'] == image['clinical_panels'] == panels
    assert asset['anatomical_review']['status'] == 'pending'
    assert asset['pixel_provenance']['higher_resolution_pixels_verified']
    assert not asset['pixel_provenance']['highest_resolution_master_verified']
    for target in asset['structure_ids']:
        assert not inspect_binding(asset, requirements[target])
        assert inspect_requirement_coverage(asset, requirements[target]) == ['requirement_coverage_partial']
    assert not any('proximal_attachment' in target for target in asset['structure_ids'])
    wrong = requirements['ankle.flexor_digitorum_accessorius_longus_muscle.muscle_belly']
    assert 'source_context_anatomical_variant_mismatch' in inspect_binding(asset, wrong)


@pytest.mark.parametrize('panel,expected', [('a','source_context_selected_panel_not_clinical_image'), ('b','source_context_selected_panel_modality_mismatch')])
def test_photograph_and_radiograph_cannot_supply_mri_coverage(panel, expected):
    assets, requirements = records()
    asset = copy.deepcopy(assets['open-ankle-accessory-soleus-plecko-fig1'])
    asset['source_context']['selected_panels'] = [panel]
    asset['representation_selection']['panels'] = [panel]
    assert expected in inspect_binding(asset, requirements['ankle.accessory_soleus_muscle.muscle_belly'])


def test_source_plane_discrepancy_and_publisher_license_evidence_are_retained():
    image = next(i for i in _structure_atlases()['ra.mri-ankle'] if i['id'] == 'open-ankle-accessory-soleus-plecko-fig3')
    assert '(f) T1-weighted axial' in image['source_caption_full']
    assert 'unresolved' in image['source_context']['sequence']
    assert 'longitudinal' in image['caption']
    review = json.loads((ROOT / 'docs/msk-accessory-soleus-source-review/acquisition-and-context.json').read_text())
    assert review['permissions']['version_explicit'] is False
    assert review['permissions']['version_resolved_from_publisher_metadata'] == image['license'] == 'CC BY 4.0'
    publisher = review['permissions']['publisher_license_record']
    assert hashlib.sha256((ROOT / publisher['path']).read_bytes()).hexdigest() == publisher['sha256']
    metadata = json.loads((ROOT / publisher['path']).read_text())['message']
    assert metadata['DOI'] == '10.1155/2020/8851920'
    assert metadata['license'][0]['URL'] == 'http://creativecommons.org/licenses/by/4.0/'
    assert image['ancillary_panels'][0]['kind'] == 'Radiography'

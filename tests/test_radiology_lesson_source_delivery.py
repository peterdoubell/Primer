"""Every available original source atlas reaches its matching lesson without changing cases."""
import copy
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer import radiology_catalog as catalog
from primer.module_media import attach_source_gallery
from tools.check_radiology_fidelity import digest
from tools.msk_runtime_rights import reference_images

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['goal', 'learning_outcomes', 'lesson', 'reference', 'radiology_reference', 'visual_spec',
          'lesson_media', 'model_family', 'model_context', 'practice', 'quiz', 'kid_text']


@pytest.fixture(scope='module')
def curriculum():
    return Curriculum()


def test_every_existing_source_reader_is_attached_once_to_its_matching_lesson(curriculum):
    atlas = catalog._structure_atlases()
    expected = {}
    for investigation in catalog.catalogue()['investigations']:
        if atlas.get(investigation['id']):
            expected.setdefault(investigation['module_id'], []).append(investigation['id'])
    actual = {}
    for node in curriculum.nodes.values():
        ids = [identifier for item in node['lesson_media'] if item['kind'] == 'source-gallery'
               for identifier in item['investigation_ids']]
        if ids:
            assert len(ids) == len(set(ids))
            actual[node['id']] = ids
            _validate_lesson_media(node)
    assert len(actual) == 49 and {k: set(v) for k, v in actual.items()} == {k: set(v) for k, v in expected.items()}
    assert set(actual['rad.5.cardiac-masses-devices']) == {
        'ra.cardiovascular-devices', 'ra.cardiac-masses', 'ra.ct-cardiovascular-pearls'}
    assert 'rad.5.bladder-virads' not in actual  # Missing native figures are not replaced with another case.


def test_authored_gallery_and_all_source_cases_survive_idempotent_attachment(curriculum):
    for identifier in ['rad.5.rectal-mr', 'rad.5.prostate-mri', 'rad.5.cardiac-masses-devices']:
        node = copy.deepcopy(curriculum.node(identifier))
        original = copy.deepcopy(node['lesson_media'])
        attach_source_gallery(node)
        assert node['lesson_media'] == original
    rectal = curriculum.node('rad.5.rectal-mr')
    galleries = [m for m in rectal['lesson_media'] if m['kind'] == 'source-gallery']
    assert len(galleries) == 1 and galleries[0]['id'] == 'rectal-original-source-gallery'


def test_every_attached_figure_keeps_its_original_role_rights_and_case_context(curriculum):
    proof = json.loads((ROOT / 'docs/radiology-lesson-source-delivery-review/review.json').read_text())
    atlas = catalog._structure_atlases()
    for module in proof['modules']:
        node = curriculum.node(module['module_id'])
        assert module['module_contract_after_sha256'] == digest({key: node.get(key) for key in FIELDS})
        for reader in module['source_readers']:
            source = atlas[reader['investigation_id']]
            assert reader['source_figures_sha256'] == digest(source)
            assert reader['figure_ids'] == [f['id'] for f in source]
            assert reader['figure_count'] == len(source)
            delivered = catalog.detail(curriculum, catalog.resolve(reader['investigation_id']))['radiology_reference']['structure_atlas']
            assert digest(delivered) == reader['source_figures_sha256']
        assert not module['clinical_or_complete_anatomical_approval']
    assert proof['newly_attached_lessons'] == 48 and not proof['whole_radiology_goal_complete']


def test_runtime_rights_audit_counts_all_new_lesson_uses(curriculum):
    catalogue = catalog.catalogue()
    inventory = reference_images(curriculum, catalogue, {}, catalog.detail, catalog_section=None)
    atlas = catalog._structure_atlases()
    by_id = {i['id']: i for i in catalogue['investigations']}
    uses = {(u['surface'], u['id']) for resource in inventory['images'] for u in resource['uses']
            if u['collection'] == 'structure_atlas'}
    for identifier, figures in atlas.items():
        for figure in figures:
            assert ('lesson:' + by_id[identifier]['module_id'], figure['id']) in uses


def test_cross_lesson_tampering_is_rejected_for_automatically_attached_sources(curriculum):
    node = copy.deepcopy(curriculum.node('rad.5.prostate-mri'))
    gallery = next(m for m in node['lesson_media'] if m['kind'] == 'source-gallery')
    gallery['investigation_ids'] = ['ra.mri-perianal-fistula']
    with pytest.raises(ValueError, match='cross-lesson'):
        _validate_lesson_media(node)

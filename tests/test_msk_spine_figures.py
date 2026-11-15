"""Spine source pixels, panel meanings and local candidate scope stay distinct."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from tools.check_msk_fidelity import (
    inspect_asset, inspect_binding, requirements_for, review_scope_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
INVESTIGATION = 'ra.thoracolumbar-fractures'
EVIDENCE = 'docs/msk-spine-image-progress.md'
PLC_DRAWING = 'open-spine-plc-schematic-bizdikian-fig1'
PLC_MRI = 'open-spine-plc-lumbar-mri-bizdikian-fig4'
FSU = 'open-spine-functional-unit-kushchayev-fig1'
LF_MRI = 'open-spine-ligamentum-flavum-kushchayev-fig26'
LF_DRAWING = LF_MRI + '-schematic-panels'
IDS = (PLC_DRAWING, PLC_MRI, FSU, LF_MRI, LF_DRAWING)
COURSES = {
    'thoracolumbar.supraspinous_ligament.intersegmental_course',
    'thoracolumbar.interspinous_ligament.intersegmental_course',
}
INTERFACES = {
    'thoracolumbar.intervertebral_disc.superior_endplate_interface',
    'thoracolumbar.intervertebral_disc.inferior_endplate_interface',
}
NATIVE = (
    (PLC_DRAWING, 'spine-plc-schematic-bizdikian-fig1.jpg', (986, 986),
     '008964ed0da0e6dac11fd2432c26f6a0c06dd9476ca16c44f3578fe082deb331'),
    (PLC_MRI, 'spine-plc-lumbar-mri-bizdikian-fig4.jpg', (986, 1856),
     '2f50c74c47f5a52aae0cc2829703cb3dd4bfc9cdb36ff00f401e9ce8298e832c'),
    (FSU, 'spine-functional-unit-kushchayev-fig1-pdf-render.png', (1309, 844),
     'cad6b73674ae97d41021c61483595bd61b068f19e2bbf69eadcd101581328f17'),
    (LF_MRI, 'spine-ligamentum-flavum-kushchayev-fig26-pdf-render.png', (1534, 583),
     '373044961659f45b5df7d02a99f91b634b1245351083cad1f889e62fef37ef5d'),
)


@pytest.fixture(scope='module')
def records():
    images = json.loads((ROOT / 'data/radiology/msk-open-images.json').read_text())
    assets = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    spine = next(i for i in requirements['investigations'] if i['investigation_id'] == INVESTIGATION)
    leaves = {part['id']: part for part in requirements_for(spine)}
    return {i['id']: i for i in images[INVESTIGATION]}, {a['id']: a for a in assets}, requirements, spine, leaves


@pytest.mark.parametrize('identifier,filename,size,fingerprint', NATIVE)
def test_spine_figures_retain_their_reviewed_artifact_bytes_and_dimensions(
        records, identifier, filename, size, fingerprint):
    images, assets, _, _, _ = records
    image, asset = images[identifier], assets[identifier]
    path = ROOT / 'web/reference-media/msk-open' / filename
    assert image['src'] == '/app/reference-media/msk-open/' + filename
    assert asset['local_path'] == str(path.relative_to(ROOT))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == fingerprint
    assert image['sha256'] == asset['sha256'] == fingerprint
    with Image.open(path) as raster:
        raster.load()
        assert raster.size == size == (image['width'], image['height'])
        assert raster.format == ('JPEG' if path.suffix == '.jpg' else 'PNG')
    assert (asset['pixel_provenance']['width'], asset['pixel_provenance']['height']) == size


@pytest.mark.parametrize('identifier,page,xobject', [(PLC_DRAWING, 2, '/Im30'), (PLC_MRI, 5, '/Im69')])
def test_bizdikian_raw_dct_streams_keep_pdf_and_conflicting_jats_licence_evidence(
        records, identifier, page, xobject):
    images, assets, _, _, _ = records
    image, asset = images[identifier], assets[identifier]
    evidence = image['source_license_evidence']
    assert asset['source_license_evidence'] == evidence
    assert evidence['pdf_sha256'] == '8b378838a139d0a31c2a84850a2d5208e9322811ede1870d6b89ecc50f0312e8'
    assert evidence['pdf_license'] == 'CC BY 4.0'
    assert 'Page 1' in evidence['pdf_license_locator']
    assert evidence['xml_sha256'] == '69695dc5015cc99de24d7365ce135c577a4b7eab513e8508e204f9003649102a'
    assert evidence['xml_license_url'] == 'https://creativecommons.org/licenses/by/3.0/'
    assert 'PDF' in evidence['resolution'] and 'JATS' in evidence['resolution']
    assert image['source_raw_dct_sha256'] == image['sha256']
    assert image['source_pdf_page'] == asset['pixel_provenance']['source_pdf_page'] == page
    assert image['source_pdf_xobject'] == asset['pixel_provenance']['source_pdf_xobject'] == xobject
    assert asset['pixel_provenance']['source_raw_dct_sha256'] == image['sha256']
    license_info = asset['source']['license']
    assert license_info['name'] == image['license'] == 'CC BY 4.0'
    assert 'CC BY 3.0' in license_info['review_basis']
    assert 'CC BY 4.0' in license_info['review_basis']


@pytest.mark.parametrize('identifier', [FSU, LF_MRI, LF_DRAWING])
def test_complete_pdf_figure_renders_keep_illustrator_credit(records, identifier):
    images, assets, _, _, _ = records
    image = images[LF_MRI if identifier == LF_DRAWING else identifier]
    asset = assets[identifier]
    assert 'Irina Nefedova' in image['attribution']
    assert 'Irina Nefedova' in asset['source']['license']['attribution']
    assert asset['source']['license']['name'] == 'CC BY 4.0'
    assert asset['pdf_render_provenance']['painted_vector_paths'] > 0
    assert 'vector labels/arrows' in image['attribution']
    assert not asset['local_path'].endswith('.jpg'), 'Raw PDF panels omit the source labels/arrows'


@pytest.mark.parametrize('identifier', [FSU, LF_MRI])
def test_pdf_figures_preserve_complete_page_render_pixels_without_resizing(records, identifier):
    images, assets, _, _, _ = records
    image, asset = images[identifier], assets[identifier]
    provenance = image['pdf_render_provenance']
    assert asset['pdf_render_provenance'] == provenance
    assert provenance['source_pdf_sha256'] == 'affa1a6dc547a274a3d220b5c2aa956aaabba086e78e966273ad7e7ee7b0fe07'
    assert provenance['artifact_type'] == 'derived_pdf_rendered_figure_region'
    assert provenance['all_source_bounds_contained']
    assert provenance['post_render_resampling'] is False
    assert provenance['painted_vector_paths'] > 0
    for embedded in provenance['embedded_images']:
        assert all(1 <= ratio < 1.001 for ratio in embedded['rendered_pixels_per_source_pixel'])
    page = ROOT / 'docs/msk-spine-pdf-review' / ('page-%02d-full-300dpi.png' % provenance['page'])
    assert hashlib.sha256(page.read_bytes()).hexdigest() == provenance['full_page_render_sha256']
    with Image.open(page) as full, Image.open(ROOT / asset['local_path']) as displayed:
        selected = full.convert('RGB').crop(provenance['crop_bbox_pixels'])
        assert selected.size == displayed.size
        assert selected.tobytes() == displayed.convert('RGB').tobytes()
        assert hashlib.sha256(selected.tobytes()).hexdigest() == provenance['decoded_crop_pixels_sha256']


def test_fig26_normal_mri_and_schematic_are_separate_claims_over_the_same_pixels(records):
    images, assets, requirements, _, _ = records
    image, clinical, schematic = images[LF_MRI], assets[LF_MRI], assets[LF_DRAWING]
    assert image['clinical_panels'] == ['b']
    assert image['schematic_panels'] == ['a']
    assert image['pathological_panels_not_credited_as_normal'] == ['c']
    assert clinical['sha256'] == schematic['sha256'] == image['sha256']
    assert clinical['local_path'] == schematic['local_path']
    for asset, kind, panel, modality in [(clinical, 'clinical_image', 'b', 'MRI'),
                                        (schematic, 'schematic', 'a', 'Schematic')]:
        assert asset['kind'] == kind and asset['modality'] == modality
        assert asset['representation_selection'] == {'kind': kind, 'panels': [panel]}
        assert asset['source_context']['selected_panels'] == [panel]
        assert asset['source_context']['panel_types'] == {'a': 'Schematic', 'b': 'MRI', 'c': 'MRI'}
        assert asset['source_context']['panel_states'] == {
            'a': 'normal_anatomical_reference', 'b': 'normal_anatomy',
            'c': 'ligamentum_flavum_hypertrophy',
        }
        assert asset['structure_ids'] == []
        assert asset['requirement_binding_evidence'] == []
    assert review_scope_fingerprint(clinical, requirements) != review_scope_fingerprint(schematic, requirements)


@pytest.mark.parametrize('identifier,other_panel,expected_issue', [
    (LF_MRI, 'a', 'source_context_selected_panel_not_clinical_image'),
    (LF_MRI, 'c', 'source_context_selected_panel_state_mismatch'),
    (LF_DRAWING, 'b', 'source_context_selected_panel_not_schematic'),
    (LF_DRAWING, 'c', 'source_context_selected_panel_not_schematic'),
])
def test_fig26_panel_swaps_invalidate_review_scope_even_when_file_hash_is_unchanged(
        records, identifier, other_panel, expected_issue):
    _, assets, requirements, _, leaves = records
    original = assets[identifier]
    changed = copy.deepcopy(original)
    changed['source_context']['selected_panels'] = [other_panel]
    changed['representation_selection']['panels'] = [other_panel]
    assert changed['sha256'] == original['sha256']
    assert review_scope_fingerprint(changed, requirements) != review_scope_fingerprint(original, requirements)
    if expected_issue:
        # Testing the representation boundary does not bind the real unlabelled
        # figure to this side-specific leaf.
        target = leaves['thoracolumbar.left_ligamentum_flavum.intersegmental_course']
        assert expected_issue in inspect_binding(changed, target)
    # A pathological MRI panel must also fail its normal-state claim,
    # independently of whether a new review fingerprint has been recorded.


def test_fig26_pathological_panel_state_cannot_be_silently_relabelled_normal(records):
    _, assets, requirements, _, _ = records
    original = assets[LF_MRI]
    changed = copy.deepcopy(original)
    changed['source_context']['panel_states']['c'] = 'normal_anatomy'
    assert review_scope_fingerprint(changed, requirements) != review_scope_fingerprint(original, requirements)


def test_spine_bindings_are_only_local_courses_and_disc_interfaces(records):
    _, assets, _, spine, leaves = records
    expected = {PLC_DRAWING: COURSES, PLC_MRI: COURSES, FSU: INTERFACES,
                LF_MRI: set(), LF_DRAWING: set()}
    by_parent = {s['id']: s for s in spine['structures']}
    for identifier in IDS:
        asset = assets[identifier]
        assert asset['investigation_ids'] == [INVESTIGATION]
        assert set(asset['structure_ids']) == expected[identifier]
        assert asset['source_context']['laterality'] == 'not_reported'
        assert asset['source_context']['extent'] == 'local'
        assert asset['source_context']['anatomical_site']['vertebral_level'] == 'not_reported'
        assert {e['structure_id'] for e in asset['requirement_binding_evidence']} == expected[identifier]
        for target in asset['structure_ids']:
            assert not inspect_binding(asset, leaves[target])
            assert by_parent[leaves[target]['parent_id']]['requires_site_instantiation']
        assert not any('ligamentum_flavum' in target or 'facet_capsule' in target
                       for target in asset['structure_ids'])
    mri_sources = {e['structure_id']: e['source_panels'] for e in assets[PLC_MRI]['requirement_binding_evidence']}
    assert mri_sources == {
        'thoracolumbar.supraspinous_ligament.intersegmental_course': ['a'],
        'thoracolumbar.interspinous_ligament.intersegmental_course': ['b'],
    }
    assert assets[PLC_MRI]['source_context']['depicted_state'] == 'unknown'


@pytest.mark.parametrize('identifier', IDS)
def test_spine_source_candidates_do_not_acquire_clinical_approval(records, identifier):
    _, assets, requirements, _, _ = records
    asset = assets[identifier]
    assert asset['anatomical_review']['status'] == 'pending'
    assert asset['visual_review']['status'] == 'source_checked'
    assert asset['fidelity'] == 'source_reviewed_not_clinically_approved'
    evidence = 'docs/msk-spine-pdf-rendering.md' if identifier in (FSU, LF_MRI, LF_DRAWING) else EVIDENCE
    assert asset['source']['license']['evidence_path'] == evidence
    assert asset['visual_review']['evidence_path'] == evidence
    assert (ROOT / evidence).is_file()
    issues = inspect_asset(asset, ROOT, review_scope_fingerprint(asset, requirements))
    assert 'asset_fingerprint_mismatch' not in issues
    assert 'commercial_rights_unverified' not in issues
    assert 'high_fidelity_unproven' in issues
    assert 'anatomical_review_missing_or_stale' in issues
    assert 'visual_review_missing_or_stale' in issues

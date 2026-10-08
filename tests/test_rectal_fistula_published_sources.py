"""Original source figures retain pixels, patient context and distinct evidence roles."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image
import pytest

from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.check_msk_fidelity import requirements_for

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/rectal-fistula-published-source-review/original-source-review.json'
IDS = ('ra.mri-rectal-cancer', 'ra.mri-perianal-fistula')
PREFIX = 'open-anorectal-'


def rows(identifier):
    return [r for r in json.loads((ROOT / 'data/radiology/radiology-open-images.json').read_text())[identifier]
            if r['id'].startswith(PREFIX)]


def figure(number):
    return next(r for r in rows(IDS[0]) if r['figure_number'] == number)


def test_all_complete_source_masters_keep_file_pixels_profile_and_binding():
    proof = json.loads(REVIEW.read_text())
    figures = [(article, f) for article in proof['articles'] for f in article['figures']]
    assert len(figures) == 26
    assert not proof['clinical_anatomical_or_full_reporting_approval_granted']
    bindings = {3: (4, 95), 4: (4, 94), 6: (7, 156), 7: (7, 155),
                10: (10, 203), 11: (10, 202)}
    all_rows = rows(IDS[0]) + rows(IDS[1])
    for article, f in figures:
        row = next(r for r in all_rows if article['pmcid'].lower() in r['id']
                   and r['figure_number'] == f['figure_number'])
        path = ROOT / 'web' / row['src'].removeprefix('/app/')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'] == f['source_master_sha256']
        with Image.open(path) as image:
            assert image.size == (f['width'], f['height']) and image.mode == f['mode']
            assert hashlib.sha256(image.tobytes()).hexdigest() == f['decoded_pixel_sha256']
            assert hashlib.sha256(image.info.get('icc_profile', b'')).hexdigest() == f['source_ICC_sha256']
        assert not f['original_source_pixels_resampled_cropped_enhanced_or_relabelled']
        assert not f['original_acquisition_matrix_or_native_geometry_verified']
        if article['pmcid'] == 'PMC9849549' and f['figure_number'] in bindings:
            assert (f['source_PDF_page'], f['source_PDF_object']) == bindings[f['figure_number']]


def test_histology_specimen_drawings_and_processed_plot_keep_separate_roles():
    assert figure(2)['ancillary_panels'][0] ['kind'] == 'Histology'
    composite = figure(8)
    assert composite['clinical_panels'] == ['a_MRI', 'b_MRI', 'c_MRI']
    assert composite['ancillary_panels'][0]['panels'] == ['middle_TME_specimen']
    assert composite['source_context']['panel_types']['middle_TME_specimen'] == 'Anatomical specimen photograph'
    assert figure(12)['ancillary_panels'][0]['kind'] == 'MRI-derived plot'
    assert len(figure(13)['source_context']['source_case_groups']) == 2
    assert len(figure(14)['source_context']['source_case_groups']) == 4
    for identifier in IDS:
        for row in rows(identifier):
            catalog._validate_source_panel_roles(row)
            assert not row['source_context']['source_native_registration_verified']
            assert not row['source_context']['source_full_fine_anatomy_approved']
            assert not row['source_context']['source_current_diagnosis_or_histology_inferred']


@pytest.mark.parametrize('change', ['unknown', 'omitted', 'duplicate', 'wrong_type', 'wrong_scheme', 'invalid_name'])
def test_descriptive_source_positions_reject_incomplete_or_conflicting_roles(change):
    row = copy.deepcopy(figure(8))
    if change == 'unknown':
        row['source_context']['panel_types']['unassigned'] = 'Schematic'
    elif change == 'omitted':
        row['schematic_panels'].pop()
    elif change == 'duplicate':
        row['schematic_panels'].append(row['schematic_panels'][0])
    elif change == 'wrong_type':
        row['source_context']['panel_types']['left_schematic'] = 'MRI'
    elif change == 'wrong_scheme':
        row['source_context']['panel_identifier_scheme'] = 'single_letter'
    else:
        row['source_context']['panel_types']['bad position!'] = 'Schematic'
    with pytest.raises(ValueError):
        catalog._validate_source_panel_roles(row)


def test_fistula_original_pairs_do_not_imply_registered_masks_or_merged_identity():
    source = {r['figure_number']: r for r in rows(IDS[1]) if 'pmc13512459' in r['id']}
    assert set(source) == {1, 2, 3, *range(21, 29)}
    assert source[1]['kind'] == 'schematic'
    assert source[27]['clinical_panels'] == ['A', 'A+']
    assert 'identity across the figures is unresolved and never merged' in source[27]['limits']
    assert 'actual MRI acquisition position is not independently verified' in source[21]['limits']
    for number, row in source.items():
        if number in (1, 21):
            continue
        panels = row['clinical_panels']
        assert all(p + '+' in panels for p in panels if '+' not in p)
        assert not row['source_context']['source_different_figures_assumed_same_patient']


def test_reporting_scope_requires_actual_interfaces_without_normal_presets_or_coverage_approval():
    inventory = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    assets = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    new_assets = [a for a in assets if a['id'].startswith(PREFIX)]
    assert len(new_assets) == 30
    for identifier, groups, obligations in [(IDS[0], 79, 1422), (IDS[1], 82, 1476)]:
        item = next(i for i in inventory['investigations'] if i['investigation_id'] == identifier)
        assert len(item['structures']) == groups and len(requirements_for(item)) * 3 == obligations
        ref = catalog.detail(Curriculum(), catalog.resolve(identifier))['radiology_reference']
        assert len(rows(identifier)) == 15
        assert all(not step['normal'] and not step['parts'] for step in ref['walkthrough']['steps'])
        assert all(step['images'] for step in ref['walkthrough']['steps'])
        assert len([i for i in ref['key_images'] if not i['id'].startswith(PREFIX)]) == 3
        assert 'Partial schematic orientation only' in ref['walkthrough']['spatial_model']['reporting_aim']
    for asset in new_assets:
        assert asset['anatomical_review']['status'] == 'pending'
        assert not asset['structure_ids'] and not asset['requirement_coverage']
        rights = asset['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']

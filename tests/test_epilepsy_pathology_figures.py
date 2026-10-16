"""Six published examples preserve full rasters, rights and bounded case meanings."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

from primer.curriculum import Curriculum
from primer.radiology_catalog import _validate_source_panel_roles, detail, resolve

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/epilepsy-pathology-figure-review-20261016'
INV = 'ra.mri-epilepsy'
PREFIX = 'open-epilepsy-'


def load(path):
    return json.loads(path.read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def figures():
    return {row['id'].removeprefix(PREFIX): row
            for row in load(ROOT / 'data/radiology/radiology-open-images.json')[INV]}


def test_full_publisher_rasters_match_encoded_and_decoded_original_identities():
    proof = load(DOC / 'original-source-review.json')
    rows = figures()
    assert len(rows) == len(proof['figures']) == 6
    assert sum(f['bytes'] for f in proof['figures']) == 3400899
    for source in proof['figures']:
        row = rows[source['id'].removeprefix(PREFIX)]
        path = ROOT / source['local_path']
        raw = path.read_bytes()
        assert sha(raw) == source['sha256'] == row['sha256']
        assert hashlib.md5(raw).hexdigest() == source['md5'] == row['source_bytes_md5']
        assert len(raw) == source['bytes']
        with Image.open(path) as image:
            image.load()
            assert image.size == (row['width'], row['height']) == (source['width'], source['height'])
            assert image.mode == source['pixel_mode']
            assert sha(image.tobytes()) == source['decoded_pixel_sha256']
            icc = image.info.get('icc_profile')
            assert (sha(icc) if icc else None) == source['ICC_sha256']
            assert image.getexif().get(274) == source['EXIF_orientation']
        assert source['original_encoded_bytes_preserved']
        assert source['source_annotations_and_all_panels_preserved']
        assert not source['crop_resample_enhancement']
        assert not source['highest_possible_original_resolution_verified']
        assert not source['submitted_TIFF_or_raw_DICOM_identity_verified']


def test_captions_authors_and_grants_match_independent_primary_source_records():
    review = load(DOC / 'source/independent-review/independent-review.json')
    candidates = {r['id']: r for r in load(DOC / 'source/candidate-map.json')['candidates']}
    rows = figures()
    for accepted in review['figures']:
        pmc, number = accepted['id'].split('-figure-')
        row = rows[pmc.lower() + '-fig' + number]
        source = review['source_documents'][pmc + '.xml']
        raw = (DOC / 'source' / (pmc + '.xml')).read_bytes()
        assert sha(raw) == source['xml_sha256']
        publisher = (DOC / 'source' / source['publisher_snapshot']).read_bytes()
        assert sha(publisher) == source['publisher_snapshot_sha256']
        assert b'creativecommons.org/licenses/by/4.0/' in publisher
        tree = ET.fromstring(raw)
        figure_id = candidates[accepted['id']]['figure_xml_id']
        figure = tree.find('.//fig[@id="' + figure_id + '"]')
        assert sha(ET.tostring(figure, encoding='utf-8')) == accepted['figure_XML_sha256']
        caption = ' '.join(''.join(figure.find('caption').itertext()).split())
        assert row['source_caption_full'] == caption
        assert not figure.findall('.//attrib') and not figure.findall('.//permissions')
        assert row['asset_source_url'] == accepted['candidate_asset']['url']
        assert row['license'] == 'CC BY 4.0'
        assert row['license_url'] == 'https://creativecommons.org/licenses/by/4.0/'
        assert 'Copyright ©' in row['attribution'] and 'byte-identically' in row['attribution']
        if pmc == 'PMC8353251':
            assert 'Daichi Sone' in row['attribution'] and '2021 Sone' in row['attribution']
        else:
            for author in ['Lucas Giansante Abud', 'Lionel Thivard', 'Thiago Giansante Abud',
                           'Guilherme Seizem Nakiri', 'Antonio Carlos dos Santos', 'Didier Dormont']:
                assert author in row['attribution']
        assert accepted['commercial_reuse']['supported']
        assert not accepted['commercial_reuse']['figure_specific_exception_or_credit_found']


def test_panel_joins_distinguish_enlargements_display_variants_and_separate_cases():
    rows = figures()
    for row in rows.values():
        _validate_source_panel_roles(row)
        context = row['source_context']
        covered = [p for d in context['source_panel_details'] for p in d['covered_panel_ids']]
        assert len(covered) == len(set(covered))
        assert set(covered) == set(row['clinical_panels']) == set(context['panel_types'])
        assert not context['different_figures_assumed_same_patient']
        assert not context['source_panels_independently_registered']
        assert not context['source_case_101006_registration']
    comparison = rows['pmc8353251-fig4']['source_context']
    assert comparison['source_case_groups'] == {
        'HS_example': ['upper_left', 'lower_left'],
        'normal_comparison': ['upper_right', 'lower_right'],
    }
    assert comparison['panel_states']['lower_left'] == 'source_HS_image_enlargement'
    assert comparison['panel_states']['lower_right'] == 'source_labelled_normal_comparison_enlargement'
    assert comparison['repeated_display_panels']['lower_left']['source'] == 'upper_left'
    fcd = rows['pmc8353251-fig3']['source_context']
    assert len(fcd['selected_panels']) == 18
    assert fcd['source_reported_histology']['finding'] == 'FCD type IIb'
    assert fcd['source_reported_histology']['image_derived'] is False
    for n in range(1, 7):
        assert fcd['display_variants'][f'C{n}']['source'] == f'B{n}'
        assert fcd['panel_states'][f'C{n}'] == 'altered_display_range_of_B_not_independent_acquisition'
    cavernoma = rows['pmc4557590-fig7']['source_context']
    assert cavernoma['panels_show_distinct_selected_lesions'] and not cavernoma['T2star_GRE_is_SWI']
    assert 'not a pre/post-contrast T1 pair' in rows['pmc4557590-fig6']['limits']
    assert 'does not supply patient laterality' in rows['pmc8353251-fig2']['limits']


def test_original_guide_and_existing_figures_are_preserved_with_four_bounded_additions():
    baseline = load(DOC / 'preservation-baseline.json')
    plan = load(DOC / 'reporting-step-patch-plan.json')
    current = load(ROOT / 'data/radiology/reporting-steps/neuroradiology.json')['investigations'][INV]
    restored = json.loads(json.dumps(current))
    for change in plan:
        index = int(change['json_pointer'].split('/')[4])
        assert current['steps'][index]['label'] == change['expected_step_label']
        assert current['steps'][index]['images'] == change['proposed_after']
        if change['expected_before'] is None:
            del restored['steps'][index]['images']
        else:
            restored['steps'][index]['images'] = change['expected_before']
    assert restored == baseline['authored_epilepsy_walkthrough']
    curriculum = Curriculum()
    ref = detail(curriculum, resolve(INV))['radiology_reference']
    for key in ['reporting', 'report_templates', 'reading']:
        assert ref.get(key) == baseline['effective_' + key]
    for key in ['key_images', 'source_native_inspectors', 'source_anatomy_references', 'spatial_model']:
        assert ref.get(key) == baseline[key]
    assert {r['id'] for r in ref['structure_atlas']} == {r['id'] for r in figures().values()}
    for change in plan:
        index = int(change['json_pointer'].split('/')[4])
        assert ref['walkthrough']['steps'][index]['images'] == change['proposed_after']
    media = curriculum.node('rad.5.epilepsy-mri')['lesson_media']
    galleries = [m for m in media if m['kind'] == 'source-gallery']
    assert len(galleries) == 1 and galleries[0]['investigation_ids'] == [INV]
    assert [m for m in media if m['kind'] != 'source-gallery'] == baseline['lesson_media']
    dementia = detail(curriculum, resolve('ra.mri-dementia'))['radiology_reference']
    assert not any(r['id'].startswith(PREFIX) for r in dementia['structure_atlas'])


def test_new_rights_evidence_does_not_grant_anatomical_or_clinical_coverage():
    records = [a for a in load(ROOT / 'data/radiology/radiology-asset-evidence.json')['assets']
               if a['id'].startswith(PREFIX)]
    assert len(records) == 6
    rows = {r['id']: r for r in figures().values()}
    for asset in records:
        assert asset['investigation_ids'] == [INV]
        assert not asset['structure_ids'] and not asset['requirement_coverage']
        assert asset['anatomical_review']['status'] == 'pending'
        assert asset['source_context'] == rows[asset['id']]['source_context']
        rights = asset['source']['license']
        assert rights['commercial_use'] and rights['redistribution'] and rights['review_status'] == 'verified'
        assert sha((ROOT / rights['evidence_path']).read_bytes()) == rights['evidence_sha256']
        assert not asset['pixel_provenance']['source_pixels_changed']
        assert not asset['pixel_provenance']['highest_resolution_acquired_master_verified']
    proof = load(DOC / 'original-source-review.json')
    assert not proof['clinical_approval'] and not proof['complete_reporting_anatomy_approved'] and not proof['model_promoted']


def test_hosted_static_inventory_names_original_files_with_exact_headers():
    inventory = load(ROOT / 'data/radiology/radiology-static-rasters.json')['files']
    for row in figures().values():
        source = (ROOT / 'web' / row['src'].removeprefix('/app/')).read_bytes()
        assert inventory[row['src']] == {
            'md5': hashlib.md5(source).hexdigest(), 'sha256': sha(source),
            'width': row['width'], 'height': row['height'], 'bytes': len(source),
            'header_hex': source[:24].hex(),
        }

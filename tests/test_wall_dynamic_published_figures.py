"""Dynamic MRI snapshots preserve time, grouped anatomy and separate publication rights."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/wall-dynamic-published-source-review'


def source_rows():
    ref = detail(Curriculum(), resolve('ra.abdominal-wall-hernias'))['radiology_reference']
    return ref, [r for r in ref['structure_atlas'] if r['id'].startswith('open-wall-dynamic-')]


def test_original_figures_preserve_pdf_rgb_samples_and_embedded_icc():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    package = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert proof['articles'][0]['license'] == 'CC BY 4.0'
    assert len(proof['figures']) == len(package['figures']) == 2
    assert [(r['figure_number'], r['pdf_page'], r['pdf_object_id']) for r in proof['figures']] == [(2, 4, 129), (3, 5, 157)]
    for row in package['figures']:
        original = next(r for r in proof['figures'] if r['figure_number'] == row['figure_number'])
        path = ROOT / row['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == original['sha256'] == row['sha256']
        with Image.open(path) as im:
            assert im.mode == 'RGB' and im.size == (original['width'], original['height'])
            assert hashlib.sha256(im.tobytes()).hexdigest() == original['decoded_pixel_sha256']
            assert hashlib.sha256(im.info['icc_profile']).hexdigest() == original['source_icc_profile_sha256']
        assert original['source_icc_missing_alternate_rgb_signature_verified']
        assert original['source_icc_profile_bytes'] == 3144
        assert original['acquisition'] == 'lossless_png_original_pdf_dct_rgb_samples_and_icc_preserved'
        assert not original['source_pixels_changed']


def test_time_and_grouped_lateral_anatomy_do_not_become_spatial_wall_models():
    ref, rows = source_rows()
    assert len(rows) == 2 and {r['modality'] for r in rows} == {'MRI'}
    for row in rows:
        c = row['source_context']
        assert c['third_stack_axis'] == 'time_not_spatial_depth'
        assert not c['spatial_3d_model_derived'] and not c['full_cine_or_raw_masks_included']
        assert not c['lateral_groups_split_into_individual_wall_layers']
        assert not c['source_annotation_is_independent_anatomical_approval']
        assert not c['source_dataset_commercial_or_redistribution_permission_granted']
        assert not c['calibrated_defect_or_mesh_geometry_granted']
    workflow = next(r for r in rows if r['figure_number'] == 2)
    assert workflow['clinical_panels'] == ['A', 'B', 'D']
    assert workflow['source_context']['workflow_only_panels'] == ['C', 'E']
    paired = next(r for r in rows if r['figure_number'] == 3)
    assert paired['source_context']['source_case_rows'] == {'A': 'breathing', 'B': 'coughing', 'C': 'Valsalva'}
    assert paired['source_context']['source_operative_stages'] == {'a': 'preoperative', 'b': 'postoperative'}
    assert paired['source_context']['source_snapshot_count'] == 18
    assert not paired['source_context']['individual_postoperative_intervals_verified']
    assert not paired['source_context']['surgical_success_or_causal_motion_change_verified']
    step = next(s for s in ref['walkthrough']['steps'] if s['label'] == 'Abdominal wall muscles and mesh')
    assert {r['id'] for r in rows}.issubset(step['images'])


def test_article_rights_do_not_grant_anatomy_coverage_or_raw_dataset_rights():
    assets = [r for r in json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets']
              if r['id'].startswith('open-wall-dynamic-')]
    assert len(assets) == 2
    holds = json.loads((REVIEW / 'raw-dataset-rights-holds.json').read_text())
    assert not holds['restricted_raw_data_downloaded_or_promoted']
    assert {r['persistent_id'] for r in holds['sources']} == {'doi:10.57745/CTM9BO', 'doi:10.57745/KTM2OA'}
    assert all(not r['commercial_or_redistribution_grant'] and 'commercial' in r['restrictions'] for r in holds['sources'])
    assert all(f['restricted'] for r in holds['sources'] for f in r['files'] if f['filename'].endswith('.zip'))
    for row in assets:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {}
        assert row['anatomical_review']['status'] == 'pending'
        rights = row['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']

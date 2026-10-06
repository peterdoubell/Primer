"""Original device projections retain source limits and exclude permission-only in-pixel material."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/cardiovascular-device-published-source-review';PREFIX='open-cardiovascular-device-pmc6837806-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_source_pixels_and_permission_exclusions_are_preserved():
    proof=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());source=next(s for s in proof['sources'] if s['pmcid']=='PMC6837806')
    assert source['original_license']=='CC BY 4.0' and source['original_license_url']=='https://creativecommons.org/licenses/by/4.0/'
    assert {r['figure_number'] for r in proof['in_pixel_permission_material_not_reused']}=={13,21}
    assert all(r['not_reused'] and 'JPEG footer' in r['reason'] and '10.1067/j.cpradiol.2018.05.006' in r['reason'] for r in proof['in_pixel_permission_material_not_reused'])
    assert len(source['figures'])==len(package['figures'])==20
    for s,row in zip(source['figures'],package['figures']):
        path=ROOT/row['local_path'];assert sha(path.read_bytes())==row['sha256']==s['sha256']
        with Image.open(path) as im:assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    for n in [13,21]:assert not (ROOT/f'web/reference-media/radiology-open/cardiovascular-device-pmc6837806-fig{n}.jpg').exists()
    assert {r['id'] for r in package['replaced_unverified_remote_figures']}=={'ra-cardiovascular-devices-source-1','ra-cardiovascular-devices-source-2'}
    assert not package['model_promoted'] and not package['structure_coverage_granted']
def test_actual_reader_replaces_remote_figures_and_retains_device_function_limits():
    ref=detail(Curriculum(),resolve('ra.cardiovascular-devices'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert set(rows)==set(range(1,23))-{13,21} and not ref['key_images']
    assert rows[1]['clinical_panels']==['whole'] and 'does not identify/clear the complete' in rows[1]['limits']
    assert 'not a universal device placement' in rows[6]['limits'] and 'no instruction to apply a magnet' in rows[7]['limits'].lower()
    assert 'not an assumed intracavitary LV lead' in rows[11]['limits']
    assert rows[22]['clinical_panels']==['a','b'] and rows[22]['source_context']['source_projection_subtypes']=={'a':'Catheter angiography','b':'Chest radiography'}
    assert 'not a recommended deployment route' in rows[22]['limits']
    for row in rows.values():
        for k in ['full_acquired_series_included','independent_calibrated_measurements_verified','same_examination_registration_verified','cross_figure_patient_identity_verified',
            'current_complete_device_system_or_mri_conditions_verified','electrical_or_haemodynamic_function_verified','complete_device_and_tissue_geometry_verified','radiographic_projections_are_actual_3d_geometry']:assert row['source_context'][k] is False
    assert ref['walkthrough']['start']['images']==[PREFIX+'1',PREFIX+'11'] and ref['walkthrough']['start']['module_illustrations'] is False
    assert PREFIX+'22' in ref['walkthrough']['steps'][3]['images'] and PREFIX+'9' in ref['walkthrough']['steps'][1]['images']
    assert not any(i in ['ra-cardiovascular-devices-source-1','ra-cardiovascular-devices-source-2'] for s in ref['walkthrough']['steps'] for i in s['images'])
def test_rights_review_does_not_inherit_third_party_or_clinical_approval():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[a for a in assets if a['id'].startswith(PREFIX)]
    assert len(rows)==20
    for row in rows:
        licence=row['source']['license'];assert licence['name']=='CC BY 4.0' and licence['commercial_use'] and licence['redistribution']
        assert sha((ROOT/licence['evidence_path']).read_bytes())==licence['evidence_sha256']
        assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'
    p=json.loads((OUT/'original-source-review.json').read_text());assert p['noncommercial_other_article_images_not_reused']=='PMC4286824'
    assert 'classification only' in next(s for s in p['sources'] if s['pmcid']=='PMC8661294')['correction_scope']

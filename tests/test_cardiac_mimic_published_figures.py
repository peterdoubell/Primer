"""Cardiac source stills retain actual modality roles and unresolved native/clinical evidence."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/cardiac-mimic-published-source-review';PREFIX='open-cardiac-mimic-pmc10818366-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_source_samples_and_actual_grant_are_preserved():
    p=json.loads((OUT/'original-source-review.json').read_text());pack=json.loads((OUT/'packaged-source-images.json').read_text());assert p['original_license']=='CC BY 4.0' and p['source_main_figure_count']==38
    assert len(p['figures'])==len(pack['figures'])==38 and pack['remaining_source_figures_not_packaged']==[]
    for s,r in zip(p['figures'],pack['figures']):
        path=ROOT/r['local_path'];assert sha(path.read_bytes())==s['sha256']==r['sha256']
        with Image.open(path) as im:assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert len(pack['replaced_unverified_investigation_images'])==3
    assert p['printed_quantitative_metric_conflict_figures']==[17]
    assert not pack['structure_coverage_granted'] and not pack['model_promoted']
def test_actual_modality_static_render_and_unknown_panel_roles_are_explicit():
    ref=detail(Curriculum(),resolve('ra.cardiac-masses'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};assert set(rows)==set(range(1,39))
    assert rows[1]['modality']=='Ultrasound' and rows[2]['source_context']['source_cine_labelled_static_panels']==['a']
    assert rows[4]['clinical_panels']==list('abc') and 'raw mapping acquisitions' in rows[4]['limits']
    assert rows[6]['clinical_panels']==list('ab') and rows[6]['source_context']['source_ct_volume_rendering_panels']==['c']
    assert rows[6]['ancillary_panels'][0]['kind']=='PET-CT' and rows[6]['ancillary_panels'][0]['panels']==['d']
    assert 'not automatic malignancy' in rows[6]['limits']
    assert rows[7]['ancillary_panels'][0]['kind']=='Ultrasound' and rows[7]['clinical_panels']==['b']
    assert rows[9]['clinical_panels']==list('cd') and rows[9]['source_context']['source_3d_echo_rendering_panels']==['b'] and rows[9]['ancillary_panels'][0]['panels']==['a']
    assert rows[12]['clinical_panels']==['a'] and rows[12]['source_context']['panel_types']['b']=='Not specified' and rows[12]['source_context']['unresolved_modality_panels']==['b']
    assert not ref['key_images']
    assert rows[17]['source_context']['source_printed_quantitative_metric_conflict_panels']==['f'] and 'local to the source site' in rows[17]['limits']
    assert rows[20]['clinical_panels']==list('cd') and rows[20]['source_context']['source_3d_echo_rendering_panels']==['b']
    assert rows[21]['clinical_panels']==['a'] and rows[21]['source_context']['source_ct_volume_rendering_panels']==['b']
    assert rows[24]['clinical_panels']==['b'] and {a['kind'] for a in rows[24]['ancillary_panels']}=={'Ultrasound','MRI'}
    assert rows[32]['clinical_panels']==list('ef') and {a['kind'] for a in rows[32]['ancillary_panels']}=={'Ultrasound','CT'}
    assert rows[34]['ancillary_panels'][0]['kind']=='PET-CT'
    assert 'specific diagnosis' in rows[27]['limits']
    assert rows[14]['source_context']['source_ct_volume_rendering_panels']==list('cd') and rows[14]['clinical_panels']==list('ab')
    for r in rows.values():
        for k in ['full_acquired_series_included','native_temporal_motion_acquired','independent_quantitative_map_or_suv_verified','same_series_registration_verified','cross_figure_patient_identity_verified','full_lesion_attachment_geometry_verified','independent_clinical_or_histological_diagnosis_verified','flat_renderings_are_actual_3d_geometry']:assert r['source_context'][k] is False
    assert ref['walkthrough']['start']['images']==[PREFIX+'2',PREFIX+'7',PREFIX+'20'] and ref['walkthrough']['start']['module_illustrations'] is False
    assert PREFIX+'6' in ref['walkthrough']['steps'][2]['images'] and PREFIX+'9' in ref['walkthrough']['steps'][4]['images']
def test_rights_do_not_borrow_native_geometry_diagnosis_or_noncommercial_material():
    a=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in a if r['id'].startswith(PREFIX)];assert len(rows)==38
    for r in rows:
        l=r['source']['license'];assert l['name']=='CC BY 4.0' and l['commercial_use'] and l['redistribution']
        assert sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256'] and not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
    assert json.loads((OUT/'original-source-review.json').read_text())['noncommercial_other_article_images_not_reused']=='PMC9558634'

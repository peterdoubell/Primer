"""Source gated examples, separate patients and caption defects cannot become routine-CT grade guarantees."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/incidental-cardiac-CT-published-source-review';PREFIX='open-incidental-cardiac-ct-pmc6365314-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_every_original_figure_and_grant_is_preserved_byte_and_pixel_identically():
    proof=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());assert proof['original_license']=='CC BY 4.0' and len(proof['figures'])==len(package['figures'])==21;original={r['figure_number']:r for r in proof['figures']};assert set(original)==set(range(1,22))
    for row in package['figures']:
        s=original[int(row['id'].removeprefix(PREFIX))];p=ROOT/row['local_path'];assert sha(p.read_bytes())==s['sha256']==row['sha256']
        with Image.open(p) as im:assert (im.width,im.height,im.mode)==(s['width'],s['height'],s['pixel_mode']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed'] and s['complete_in_pixel_material_inspected']
    assert not package['module_lesson_or_other_investigation_media_changed'] and not package['structure_coverage_granted']
def test_gating_patients_views_and_source_caption_ambiguity_are_retained():
    ref=detail(Curriculum(),resolve('ra.ct-cardiovascular-pearls'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};assert len(rows)==21 and not ref['key_images']
    for n in [2,5,6]:assert rows[n]['source_context']['source_gating']=='ECG_gated_explicit' and rows[n]['source_context']['source_dedicated_study_cannot_be_generalised_as_routine_nongated']
    assert all(rows[n]['source_context']['source_gating']=='not_explicitly_reported' for n in set(rows)-{2,5,6})
    assert len(set(rows[8]['source_context']['source_panel_patient_groups'].values()))==3
    assert rows[8]['source_context']['source_panel_contrast']=={'a':'enhanced_phase_not_named','b':'not_explicitly_reported','c':'not_explicitly_reported'}
    assert rows[12]['clinical_panels']==['a','b'] and rows[12]['source_context']['source_Fig12_duplicate_caption_b_mapping_ambiguous'] and 'without inventing a third panel' in rows[12]['limits']
    assert rows[18]['source_context']['source_panel_patient_groups']['a']!=rows[18]['source_context']['source_panel_patient_groups']['b']
    assert rows[21]['clinical_panels']==['whole'] and 'actual histology record' in rows[21]['limits']
    assert 'printed 3.8 cm' in rows[1]['limits'] and 'dynamic obstruction' in rows[11]['limits'] and 'clinically establish constrictive physiology' in rows[15]['limits']
    assert PREFIX+'15' in ref['walkthrough']['steps'][4]['images'] and PREFIX+'6' in ref['walkthrough']['steps'][2]['images']
    for row in rows.values():
        for key in ['full_native_series_calibration_and_phase_verified','independent_wall_thickness_or_function_verified','same_patient_or_phase_registration_verified','clinical_pressure_shunt_or_obstruction_verified','source_histology_or_aetiology_independently_verified','complete_tissue_branch_or_pathology_geometry_verified','MIP_or_still_is_actual_3D_geometry']:assert row['source_context'][key] is False

def test_rights_and_pixels_do_not_approve_leaf_geometry_or_clinical_function():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)];assert len(rows)==21
    for row in rows:
        lic=row['source']['license'];assert lic['name']=='CC BY 4.0' and lic['commercial_use'] and lic['redistribution'] and sha((ROOT/lic['evidence_path']).read_bytes())==lic['evidence_sha256']
        assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'

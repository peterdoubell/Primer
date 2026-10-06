"""Actual CT panel letters/phases and original pixels do not approve stenosis or physiological diagnoses."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/chest-calcification-published-source-review';PREFIX='open-chest-calcium-pmc7774698-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_figures_and_actual_source_grant_are_preserved():
    p=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());assert p['original_license']=='CC BY 4.0' and len(package['figures'])==5;original={r['figure_number']:r for r in p['figures']}
    assert set(original)=={3,4,5,6,7} and {r['figure_number'] for r in p['not_selected_figures']}=={1,2}
    for r in package['figures']:
        source=original[int(r['id'].removeprefix(PREFIX))];path=ROOT/r['local_path'];assert sha(path.read_bytes())==source['sha256']==r['sha256']
        with Image.open(path) as im:assert (im.width,im.height,im.mode)==(source['width'],source['height'],source['pixel_mode']) and sha(im.tobytes())==source['decoded_pixel_sha256']
        assert source['publisher_md5_verified'] and source['complete_in_pixel_material_inspected'] and not source['source_pixels_changed']
    assert not package['module_lesson_or_other_investigation_media_changed'] and not package['structure_coverage_granted']
def test_actual_case_letters_contrast_and_site_roles_remain_separate():
    ref=detail(Curriculum(),resolve('ra.ct-cardiovascular-pearls'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};assert len(rows)==5 and not ref['key_images']
    assert rows[3]['clinical_panels']==list('abcdefgh') and rows[4]['clinical_panels']==list('abcdefghijkl')
    for n in [3,4,6]:
        phase=rows[n]['source_context']['panel_contrast_phase'];assert all(phase[l]=='unenhanced' for l in 'abcd') and all(phase[l]=='enhanced_phase_not_named' for l in rows[n]['clinical_panels'] if l not in 'abcd')
        assert rows[n]['source_context']['caption_uppercase_to_actual_lowercase_map']['A']=='a'
    assert rows[5]['source_context']['panel_contrast_phase']=={'a':'enhanced_phase_not_named','b':'unenhanced'} and 'different sources/phases' in rows[5]['limits']
    assert 'pericardial calcium alone' in rows[7]['limits'] and 'not independently calculated Agatston data' in rows[3]['limits']
    assert ref['walkthrough']['start']['module_illustrations'] is False and PREFIX+'7' in ref['walkthrough']['steps'][4]['images'] and all(not s['normal'] for s in ref['walkthrough']['steps'])
    for row in rows.values():
        for k in ['source_visual_grades_are_independently_derived','full_native_CT_series_or_voxel_calibration_verified','same_patient_or_phase_registration_verified','clinical_aetiology_or_function_independently_verified','complete_coronary_valve_or_pericardial_geometry_verified','projection_or_still_is_actual_3D_geometry']:assert row['source_context'][k] is False
def test_new_rights_clearance_does_not_fill_clinical_structure_bindings():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)];assert len(rows)==5
    for row in rows:
        lic=row['source']['license'];assert lic['name']=='CC BY 4.0' and lic['commercial_use'] and lic['redistribution'] and sha((ROOT/lic['evidence_path']).read_bytes())==lic['evidence_sha256']
        assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'

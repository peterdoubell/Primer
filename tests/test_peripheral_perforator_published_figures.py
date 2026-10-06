"""Source artefacts, annotation roles, patients and operative context cannot supply new geometry."""
import json,hashlib
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/peripheral-perforator-published-source-review';PREFIX='open-peripheral-perforator-pmc9964888-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_selected_original_pixels_and_grants_are_preserved_without_noncommercial_foot_reuse():
    proof=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());assert proof['original_license']=='CC BY 4.0' and len(package['figures'])==6
    source={r['figure_number']:r for r in proof['figures']};assert set(source)=={1,2,3,4,6,8}
    for row in package['figures']:
        s=source[int(row['id'].removeprefix(PREFIX))];path=ROOT/row['local_path'];assert sha(path.read_bytes())==row['sha256']==s['sha256']
        with Image.open(path) as im:assert (im.width,im.height,im.mode)==(s['width'],s['height'],s['pixel_mode']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert proof['noncommercial_pedal_source_not_reused']['original_license']=='CC BY-NC 4.0' and not proof['noncommercial_pedal_source_not_reused']['reused']
    assert {r['figure_number'] for r in proof['not_selected_figures']}=={5,7}
def test_actual_source_roles_patients_and_missing_motion_are_explicit():
    ref=detail(Curriculum(),resolve('ra.mra-peripheral-vessels'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};assert len(rows)==6
    assert 'motion artefact is not displayed' in rows[1]['limits']
    assert rows[2]['source_context']['source_caption_calls_schematic_but_pixels_are_MRI_quality_examples'] and not rows[2].get('contains_schematic_panels')
    assert rows[3]['source_context']['source_FA_abbreviation']=='fibular_artery' and 'not femoral artery' in rows[3]['limits']
    groups=rows[4]['source_context']['source_panel_patient_groups'];assert groups['a']!=groups['b'] and 'two different patients' in rows[4]['limits']
    groups=rows[8]['source_context']['source_panel_patient_groups'];assert groups['a']==groups['b'] and groups['c']==groups['d'] and groups['a']!=groups['c']
    assert 'not independent measured flow' in rows[6]['limits'] and rows[6]['source_context']['laterality']=='left'
    assert PREFIX+'8' in ref['walkthrough']['steps'][3]['images'] and PREFIX+'1' in ref['walkthrough']['steps'][4]['images']
    for row in rows.values():
        for key in ['full_native_volume_or_series_included','independent_calibrated_measurements_verified','same_examination_or_cross_patient_registration_verified','complete_vessel_wall_perforator_or_tissue_geometry_verified','flow_perfusion_dominance_or_viability_verified','operative_suitability_independently_verified','projection_or_annotation_is_actual_3D_geometry']:assert row['source_context'][key] is False
def test_rights_clearance_is_not_full_structure_or_clinical_approval():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)];assert len(rows)==6
    for row in rows:
        l=row['source']['license'];assert l['name']=='CC BY 4.0' and l['commercial_use'] and l['redistribution'] and sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256']
        assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'

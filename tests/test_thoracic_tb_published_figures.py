"""Original TB source examples cannot be recast as adult/uniform modality/laboratory or full3D proof."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/thoracic-tb-published-source-review';PREFIX='open-thoracic-tb-pmc11449295-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_complete_original_files_pixels_and_original_article_grant():
    p=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());original={r['figure_number']:r for r in p['figures']}
    assert set(original)=={1,2,3,4,5,6,7,9,10,11,12,13,16} and p['original_license']=='CC BY 4.0'
    for row in package['figures']:
        o=original[int(row['id'].removeprefix(PREFIX))];path=ROOT/row['local_path'];assert sha(path.read_bytes())==row['sha256']==o['sha256']
        with Image.open(path) as im:assert (im.width,im.height,im.mode)==(o['width'],o['height'],o['pixel_mode']) and sha(im.tobytes())==o['decoded_pixel_sha256']
    assert {r['figure_number'] for r in p['held_figures']}=={8,14,15} and not p['structure_coverage_granted']
def test_actual_patient_modality_phase_and_timeline_boundaries_survive_reader():
    ref=detail(Curriculum(),resolve('ra.tuberculosis'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};assert len(rows)==13
    assert rows[1]['modality']=='Radiography' and rows[1]['clinical_panels']==['A'] and rows[1]['source_context']['panel_types']['B']=='MRI'
    assert rows[1]['source_context']['population']['life_stage']=='immature'
    assert rows[2]['source_context']['source_time_groups']['two_year_follow_up']==['B'] and rows[2]['source_context']['source_time_groups']['five_year_follow_up']==['C']
    assert rows[9]['source_context']['source_time_groups']['seven_day_CXR']==['B'] and rows[9]['source_context']['source_time_groups']['five_day_CT']==['E','F']
    assert len(rows[10]['source_context']['source_patient_groups'])==3 and rows[10]['modality']=='Ultrasound'
    assert rows[13]['source_context']['source_CT_phase_roles']=={'A':'unenhanced','B':'unenhanced','C':'enhanced','D':'enhanced'}
    assert rows[16]['clinical_panels']==['B'] and rows[16]['source_context']['projection_subtype']=={'A':'right_MLO_mammography','C':'right_MLO_mammography'}
    assert not rows[16]['source_context']['source_biopsy_AFB_result_is_image_derived'] and not ref['key_images']
    assert all(not s['normal'] for s in ref['walkthrough']['steps'])
def test_integrity_and_licence_clearance_do_not_grant_anatomy_or_microbiology():
    assets=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)];assert len(assets)==13
    for a in assets:
        l=a['source']['license'];assert sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256'] and l['commercial_use']
        assert not a['structure_ids'] and not a['requirement_coverage'] and a['anatomical_review']['status']=='pending'
        assert not a['source_context']['genotype_viability_infectivity_or_resistance_verified']
        assert not a['source_context']['full_native_anatomical_or_3D_extent_verified']

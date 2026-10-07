"""Fixed specimen/phase-contrast anatomy cannot silently become diagnostic in-vivo CT or a matching ROI."""
import copy,hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import inspect_binding
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/hipct-lung-publication-source-review';PREFIX='open-hipct-lung-pmc9163096-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_complete_original_publication_pixels_and_article_grant_preserved():
    p=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());original={r['figure_number']:r for r in p['figures']}
    assert set(original)=={1,3} and p['original_license']=='CC BY 4.0'
    for row in package['figures']:
        o=original[int(row['id'].removeprefix(PREFIX))];path=ROOT/row['local_path'];assert sha(path.read_bytes())==row['sha256']==o['source_file_sha256']
        with Image.open(path) as im:assert (im.width,im.height,im.mode)==(o['width'],o['height'],o['pixel_mode']) and sha(im.tobytes())==o['decoded_pixel_sha256']
    assert not p['original_raw_dataset_rights_independently_approved_by_this_figure_review'] and not p['clinical_approval'] and not p['structure_coverage_granted']
def test_specimen_setup_and_CT_roles_and_ROIs_remain_distinct():
    ref=detail(Curriculum(),resolve('ra.hrct-lung'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert rows[1]['clinical_panels']==['d'] and rows[1]['source_schematic_panels']==['c']
    assert rows[1]['ancillary_panels'][0]['kind']=='Anatomical specimen photograph' and rows[1]['ancillary_panels'][0]['panels']==['a','b']
    assert rows[3]['clinical_panels']==list('abcdef') and rows[3]['source_context']['source_nodule_panel_VOIs']==['6.5um_VOI5','2.5um_VOI2b']
    assert not rows[3]['source_context']['source_nodule_is_acquired_VOI03_or_VOI03b_block']
    for r in rows.values():
        c=r['source_context'];assert c['setting']=='cadaveric' and c['laterality']=='left' and c['source_donor']['age_years']==94
        assert not c['healthy_in_vivo_reference'] and not c['clinical_HU_calibration_verified'] and not c['flat_volume_rendering_is_interactive_3D_model']
def test_publication_grant_and_source_sampling_cannot_approve_clinical_bindings():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)];assert len(rows)==2
    for r in rows:
        l=r['source']['license'];assert l['name']=='CC BY 4.0' and sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256']
        assert not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
        assert 'source_context_setting_mismatch' in inspect_binding(r,{'modality_scope':['CT'],'context_requirements':{'setting':'in_vivo'}})
    r=copy.deepcopy(next(r for r in rows if r['id']==PREFIX+'1'));r['source_context']['selected_panels']=['a']
    assert 'source_context_selected_panel_not_clinical_image' in inspect_binding(r,{'modality_scope':['CT']})

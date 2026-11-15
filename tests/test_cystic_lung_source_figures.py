"""Original panel identities and source bytes do not grant native anatomy or clinical conclusions."""
import json,hashlib
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for
from tools.anatomy_sources.expand_cystic_lung_requirements import build
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/cystic-lung-published-source-review';PREFIX='open-cystic-lung-pmc13200743-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_files_and_decoded_pixels_are_preserved_with_actual_grant():
    p=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());source={r['figure_number']:r for r in p['figures']}
    assert set(source)==set(range(1,12)) and p['original_license']=='CC BY 4.0'
    for row in package['figures']:
        original=source[int(row['id'].removeprefix(PREFIX))];path=ROOT/row['local_path'];assert sha(path.read_bytes())==row['sha256']==original['sha256']
        with Image.open(path) as im:assert (im.width,im.height,im.mode)==(original['width'],original['height'],original['pixel_mode']) and sha(im.tobytes())==original['decoded_pixel_sha256']
    assert not p['clinical_approval'] and not p['structure_coverage_granted'] and not p['model_promoted']
def test_actual_panels_patient_groups_and_source_chronology_are_distinct():
    ref=detail(Curriculum(),resolve('ra.hrct-cystic-lung'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert len(rows)==11 and all(r['modality']=='CT' for r in rows.values())
    assert len(rows[1]['source_context']['source_patient_groups'])==4 and rows[1]['source_context']['caption_E_3D_vs_actual_axial_presentation_mismatch']
    assert rows[2]['clinical_panels']==list('ABCDEFGHI') and rows[4]['clinical_panels']==list('ABCDEFGHI')
    assert rows[5]['clinical_panels']==list('ABCDEFHIK') and 'J' not in rows[5]['clinical_panels']
    assert rows[3]['source_context']['source_time_groups']['eight_month_follow_up']==['C']
    assert rows[8]['source_context']['source_time_groups']['January_2018']==['C','D']
    assert rows[9]['source_context']['cross_panel_same_patient_identity_verified'] is False
    assert 'low PET uptake' in rows[11]['limits'] and ref['key_images']
def test_rights_clearance_cannot_supply_full_anatomical_requirement_bindings():
    assets=[a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id'].startswith(PREFIX)]
    assert len(assets)==11
    for a in assets:
        l=a['source']['license'];assert l['name']=='CC BY 4.0' and l['commercial_use'] and sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256']
        assert not a['structure_ids'] and not a['requirement_coverage'] and a['anatomical_review']['status']=='pending'
def test_full_structure_scope_requires_actual_sites_and_current_contract():
    item=build();stored=next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']=='ra.hrct-lung')
    assert item['structures']==[s for s in stored['structures'] if s['id'].startswith('cystic_lung.')]
    assert len(item['structures'])==75 and len(requirements_for(item))==565
    assert all(s['requires_site_instantiation'] and s['report_refs'] for s in item['structures'])
    ids={s['id'] for s in item['structures']}
    for key in ['right_lower_medial_basal_region','left_additional_region','right_cyst','left_cystic_mass','right_artery','left_vein','nodes','renal','acquisition','comparison','clinical_context']:assert 'cystic_lung.'+key in ids
    ref=detail(Curriculum(),resolve('ra.hrct-cystic-lung'))['radiology_reference']
    assert all(not s['normal'] for s in ref['walkthrough']['steps']) and ref['reporting']['classification'] is None
    assert 'Partial thoracic orientation' in ref['spatial_model']['reporting_aim']
    assert 'four-cysts/age-forty' in ref['walkthrough']['steps'][5]['tip']

import copy,hashlib,json
from pathlib import Path
import pytest
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve,_validate_source_panel_roles
ROOT=Path(__file__).resolve().parents[1];PREFIX='open-esophagus-pmc11227487-fig'
def rows():return [r for r in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())['ra.esophagus'] if r['id'].startswith(PREFIX)]
def test_original_masters_and_swapped_PDF_object_order():
    r=rows();proof=json.loads((ROOT/'docs/esophagus-mri-source-review/original-source-review.json').read_text());assert len(r)==6
    assert [(f['source_PDF_object'],f['source_PDF_page']) for f in proof['figures']]==[(126,6),(139,7),(138,7),(149,8),(148,8),(177,9)]
    for row,f in zip(r,proof['figures']):
        path=ROOT/'web'/row['src'].removeprefix('/app/');assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']==f['source_master_sha256']
        with Image.open(path) as im:assert im.size==(f['width'],f['height']) and hashlib.sha256(im.tobytes()).hexdigest()==f['decoded_pixel_sha256']
def test_endoscopy_histology_and_separate_cases_are_not_MRI():
    r=rows();first=r[0];assert first['source_context']['source_panels_are_different_patients'];assert first['source_context']['source_case_groups']['source_T4_aortic_case']==list('uv');assert first['source_context']['source_case_groups']['different_source_T4_bronchial_case']==list('wxy')
    fifth=r[4];assert fifth['source_context']['panel_types']['h']=='Ultrasound' and fifth['source_context']['panel_types']['j']=='Histology';assert fifth['source_context']['source_caption_panel_discrepancy']
    broken=copy.deepcopy(fifth);broken['clinical_panels'].append('j');broken['source_context']['selected_panels'].append('j')
    with pytest.raises(ValueError,match='modality'):_validate_source_panel_roles(broken)
    assert [x['source_context']['population'].get('age_years') for x in r]==[None,62,67,63,64,68]
def test_source_case_images_follow_wall_and_fistula_steps_without_anatomy_approval():
    ref=detail(Curriculum(),resolve('ra.esophagus'))['radiology_reference'];w=ref['walkthrough'];assert not w['start']['images']
    assert {i for i in w['steps'][1]['images'] if i.startswith(PREFIX)}=={PREFIX+str(i) for i in range(1,7)}
    assert {i for i in w['steps'][4]['images'] if i.startswith(PREFIX)}=={PREFIX+'2'}
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for a in assets:
        if a['id'].startswith(PREFIX):assert a['anatomical_review']['status']=='pending' and not a['structure_ids'] and not a['requirement_coverage']
    other=detail(Curriculum(),resolve('ra.swallowing'))['radiology_reference'];assert not any(x['id'].startswith(PREFIX) for x in other.get('structure_atlas',[]))

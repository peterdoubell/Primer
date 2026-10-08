"""Preserved source FOV stills are not native cine or a normal reference."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];INV='ra.swallowing';ID='open-swallowing-pmc12081525-fig2'
def test_original_grayscale_master_and_case_context_survive():
    proof=json.loads((ROOT/'docs/swallowing-published-source-review/original-source-review.json').read_text());figure=proof['figures'][0];row=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV][0];assert row['id']==ID and row['clinical_panels']==['a','b'] and row['modality']=='Radiography'
    assert figure['source_PDF_object']==71 and figure['source_PDF_page']==6 and figure['explicit_original_PDF_page_binding_visually_reviewed']
    assert figure['original_HTML_and_PDF_encoded_contrast_differ'] and figure['numbered_HTML_PDF_thumbnail_RGB_RMS']>49
    path=ROOT/'web'/row['src'].removeprefix('/app/');assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']==figure['source_master_sha256']
    with Image.open(path) as image:assert image.mode=='L' and image.size==(1350,1022) and hashlib.sha256(image.tobytes()).hexdigest()==figure['decoded_pixel_sha256']
    c=row['source_context'];assert c['population']['age_not_supplied'] and c['population']['life_stage']=='unknown' and c['population']['sex']=='female'
    for key in ['full_original_cine_or_DICOM_available','frame_order_timestamps_or_frame_pulse_rates_supplied','source_views_independently_registered','still_implies_aspiration_absence_or_swallow_function','source_case_is_normal_reference','source_adult_consensus_is_patient_age_evidence']:assert c[key] is False
    asset=next(a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id']==ID);assert not asset['structure_ids'] and not asset['requirement_coverage'] and asset['anatomical_review']['status']=='pending';assert asset['source']['license']['commercial_use'] and asset['source']['license']['redistribution']
def test_FOV_example_does_not_fill_functional_steps_or_replace_other_investigations():
    ref=detail(Curriculum(),resolve(INV))['radiology_reference'];assert not ref['key_images'];w=ref['walkthrough'];assert w['start']['images']==[] and not w['start']['module_illustrations']
    assert all(not r['images'] and not r['normal'] for r in w['steps']);assert len(ref['structure_atlas'])==1
    other=detail(Curriculum(),resolve('ra.esophagus'))['radiology_reference'];assert other['key_images']

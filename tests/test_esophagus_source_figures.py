"""Actual source masters/roles do not certify microscopic anatomy or physiology."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];INV='ra.esophagus';PREFIX='open-esophagus-pmc5438315-fig'
def rows():return json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
def test_complete_original_figures_and_nonsequential_PDF_bindings_preserved():
    r=rows();proof=json.loads((ROOT/'docs/esophagus-published-source-review/original-source-review.json').read_text());figures={f['figure_number']:f for f in proof['figures']};assert len(r)==19 and {x['figure_number'] for x in r}==set(range(2,21))
    assert figures[9]['source_PDF_object']==66 and figures[10]['source_PDF_object']==65
    assert figures[12]['source_PDF_object']==76 and figures[13]['source_PDF_object']==75
    assert figures[15]['source_PDF_object']==82 and figures[16]['source_PDF_object']==81
    for x in r:
        f=figures[x['figure_number']];path=ROOT/'web'/x['src'].removeprefix('/app/');assert hashlib.sha256(path.read_bytes()).hexdigest()==x['sha256']==f['source_master_sha256']
        with Image.open(path) as im:assert im.size==(f['width'],f['height']) and hashlib.sha256(im.tobytes()).hexdigest()==f['decoded_pixel_sha256']
        asset=next(a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id']==x['id']);assert asset['anatomical_review']['status']=='pending' and not asset['structure_ids'] and not asset['requirement_coverage']
def test_drawing_is_not_histology_and_two_foreign_body_patients_are_not_merged():
    r={x['figure_number']:x for x in rows()};assert r[2]['kind']=='schematic' and r[2]['modality']=='Schematic' and r[2]['clinical_panels']==[] and r[2]['schematic_panels']==['full']
    assert r[6]['clinical_panels']==['a'] and r[6]['ancillary_panels'][0]['kind']=='Radiography' and r[6]['ancillary_panels'][0]['panels']==['b'];assert r[6]['source_context']['source_panels_are_different_patients']
    assert r[14]['clinical_panels']==['b'] and r[14]['ancillary_panels'][0]['panels']==['a']
    assert r[16]['clinical_panels']==['c'] and r[16]['ancillary_panels'][0]['panels']==['a','b']
    for x in r.values():
        c=x['source_context'];assert c['population']['age_not_supplied'] and c['population']['sex_not_supplied'];assert not c['source_native_registration_verified'] and not c['source_static_views_supply_timed_transit_or_pressure'] and not c['source_labels_are_current_patient_histology_or_cause']
def test_source_figures_follow_relevant_steps_not_intro_or_other_reader():
    r=detail(Curriculum(),resolve(INV))['radiology_reference'];w=r['walkthrough'];assert not r['key_images'] and not w['start']['images'] and not w['start']['module_illustrations']
    placed={i for s in w['steps'] for i in s['images']};assert placed=={PREFIX+str(i) for i in range(3,21)} and PREFIX+'2' not in placed
    assert all(not s['normal'] for s in w['steps']);other=detail(Curriculum(),resolve('ra.swallowing'))['radiology_reference'];assert len(other['source_motion_references'])==1 and len(other['source_anatomy_references'])==2

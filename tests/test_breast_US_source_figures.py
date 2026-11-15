import copy,hashlib,json
from pathlib import Path
import pytest
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve,_validate_source_panel_roles
ROOT=Path(__file__).resolve().parents[1];PREFIX='open-breast-us-pmc10000574-fig'
def rows(inv):return [r for r in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text()).get(inv,[]) if r['id'].startswith(PREFIX)]
def test_all_eleven_full_masters_preserve_original_samples_and_duplicate_source_bindings():
    r=rows('ra.ultrasound-breast');proof=json.loads((ROOT/'docs/breast-US-published-source-review/original-source-review.json').read_text());assert len(r)==len(proof['figures'])==11
    assert [(f['source_PDF_object'],f['source_PDF_page']) for f in proof['figures']][7:9]==[(183,9),(201,10)]
    for row,f in zip(r,proof['figures']):
        path=ROOT/'web'/row['src'].removeprefix('/app/');assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']==f['source_master_sha256']
        with Image.open(path) as im:assert im.size==(f['width'],f['height']) and hashlib.sha256(im.tobytes()).hexdigest()==f['decoded_pixel_sha256']
        assert not f['source_pixels_resampled_or_enhanced']
def test_clinical_photo_CT_mammography_and_device_output_are_separate_from_US():
    r={x['figure_number']:x for x in rows('ra.ultrasound-breast')};assert r[9]['clinical_panels']==['B'] and r[9]['ancillary_panels'][0]['kind']=='Clinical photograph';assert r[9]['source_context']['population']['sex']=='male' and r[9]['source_context']['population']['life_stage']=='unknown'
    assert r[10]['ancillary_panels'][0]['kind']=='Radiography' and r[11]['ancillary_panels'][0]['kind']=='CT';assert r[11]['source_context']['laterality']=='right'
    assert r[7]['clinical_panels']==['middle'] and r[7]['schematic_panels']==['left'] and r[7]['ancillary_panels'][0]['kind']=='Ultrasound-derived display'
    bad=copy.deepcopy(r[7]);bad['clinical_panels'].append('right');bad['source_context']['selected_panels'].append('right')
    with pytest.raises(ValueError,match='modality'):_validate_source_panel_roles(bad)
    assert not r[7]['source_context']['source_device_classification_is_current_validated_assessment']
def test_reader_scoping_does_not_borrow_MRI_registration_or_approve_full_anatomy():
    expected={'ra.ultrasound-breast':11,'ra.breast-cancer-staging':6,'ra.breast-implants':3,'ra.male-breast':1};assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for inv,n in expected.items():
        assert len(rows(inv))==n;ref=detail(Curriculum(),resolve(inv))['radiology_reference'];assert not ref['key_images'] and not ref['walkthrough']['start']['images'];assert all(not s['normal'] for s in ref['walkthrough']['steps'])
        for a in assets:
            if a['id'].startswith(PREFIX) and inv in a['investigation_ids']:assert not a['structure_ids'] and not a['requirement_coverage'] and a['anatomical_review']['status']=='pending'
    other=detail(Curriculum(),resolve('ra.mri-breast'))['radiology_reference'];assert not any(a['id'].startswith(PREFIX) for a in other.get('structure_atlas',[]))
    # Existing clinical readers/source rasters must retain their reviewed bytes.
    for row in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())['ra.esophagus']:
        assert hashlib.sha256((ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()).hexdigest()==row['sha256']

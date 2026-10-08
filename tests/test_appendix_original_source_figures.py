import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve, _validate_source_panel_roles

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'open-appendix-pmc'
REVIEW = ROOT/'docs/appendix-original-source-review'

def records():
    rows = [r for r in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())['ra.appendicitis'] if r['id'].startswith(PREFIX)]
    proof = json.loads((REVIEW/'original-source-review.json').read_text())
    return rows, proof

def test_complete_original_pixels_and_explicit_numbered_page_bindings():
    rows, proof = records()
    assert len(rows)==19
    for article in proof['articles']:
        xml = (REVIEW/(article['pmcid']+'-original.xml')).read_bytes()
        assert hashlib.sha256(xml).hexdigest()==article['original_XML_sha256']
        grant=ET.fromstring(xml).find('.//permissions/license')
        assert 'https://creativecommons.org/licenses/by/4.0/' in ET.tostring(grant,encoding='unicode')
        for f in article['figures']:
            row=next(r for r in rows if r['id']==PREFIX+article['pmcid'][3:]+'-fig'+str(f['figure_number']))
            path=ROOT/'web'/row['src'].removeprefix('/app/')
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']==f['source_master_sha256']
            with Image.open(path) as im:
                assert im.size==(f['width'],f['height']) and im.mode==f['mode']
                assert hashlib.sha256(im.tobytes()).hexdigest()==f['decoded_pixel_sha256']
                assert hashlib.sha256(im.info.get('icc_profile',b'')).hexdigest()==f['source_ICC_sha256']
            assert not f['source_pixel_changes'] and not f['source_pixels_resampled_or_enhanced']
            assert all(a>=b for a,b in zip((f['width'],f['height']),f['HTML_master_dimensions']))
    postoperative=next(a for a in proof['articles'] if a['pmcid']=='PMC4330234')
    objects={f['figure_number']:(f['source_PDF_page'],f['source_PDF_object']) for f in postoperative['figures']}
    assert objects[2]==(3,21) and objects[3]==(3,20)
    assert objects[7]==(7,68) and objects[8]==(7,67)

def test_different_patients_modalities_and_postoperative_context_cannot_be_merged():
    rows,_=records();rows={r['id']:r for r in rows}
    mixed=rows[PREFIX+'8531161-fig7']
    assert mixed['clinical_panels']==['B'] and mixed['ancillary_panels'][0]['kind']=='Ultrasound'
    bad=copy.deepcopy(mixed);bad['clinical_panels']=['A','B'];bad['source_context']['selected_panels']=['A','B']
    with pytest.raises(ValueError,match='modality'):_validate_source_panel_roles(bad)
    four=rows[PREFIX+'8531161-fig6']['source_context']
    assert four['source_panels_are_different_patients'] and len(four['source_case_groups'])==4
    for ident,n in [('8531161-fig9',2),('4330234-fig4',2),('4330234-fig5',2)]:
        ctx=rows[PREFIX+ident]['source_context']
        assert ctx['source_panels_are_different_patients'] and len(ctx['source_case_groups'])==n
    assert rows[PREFIX+'4330234-fig3']['modality']=='MRI'
    assert rows[PREFIX+'4330234-fig3']['source_context']['population']['age_years']==16
    assert rows[PREFIX+'6497212-fig1']['modality']=='Radiography'
    assert '14.4 mm' in rows[PREFIX+'6497212-fig2']['caption']
    assert all(rows[PREFIX+'6497212-fig'+str(i)]['source_context']['population']['age_years']==10 for i in [1,2,3])
    assert 'gangrenous despite' in rows[PREFIX+'8531161-fig5']['limits']

def test_reader_covers_steps_without_unsupported_negative_presets_or_new_anatomy_approval():
    rows,proof=records();ref=detail(Curriculum(),resolve('ra.appendicitis'))['radiology_reference']
    assert not ref['key_images'] and not ref['walkthrough']['start']['images']
    assert len(ref['structure_atlas'])==22
    assert all(not step['normal'] and step['images'] for step in ref['walkthrough']['steps'])
    assert 'Partial schematic' in ref['spatial_model']['reporting_aim']
    runtime_ids={r['id'] for r in rows}
    assert not any(pmc in ident for pmc in ['3205519','3846936'] for ident in runtime_ids)
    assert {r['pmcid'] for r in proof['held_candidates']}=={'PMC3205519','PMC3846936'}
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for asset in assets:
        if asset['id'] in runtime_ids:
            assert asset['anatomical_review']['status']=='pending'
            assert not asset['structure_ids'] and not asset['requirement_coverage']
            assert not asset['source_context']['source_native_registration_verified']
    # Every earlier reader's source raster remains bound to its reviewed bytes.
    for inv,images in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text()).items():
        for row in images:
            assert hashlib.sha256((ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()).hexdigest()==row['sha256']

def test_original_pdf_images_independently_decode_to_every_runtime_sample_when_source_cache_present():
    cache=Path('/Users/peter/Documents/ChatGPT/Primer/.research/appendix-original-source')
    _,proof=records()
    if not all((cache/(a['pmcid']+'.1.pdf')).exists() for a in proof['articles']):
        pytest.skip('Original acquired source PDFs are retained in the source cache, outside runtime')
    pypdf=pytest.importorskip('pypdf')
    for article in proof['articles']:
        raw=(cache/(article['pmcid']+'.1.pdf')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==article['original_PDF_sha256']
        reader=pypdf.PdfReader(cache/(article['pmcid']+'.1.pdf'))
        for f in article['figures']:
            source=next(i for i in reader.pages[f['source_PDF_page']-1].images if i.indirect_reference.idnum==f['source_PDF_object']).image
            assert hashlib.sha256(source.tobytes()).hexdigest()==f['decoded_pixel_sha256']

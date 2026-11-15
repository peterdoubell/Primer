"""Published collection figures must retain source rights, modalities and gas context."""
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.anatomy_sources.acquire_pancreatitis_published_figures import verify_license,PANEL_TYPES
from tools.check_msk_fidelity import inspect_binding

ROOT=Path(__file__).resolve().parents[1]


def figures():
    return [r for r in detail(Curriculum(),resolve('ra.ct-pancreatitis'))['radiology_reference']['structure_atlas'] if r['id'].startswith('open-pancreatitis-sureka-')]


def test_original_license_cannot_be_replaced_by_noncommercial_or_temporary_grant():
    good='<article><article-meta><permissions><license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://creativecommons.org/licenses/by/4.0/"/></permissions></article-meta></article>'
    verify_license(ET.fromstring(good))
    with pytest.raises(ValueError,match='commercial reuse'):verify_license(ET.fromstring(good.replace('/by/','/by-nc/')))
    with pytest.raises(ValueError,match='commercial reuse'):verify_license(ET.fromstring(good.replace('https://creativecommons.org/licenses/by/4.0/','https://example.org/temporary-research-permission')))


def test_all_source_examples_remain_complete_original_bytes_without_coverage_credit():
    rows=figures();assert len(rows)==7
    proof=json.loads((ROOT/'docs/pancreatitis-published-source-review/packaged-figure-selection.json').read_text())
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for row in rows:
        file=ROOT/'web'/row['src'].removeprefix('/app/')
        assert hashlib.sha256(file.read_bytes()).hexdigest()==row['sha256']
        selected=next(r for r in proof['figures'] if r['figure_number']==row['figure_number'])
        assert selected['sha256']==row['sha256']
        assert selected['source_pixels_changed'] is False
        assert row['license']=='CC BY 4.0'
        asset=next(r for r in assets if r['id']==row['id'])
        assert asset['structure_ids']==[] and asset['requirement_coverage']=={}
        assert asset['anatomical_review']['status']=='pending'
        assert asset['investigation_ids']==['ra.ct-pancreatitis']
    assert next(r for r in rows if r['figure_number']==5)['width']==951
    assert next(r for r in rows if r['figure_number']==7)['width']==1001
    assert proof['clinical_approval'] is False and proof['structure_coverage_granted'] is False


def test_serial_mixed_modalities_cannot_borrow_mri_or_ultrasound_into_ct():
    row=next(r for r in figures() if r['figure_number']==5)
    assert PANEL_TYPES[5]=={'a':'Ultrasound','b':'CT','c':'CT','d':'Ultrasound','e':'CT','f':'MRI'}
    assert row['clinical_panels']==['b','c','e'] and row['source_context']['panel_types']==PANEL_TYPES[5]
    assert {r['kind']:r['panels'] for r in row['ancillary_panels']}=={'Ultrasound':['a','d'],'MRI':['f']}
    wrong={'kind':'clinical_image','modality':'CT','source_context':copy.deepcopy(row['source_context'])}
    wrong['source_context']['selected_panels']=['f']
    issues=inspect_binding(wrong,{'id':'source.ct','modality_scope':['CT'],'context_requirements':[]})
    assert 'source_context_selected_panel_modality_mismatch' in issues


def test_mri_pseudocyst_and_gas_fistula_keep_actual_source_context():
    rows=figures();mr=next(r for r in rows if r['figure_number']==4);gas=next(r for r in rows if r['figure_number']==8)
    assert mr['modality']=='MRI' and mr['clinical_panels']==['a','b']
    assert 'no CT, DWI/ADC' in mr['limits']
    assert 'biliary stent and duodenal communication' in gas['caption']
    assert 'not labelled as microbiologically proved infection' in gas['caption']
    assert 'clinical_panels' in gas and gas['modality']=='CT'


def test_pdf_selections_bind_actual_encoded_streams_and_original_source_url():
    proof=json.loads((ROOT/'docs/pancreatitis-published-source-review/pdf-stream-readback.json').read_text())
    rows=figures()
    assert proof['pixels_reencoded'] is False
    assert [r['pdf_object_id'] for r in proof['figures']]==[47,54]
    for r in proof['figures']:
        image=next(i for i in rows if i['figure_number']==r['figure_number'])
        assert '.pdf?md5=' in image['asset_source_url']
        assert r['compressed_pdf_stream_equals_packaged_jpeg'] is True
        assert r['sha256']==image['sha256']


def test_reasoning_plate_keeps_wall_maturity_and_clinical_context():
    n=Curriculum().nodes['rad.5.pancreas-acute']
    p=next(p for p in n['lesson_media'] if p['id']=='rad-5-pancreas-acute-reasoning-plate')
    assert 'wall maturity and clinical context' in p['caption']
    assert 'name and action' not in p['caption']

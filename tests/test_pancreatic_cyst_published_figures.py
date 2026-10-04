"""Original cyst figures preserve full composites, exact streams and modality/grade boundaries."""
import copy
import hashlib
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import inspect_binding

ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/pancreatic-cyst-published-source-review'


def figures():
    return [r for r in detail(Curriculum(),resolve('ra.pancreatic-cysts'))['radiology_reference']['structure_atlas'] if r['id'].startswith('open-pancreatic-cyst-')]


def test_all_seven_figures_use_larger_original_encoded_streams_without_structure_credit():
    rows=figures();assert len(rows)==7
    original=json.loads((REVIEW/'original-source-review.json').read_text())
    streams=json.loads((REVIEW/'original-pdf-stream-selection.json').read_text())
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for r in rows:
        src=next(s for s in original['figures'] if r['source_url']==s['source_article_url'] and r['figure_number']==int(s['figure_id'][3:]))
        stream=next(s for s in streams['figures'] if s['pmcid']==src['pmcid'] and s['figure_id']==src['figure_id'])
        assert r['width']>src['width'] and r['height']>src['height']
        assert hashlib.sha256((ROOT/'web'/r['src'].removeprefix('/app/')).read_bytes()).hexdigest()==stream['sha256']==r['sha256']
        assert stream['compressed_pdf_stream_matches_extracted_jpeg'] is True
        assert stream['source_pixels_resampled_or_reencoded'] is False
        assert r['license']=='CC BY 4.0' and r['modality']=='MRI'
        assert r['clinical_panels']==src['selected_mri_panels']
        a=next(a for a in assets if a['id']==r['id'])
        assert a['structure_ids']==[] and a['requirement_coverage']=={} and a['investigation_ids']==['ra.pancreatic-cysts']
        assert a['anatomical_review']['status']=='pending'
    assert original['separately_credited_2021_book_figure_excluded']=='PMC8355307 Fig2'
    assert not any('pmc8355307-fig2' in r['id'] for r in rows)


def test_pet_ct_eus_and_histology_cannot_lend_features_to_selected_mri():
    r=next(r for r in figures() if 'pmc13315461-fig4' in r['id'])
    assert r['clinical_panels']==list('abcdef')
    assert {p['kind']:p['panels'] for p in r['ancillary_panels']}=={'PET-CT':['g'],'Ultrasound':['h'],'Histology':['i','j']}
    for panel in ['g','h','i']:
        context=copy.deepcopy(r['source_context']);context['selected_panels']=[panel]
        expected='source_context_selected_panel_not_clinical_image' if panel=='i' else 'source_context_selected_panel_modality_mismatch'
        assert expected in inspect_binding({'kind':'clinical_image','modality':'MRI','source_context':context},{'id':'mri','modality_scope':['MRI'],'context_requirements':[]})
    assert 'enhancement alone does not establish malignant grade' in r['caption']
    high=next(r for r in figures() if 'pmc13315461-fig5' in r['id'])
    assert 'cannot independently establish histological grade' in high['caption']


def test_ct_architecture_stays_separate_from_mri_and_communication_geometry():
    r=next(r for r in figures() if 'pmc8355307-fig4' in r['id'])
    assert r['clinical_panels']==['b','c','d']
    assert r['ancillary_panels'][0]['kind']=='CT' and r['ancillary_panels'][0]['panels']==['a']
    ipmn=next(r for r in figures() if 'pmc8355307-fig18' in r['id'])
    assert 'complete communication geometry remain unapproved' in ipmn['caption']
    assert 'calibrated native DICOM volume' in ipmn['limits']

"""Complete CT/operative composites retain independent modalities and original pixel streams."""
import copy,hashlib,json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import inspect_binding

ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/peritoneal-published-source-review'


@pytest.mark.parametrize('module',['ra.ct-peritoneum','ra.ct-peritoneal-carcinomatosis'])
def test_seven_original_figures_are_available_with_no_approved_structure_credit(module):
    rows=[r for r in detail(Curriculum(),resolve(module))['radiology_reference']['structure_atlas'] if r['id'].startswith('open-peritoneal-')]
    assert len(rows)==7 and len({r['id'] for r in rows})==7
    source=json.loads((REVIEW/'original-source-review.json').read_text());streams=json.loads((REVIEW/'original-pdf-stream-selection.json').read_text())
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for r in rows:
        original=next(s for s in source['figures'] if s['figure_number']==r['figure_number'])
        stream=next(s for s in streams['figures'] if s['figure_number']==r['figure_number'])
        assert r['width']>original['width'] and r['height']>original['height']
        assert hashlib.sha256((ROOT/'web'/r['src'].removeprefix('/app/')).read_bytes()).hexdigest()==r['sha256']==stream['sha256']
        assert stream['original_dct_stream_readback_verified'] is True and stream['source_pixels_changed'] is False
        assert r['modality']=='CT' and r['clinical_panels']==['a']
        assert r['license']=='CC BY 4.0'
        assert r['ancillary_panels'][0]['kind']=='Clinical photograph' and r['ancillary_panels'][0]['panels']==['b']
        a=next(a for a in assets if a['id']==r['id'])
        assert a['investigation_ids']==[module] and a['structure_ids']==[] and a['requirement_coverage']=={}
        assert a['anatomical_review']['status']=='pending'


def test_operative_visibility_cannot_be_borrowed_as_ct_anatomy():
    r=next(r for r in detail(Curriculum(),resolve('ra.ct-peritoneal-carcinomatosis'))['radiology_reference']['structure_atlas'] if r['figure_number']==11)
    context=copy.deepcopy(r['source_context']);context['selected_panels']=['b']
    assert 'source_context_selected_panel_not_clinical_image' in inspect_binding({'kind':'clinical_image','modality':'CT','source_context':context},{'id':'ct','modality_scope':['CT'],'context_requirements':[]})
    assert 'CT appearance alone does not establish microscopic implants' in r['caption']
    assert 'cannot supply CT features, histology or operative eligibility' in r['limits']


def test_repeated_attachments_are_not_new_independent_figures_or_patients():
    refs=[detail(Curriculum(),resolve(m))['radiology_reference']['structure_atlas'] for m in ['ra.ct-peritoneum','ra.ct-peritoneal-carcinomatosis']]
    rows=[[r for r in items if r['id'].startswith('open-peritoneal-')] for items in refs]
    assert len({r['id'] for items in rows for r in items})==14
    assert len({r['src'] for items in rows for r in items})==7
    assert {r['sha256'] for r in rows[0]}=={r['sha256'] for r in rows[1]}

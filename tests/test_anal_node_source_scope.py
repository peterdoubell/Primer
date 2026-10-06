"""Subregion geometry and public form rights cannot inherit historical staging or controlled MRI."""
import hashlib
import json
import pytest
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,requirements_for,inspect_binding
from tools.anatomy_sources.review_anal_series_sources import source_rows

ROOT=Path(__file__).resolve().parents[1]


def test_all_explicit_side_and_subregion_fields_need_their_own_source_evidence():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(i for i in data['investigations'] if i['investigation_id']=='ra.mri-anal-cancer')
    groups=[s for s in item['structures'] if s['id'].startswith('anal_cancer.node_subregion_')]
    assert len(groups)==20 and sum(len(s['required_parts']) for s in groups)==160
    assert {s['laterality'] for s in groups}=={'left','right'}
    for side in ['left','right']:
        for region in ['lateral_sacral','presacral','internal_iliac_anterior','common_iliac_posterolateral','inguinal_deep','inguinal_superficial']:
            assert 'anal_cancer.node_subregion_'+side+'_'+region in {s['id'] for s in groups}
    assert all(s['source_document_page'] in [4,6,8,10] for s in groups)
    sub={**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}}
    result=audit(sub,{'assets':[{'id':'parent-node-map','kind':'model','investigation_ids':[item['investigation_id']],
                               'structure_ids':['anal_cancer.left_internal_iliac_nodes','anal_cancer.right_inguinal_nodes']}]},
                 expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==1125 and result['counts']['verified']==0 and result['counts']['missing']==1125
    target=next(p for p in requirements_for(item) if p['id']=='anal_cancer.node_subregion_right_presacral.named_vessel_interface')
    assert 'source_context_laterality_mismatch' in inspect_binding({'kind':'clinical_image','modality':'MRI','source_context':{'laterality':'left'}},target)


def test_access_rows_keep_license_bound_to_its_specific_artifact():
    rows=source_rows(b'<table><tr><td>Images</td><td>Unavailable</td><td>NIH Controlled Data Access Policy</td></tr><tr><td>Form</td><td><a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></td></tr></table>')
    assert rows[0][-1]['text']=='NIH Controlled Data Access Policy' and not rows[0][-1]['urls']
    assert rows[1][-1]['text']=='CC BY 4.0' and rows[1][-1]['urls']==['https://creativecommons.org/licenses/by/4.0/']
    review=json.loads((ROOT/'docs/anal-series-source-review/source-access-and-form-review.json').read_text())
    first=review['sources'][0]
    assert hashlib.sha256((ROOT/'docs/anal-series-source-review'/first['form_file']).read_bytes()).hexdigest()==first['form_sha256']
    assert first['specific_form_license']=='CC BY 4.0' and not first['form_license_is_image_or_clinical_dataset_permission']
    assert first['image_access']==first['clinical_access']=='unavailable_controlled'
    assert not review['raw_MRI_or_clinical_data_downloaded'] and not review['runtime_promoted']
    assert not review['separate_diagram_credit_and_anatomical_fidelity_verified']


def test_historical_staging_choices_and_default_negative_claims_do_not_enter_runtime():
    review=json.loads((ROOT/'docs/anal-series-source-review/source-access-and-form-review.json').read_text())
    assert review['staging_holds']==[{'source_page':11,'choices':['N2','N3'],'runtime_categories_adopted':False},
                                   {'source_page':12,'choices':['M2'],'runtime_categories_adopted':False}]
    ref=detail(Curriculum(),resolve('ra.mri-anal-cancer'))['radiology_reference']
    assert 'N2-metastases' not in str(ref) and 'M2-based' not in str(ref)
    for step in [ref['walkthrough']['steps'][2],ref['walkthrough']['steps'][3]]:
        assert 'adequate / limited / unassessed' in str(step['normal'])
        assert 'Unresolved' in str(step['normal'])
    assert 'No invasion of adjacent organs.' not in str(ref['walkthrough'])
    assert 'No suspicious mesorectal, pelvic sidewall or inguinal nodes.' not in str(ref['walkthrough'])


def test_retained_original_form_pages_support_the_recorded_holds():
    pypdf=pytest.importorskip('pypdf')
    pdf=pypdf.PdfReader(ROOT/'docs/anal-series-source-review/original-consensus-form.pdf')
    assert len(pdf.pages)==13
    assert 'N2' in pdf.pages[10].extract_text() and 'N3' in pdf.pages[10].extract_text()
    assert 'M2' in pdf.pages[11].extract_text()
    text=' '.join(pdf.pages[3].extract_text().lower().split())
    assert 'lateral sacral' in text and 'pre-sacral' in text

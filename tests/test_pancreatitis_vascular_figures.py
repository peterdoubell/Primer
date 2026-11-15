"""Source arterial/venous examples retain grants, uncertainty and actual case context."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license

ROOT=Path(__file__).resolve().parents[1]


def test_original_xml_grants_remain_version_specific_and_restrictive_sources_are_rejected():
    for number in ['3.0','4.0']:
        p=ET.fromstring('<permissions><license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://creativecommons.org/licenses/by/'+number+'/"/></permissions>')
        assert exact_license(p)==('CC BY '+number,'https://creativecommons.org/licenses/by/'+number+'/')
    for url in ['https://creativecommons.org/licenses/by-nc/4.0/','https://example.org/temporary-research-grant']:
        p=ET.fromstring('<permissions><license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="'+url+'"/></permissions>')
        with pytest.raises(ValueError,match='restricted'):exact_license(p)


def test_original_vascular_examples_do_not_invent_phase_diagnosis_or_structure_credit():
    ref=detail(Curriculum(),resolve('ra.ct-pancreatitis'))['radiology_reference']
    rows=[r for r in ref['structure_atlas'] if r['id'].startswith('open-pancreatitis-vascular-')]
    assert len(rows)==3
    proof=json.loads((ROOT/'docs/pancreatitis-vascular-source-review/original-source-review.json').read_text())
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for r in rows:
        source=next(s for s in proof['figures'] if s['source_article_url']==r['source_url'])
        assert r['modality']=='CT' and r['sha256']==source['sha256']
        assert hashlib.sha256((ROOT/'web'/r['src'].removeprefix('/app/')).read_bytes()).hexdigest()==r['sha256']
        assert r['license']==source['license']
        a=next(a for a in assets if a['id']==r['id'])
        assert a['structure_ids']==[] and a['requirement_coverage']=={}
        assert a['anatomical_review']['status']=='pending' and a['investigation_ids']==['ra.ct-pancreatitis']
    conflict=next(r for r in rows if 'pmc12490646' in r['id'])
    assert conflict['source_modality_caption_body_discrepancy'] is True
    assert 'body calls this CTA' in conflict['caption'] and 'context discrepancy remains unresolved' in conflict['caption']
    assert 'does not independently verify active extravasation' in conflict['limits']
    recurrent=next(r for r in rows if 'pmc9870600' in r['id'])
    assert recurrent['license']=='CC BY 3.0'
    assert 'Recurrent-pancreatitis source case' in recurrent['caption'] and 'acute-only episode' in recurrent['limits']
    portal=next(r for r in rows if 'pmc12358223' in r['id'])
    assert 'nonocclusive proximal portal-vein filling defect' in portal['caption']
    assert 'complete portal/SMV/splenic-vein extent' in portal['limits']

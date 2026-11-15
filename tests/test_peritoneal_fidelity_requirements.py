"""Peritoneal compartments and source-specific burden cannot be inferred from parent anatomy."""
import json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory(key):
    d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());i=next(r for r in d['investigations'] if r['investigation_id']==key)
    return {**d,'investigations':[i],'scope':{'catalog_investigation_ids':[key]}},i


@pytest.mark.parametrize('key,count,prefix',[('ra.ct-peritoneum',203,'peritoneum'),('ra.ct-peritoneal-carcinomatosis',253,'peritoneal_carcinoma')])
def test_peritoneal_scope_binds_every_reporting_section_and_actual_compartments(key,count,prefix):
    d,i=inventory(key);r=detail(Curriculum(),resolve(key))['radiology_reference'];validate_reporting_snapshots(d,{key:r['reporting']})
    assert i['source_contract_sha256']==digest({k:r.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(i)};assert len(leaves)==count
    for target in ['spaces.epiploic_foramen','spaces.rectouterine_if_present','ligaments.hepatoduodenal','mesentery.sigmoid_mesocolon',
                   'bowel.serosal_margin','deposits.miliary_suspicion','critical_sites.ureter_interface','capsular_interface.hepatic_parenchymal_interface']:
        assert prefix+'.'+target in leaves
    assert {r['checklist_index'] for s in i['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(d,{'assets':[{'id':'abdomen','kind':'model','investigation_ids':[key],'structure_ids':[prefix+'.surfaces',prefix+'.spaces']}]},expected_catalog_ids={key})
    assert result['representation_requirements']==count*3
    assert result['counts']=={'verified':0,'unverified':0,'missing':count*3}


def test_all_13_source_pci_regions_keep_actual_extent_and_unassessed_state():
    _,i=inventory('ra.ct-peritoneal-carcinomatosis')
    regions=[s for s in i['structures'] if s['id'].startswith('peritoneal_carcinoma.pci_')]
    assert len(regions)==13
    assert any(s['id'].endswith('upper_jejunum') for s in regions) and any(s['id'].endswith('lower_ileum') for s in regions)
    assert all(any(p['id'].endswith('uncertain_or_unassessed_region') for p in s['required_parts']) for s in regions)
    leaves={r['id']:r for r in requirements_for(i)}
    assert 'source_context_purpose_mismatch' in inspect_binding({'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}},leaves['peritoneal_carcinoma.deposits.complete_margin'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding({'kind':'clinical_image','modality':'CT'},leaves['peritoneal_carcinoma.mri.source_dwi_region'])


def test_ct_burden_and_ascites_are_not_historical_score_only_operative_verdicts():
    n=Curriculum().nodes['rad.5.peritoneum'];r=n['reference']
    assert 'No universal CT-score-only' in r['measure'][1]['cutoff']
    assert 'new ascites alone does not establish' in r['approach'][5]['detail']
    assert 'CT-estimated' in r['template'] and 'no automatic score-only decision' in r['template']
    assert n['quiz'][3]['answer']=='11'
    assert 'do not make imaging alone an operative verdict' in n['quiz'][4]['explain']
    steps=detail(Curriculum(),resolve('ra.ct-peritoneal-carcinomatosis'))['radiology_reference']['walkthrough']['steps']
    assert 'Ascites alone is nonspecific' in steps[0]['tip']
    assert 'multidisciplinary assessment' in steps[3]['tip']
    assert 'Imaging PCI is not operative PCI' in steps[4]['tip']

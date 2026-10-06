"""TAVI anatomy and device/access decisions require source-specific evidence, not isolated cutoffs."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots

ROOT=Path(__file__).resolve().parents[1]
IDENT='ra.ct-tavi'

def test_complete_source_contract_and_every_report_field_are_bound():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT)
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    validate_reporting_snapshots(single,{IDENT:ref['reporting']})
    assert len(item['structures'])==54 and len(requirements_for(item))==454
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={p['id'] for p in requirements_for(item)}
    for suffix in ['annulus.each_attachment_nadir','annulus.area','annulus.perimeter','annulus.orthogonal_minimum_diameter',
        'noncoronary_cusp.leaflet_to_coronary_or_stj_relation','left_coronary_ostium.inferior_ostial_margin',
        'right_common_femoral.minimum_orthogonal_lumen_and_location','left_axillary.uncovered_route_extent',
        'transcaval_target.interposed_tissue_or_bowel','prior_surgical_valve.labelled_size_vs_actual_internal_diameter',
        'prior_transcatheter_valve.leaflet_or_neoskirt_geometry','virtual_valve_model.virtual_valve_to_stj_distances',
        'planning_limits.device_specific_instructions_and_version']:
        assert 'tavi.'+suffix in ids
    result=audit(single,{'assets':[{'id':'generic-root','kind':'model','investigation_ids':[IDENT],
        'structure_ids':['tavi.annulus','tavi.left_coronary_ostium']}]},expected_catalog_ids={IDENT})
    assert result['representation_requirements']==1362 and result['counts']=={'verified':0,'unverified':0,'missing':1362}

def test_scoring_sizing_and_access_are_actual_source_and_team_decisions():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];s=ref['walkthrough']['steps']
    assert 'device-specific heart-team' in s[0]['tip']
    assert 'bicuspid/other morphology' in s[0]['look']
    assert 'not an automatically valid Agatston score' in s[1]['tip']
    assert 'virtual-device distances' in s[2]['tip'] and 'simulation assumptions' in s[2]['tip']
    assert 'no universal diameter cutoff' in s[4]['tip']
    assert 'actual candidate' in s[4]['findings'][2].lower()
    assert 'heart-team planning' in ref['reporting']['escalation'][0]
    item=next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']==IDENT)
    assert item['clinical_validation_status'].startswith('draft_') and all(i['requires_site_instantiation'] for i in item['structures'])

"""Thyroid scope includes actual components and interfaces without turning ultrasound into pathology."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1];INV='ra.ultrasound-thyroid'
def item():return next(x for x in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if x['investigation_id']==INV)
def test_full_thyroid_nodal_and_adjacent_interface_scope_is_preserved():
    i=item();assert i['module_id']=='rad.5.thyroid-tirads' and i['modality_scope']==['Ultrasound']
    assert len(i['structures'])==72 and len(requirements_for(i))==445
    ids={x['id'] for x in i['structures']}
    for side in ['left','right']:
        for key in ['thyroid_lobe','superior_pole_nodules','inferior_pole_nodules','actual_central_VI_nodes','covered_superior_mediastinal_VII_nodes','nodule_to_capsule_and_perithyroidal_tissue','nodule_to_esophagus','nodule_to_carotid_jugular_interface','encountered_recurrent_laryngeal_nerve_region','encountered_parathyroid_or_mimic']:
            assert 'thyroid.'+side+'_'+key in ids
    assert 'thyroid.not_applicable_isthmus_or_midline_nodules' in ids
    assert not any('left_isthmus' in x or 'right_isthmus' in x for x in ids)
    parts={p['name'].lower() for s in i['structures'] for p in s['required_parts']}
    assert any('source resolved hilum' in p for p in parts) and any('cortex' in p for p in parts)
    assert any('solid fluid spongiform' in p for p in parts) and any('uncovered extent' in p for p in parts)
    assert all(s['requires_site_instantiation'] for s in i['structures'])
    assert all(0<=r['checklist_index']<6 for s in i['structures'] for r in s['report_refs'])
def test_actual_acquired_reporting_and_function_are_distinct_from_normal_presets():
    r=detail(Curriculum(),resolve(INV))['radiology_reference'];walk=r['walkthrough']
    assert all(s['normal']=={} for s in walk['steps'])
    assert walk['spatial_model']['family']=='neck' and 'Partial neck orientation only' in walk['spatial_model']['reporting_aim']
    assert 'not all reverberation' in walk['steps'][2]['tip']
    assert 'biopsy results' in walk['steps'][4]['tip'] and 'growth' in walk['steps'][4]['tip']
    assert len(r['reporting']['checklist'])==6
    functional=' '.join(item()['functional_evidence_requirements']).lower()
    for term in ['doppler','histology','cytology','thyroid function','reverberation']:assert term in functional

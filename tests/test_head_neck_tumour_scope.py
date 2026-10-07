import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1];INV='ra.head-neck-malignancy'
def item():return next(x for x in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if x['investigation_id']==INV)
def test_primary_gland_duct_route_and_nodal_interfaces_remain_required():
    i=item();assert i['module_id']=='rad.5.deep-neck-spaces' and len(i['structures'])==88 and len(requirements_for(i))==528
    ids={x['id'] for x in i['structures']}
    for side in ['left','right']:
        for key in ['parotid_superficial_deep_accessory_gland_and_duct','submandibular_gland_deep_extension_and_duct','sublingual_gland_and_ducts','each_encountered_minor_salivary_gland_site','facial_nerve_intraparotid_branches_and_skull_base_route','trigeminal_V1_V2_V3_and_actual_peripheral_branches','each_actual_vessel_wall_lumen_to_lesion_interface','actual_VI_nodes','covered_VII_and_other_map_dependent_nodes','each_actual_treated_or_repaired_tissue_interface']:
            assert 'head_neck_tumour.'+side+'_'+key in ids
    assert all(x['requires_site_instantiation'] and x['modality_scope']==['MRI','CT'] for x in i['structures'])
    assert all(0<=r['checklist_index']<5 for x in i['structures'] for r in x['report_refs'])
def test_imaging_patterns_do_not_preset_histology_function_or_stage():
    r=detail(Curriculum(),resolve(INV))['radiology_reference'];w=r['walkthrough']
    assert all(x['normal']=={} for x in w['steps']) and 'Partial head/neck orientation' in w['spatial_model']['reporting_aim']
    assert 'not separated reliably by a universal' in w['steps'][0]['tip']
    assert 'remodelling is not proof of benignity' in w['steps'][1]['tip']
    assert 'not a stand-alone diagnosis' in w['steps'][3]['tip']
    evidence=' '.join(item()['functional_evidence_requirements'])
    for term in ['histology/cytology','molecular assays','formal site-specific staging','salivary secretion/duct patency']:assert term in evidence

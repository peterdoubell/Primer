import copy,json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.anatomy_sources.expand_breast_requirements import IDS,build_draft
from tools.check_msk_fidelity import requirements_for
from tools.check_radiology_fidelity import digest
ROOT=Path(__file__).resolve().parents[1]
def inputs(inv):
    ref=catalog.detail(Curriculum(),catalog.resolve(inv))['radiology_reference'];node=json.loads((ROOT/'data/radiology/reporting-steps/breast.json').read_text())['investigations'][inv];return ref,node
@pytest.mark.parametrize('inv',IDS)
def test_every_actual_side_route_node_lesion_and_device_remains_in_full_draft(inv):
    ref,node=inputs(inv);before=copy.deepcopy((ref,node));guide,draft,item,removed=build_draft(inv,ref,node);assert (ref,node)==before
    assert removed==sum(bool(s.get('normal')) for s in node['steps']) and all(not s['normal'] for s in draft['steps'])
    expected=114 if inv=='ra.breast-implants' else 95 if inv in ['ra.mri-breast','ra.breast-cancer-staging'] else 92;assert len(item['structures'])==expected and len(requirements_for(item))==expected*6
    keys={s['id'] for s in item['structures']};prefix=inv.removeprefix('ra.').replace('-','_')
    for side in ['left','right']:
        for key in ['skin_epidermis','superficial_fascia_anterior_layer','superficial_fascia_posterior_layer','cooper_ligaments_and_actual_attachments','each_actual_terminal_segmental_and_lactiferous_duct_wall_lumen','each_actual_cutaneous_intercostal_and_nipple_neural_route','axillary_level_i_nodes','axillary_level_ii_nodes','axillary_level_iii_nodes','interpectoral_rotter_nodes','internal_mammary_nodes','intramammary_nodes','every_actual_mass_boundary_and_internal_component','each_actual_non_mass_lesion_or_enhancement_component','each_actual_biopsy_clip_wire_seed_and_tissue_correspondence']:
            assert prefix+'.'+side+'_'+key in keys
        if inv=='ra.breast-implants':
            for key in ['each_actual_shell_layer_and_shell_discontinuity','external_fibrous_capsule_and_implant_capsule_interface','each_actual_valve_port_expander_and_connection','each_actual_peri_implant_fluid_collection_and_capsular_mass']:assert prefix+'.'+side+'_'+key in keys
    assert all(s['requires_site_instantiation'] and not s.get('requirement_coverage') for s in item['structures'])
    assert 'single-left-breast' in draft['model']['reporting_aim'] and 'unverified' in draft['model']['reporting_aim']
    for original,expanded in zip(ref['reporting']['template_sections'],guide['template_sections']):assert original['body'].split('\n\nAdditional source anatomy:')[0] in expanded['body']
    for step in draft['steps']:assert set(step['measurements']) <= {m['name'] for m in guide['measurements']}
    assert {m['name'] for m in ref['reporting']['measurements']} <= {m['name'] for m in guide['measurements']}
@pytest.mark.parametrize('inv',IDS)
def test_bad_topology_and_measurement_routes_fail_without_truncation(inv):
    ref,node=inputs(inv);node['steps'].append(copy.deepcopy(node['steps'][0]))
    with pytest.raises(ValueError,match='topology'):build_draft(inv,ref,node)
    ref,node=inputs(inv);node['steps'][0]['measurements']=['Unregistered measurement']
    with pytest.raises(ValueError,match='measurement routing'):build_draft(inv,ref,node)
def test_six_applied_contracts_and_modality_population_scope_remain_explicit():
    requirements=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());items={i['investigation_id']:i for i in requirements['investigations']};total=0
    for inv in IDS:
        item=items[inv];ref,_=inputs(inv);total+=len(item['structures']);assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
        assert item['clinical_validation_status'].startswith('draft_requires_') and all(not s.get('requirement_coverage') for s in item['structures'])
    assert total==580 and items['ra.mammography']['modality_scope']==['Radiography'] and items['ra.ultrasound-breast']['modality_scope']==['Ultrasound'] and items['ra.mri-breast']['modality_scope']==['MRI']
    stage,_=inputs('ra.breast-cancer-staging');assert 'pectoral involvement is not alone' in stage['walkthrough']['steps'][2]['look'];assert 'No whole-body imaging is automatically required' in stage['walkthrough']['steps'][4]['look']
    implant,_=inputs('ra.breast-implants');assert 'BIA-ALCL and SCC are different' in implant['walkthrough']['steps'][3]['look']
    male,_=inputs('ra.male-breast');assert 'fat-only normal template' in ' '.join(male['reporting']['protocol']);assert 'patient sex does not itself certify benignity' in male['walkthrough']['steps'][4]['look']
    MRI,_=inputs('ra.mri-breast');assert 'actual times' in MRI['walkthrough']['steps'][3]['look'] and 'full BI-RADS manual' in MRI['reporting']['classification']['summary']

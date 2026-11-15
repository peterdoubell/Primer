"""Full anatomical scope requires actual case sites and modalities; laboratory facts are not geometry."""
import json
from pathlib import Path
from tools.check_msk_fidelity import requirements_for
from tools.anatomy_sources.expand_thoracic_tb_requirements import build
ROOT=Path(__file__).resolve().parents[1]
def test_full_floor_and_current_source_contract():
    item=build();stored=next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']=='ra.tuberculosis')
    assert item==stored and item['module_id']=='rad.5.chest-infection'
    assert len(item['structures'])==87 and len(requirements_for(item))==652
    assert item['modality_scope']==['Radiography','CT','MRI','Ultrasound']
def test_regions_connections_and_extrapulmonary_tissues_are_required():
    item=build();ids={s['id'] for s in item['structures']}
    for key in ['right_upper_apical_region','left_additional_region','right_distal_airway','left_pulmonary_arterial','right_systemic_collateral','left_venous','right_hilar_nodes','left_axillary_nodes','mediastinal_nodes_subcarinal','mediastinal_nodes_additional_or_unassigned','right_empyema_extension','left_fistula','right_breast_chestwall','pericardium','myocardium_chambers','thoracic_spine','sternum_clavicles','vascular_cavity_connection','residual_post_treatment']:
        assert 'thoracic_tb.'+key in ids
    assert all(s['requires_site_instantiation'] and s['report_refs'] for s in item['structures'])
    assert all('Projection overlap' in s['condition'] for s in item['structures'])
def test_lab_and_function_confirmation_do_not_become_fake_anatomical_parts():
    item=build();parts=[r['name'].lower() for s in item['structures'] for r in s['required_parts']]
    assert not any('genotype' in name or 'susceptibility' in name or 'infectivity' in name for name in parts)
    assert any('laboratory/specimen/molecular/culture/susceptibility' in r for r in item['functional_evidence_requirements'])
    assert 'not structures to invent in3D' in item['functional_evidence_requirements'][0]
    assert any('scar/calcium' in issue for issue in item['source_scope_issues'])

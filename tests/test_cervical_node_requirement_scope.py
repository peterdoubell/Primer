"""Named nodal maps and actual nodes cannot collapse into interchangeable level labels."""
import json
from pathlib import Path
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1]
def item():return next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']=='ra.cervical-lymph-nodes')

def test_surgical_and_extended_VII_remain_distinct_source_requirements():
    structures={s['id']:s for s in item()['structures']}
    for side in ['left','right']:
        surgical=structures['cervical_nodes.'+side+'_covered_superior_mediastinal_surgical_VII_if_named']
        extended=structures['cervical_nodes.'+side+'_retropharyngeal_extended_VIIa']
        retrostyloid=structures['cervical_nodes.'+side+'_retrostyloid_extended_VIIb']
        assert 'surgical' in surgical['map_scope'].lower() and 'not automatically' in extended['map_scope']
        assert surgical['id']!=extended['id']!=retrostyloid['id']
    Ia=structures['cervical_nodes.not_applicable_submental_Ia_midline']
    assert Ia['laterality']=='not_applicable'
    assert not any(s['id'].endswith('_submental_Ia_midline') and s['laterality'] in ['left','right'] for s in structures.values())


def test_actual_nonindex_nodes_and_every_source_interface_remain_required():
    r=item();structures={s['id']:s for s in r['structures']}
    for side in ['left','right']:
        for key in ['every_actual_nonindex_covered_node','each_actual_conglomerate_component','internal_jugular_venous_course_and_connections','skin_subcutaneous_and_superficial_fascial_interfaces']:
            assert structures['cervical_nodes.'+side+'_'+key]['requires_site_instantiation']
        node=structures['cervical_nodes.'+side+'_each_actual_pretracheal_node']
        assert any(p['id'].endswith('source_resolved_cortex') for p in node['required_parts'])
        assert any(p['id'].endswith('source_resolved_hilum') for p in node['required_parts'])
    assert len(requirements_for(r))==807 and r['functional_evidence_requirements']
    assert {i for s in structures.values() for i in s['walkthrough_step_indices']}==set(range(5))
    assert {p['checklist_index'] for s in structures.values() for p in s['report_refs']}==set(range(5))

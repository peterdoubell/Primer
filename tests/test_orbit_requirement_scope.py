"""A compartment sketch or selected MRI cases cannot stand for all reportable orbital anatomy."""
import json
from pathlib import Path
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1]
def item():return next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']=='ra.ct-mri-eye')

def test_bilateral_muscle_components_and_globe_interfaces_are_not_generic_parents():
    structures={s['id']:s for s in item()['structures']}
    for side in ['left','right']:
        for muscle in ['superior_rectus','inferior_rectus','medial_rectus','lateral_rectus','superior_oblique','inferior_oblique','levator_palpebrae']:
            for component in ['belly','tendon','insertion_or_attachment']:
                s=structures['orbit.'+side+'_'+muscle+'_'+component]
                assert s['laterality']==side and s['requires_site_instantiation']
        for key in ['retina_and_source_detachment_interfaces','choroid_and_source_detachment_interfaces','optic_nerve_sheath_and_perineural_interfaces','superior_ophthalmic_vein_and_connections','lacrimal_sac_and_actual_drainage_interfaces']:
            assert 'orbit.'+side+'_'+key in structures
    assert len(requirements_for(item()))==1116
    assert {i for s in structures.values() for i in s['walkthrough_step_indices']}==set(range(5))
    assert {r['checklist_index'] for s in structures.values() for r in s['report_refs']}==set(range(5))

def test_bone_and_neural_sources_remain_distinct_and_function_is_not_geometry():
    structures={s['id']:s for s in item()['structures']}
    for side in ['left','right']:
        assert structures['orbit.'+side+'_optic_canal_bony_boundaries']['modality_scope']==['CT']
        assert structures['orbit.'+side+'_optic_nerve_intracanalicular_segment']['modality_scope']==['MRI']
    assert item()['functional_evidence_requirements'] and 'draft_requires' in item()['clinical_validation_status']

"""Tiny source structures and neural/device evidence cannot collapse into a generic ear parent."""
import json
from pathlib import Path
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1]


def item():
    rows=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations']
    return next(r for r in rows if r['investigation_id']=='ra.ct-temporal-bone')


def test_bilateral_ossicular_components_and_critical_bony_channels_need_CT():
    structures={s['id']:s for s in item()['structures']}
    for side in ['left','right']:
        for key in ['malleus_manubrium','incus_lenticular_process','incudostapedial_articulation','stapes_anterior_crus','stapes_posterior_crus','stapes_footplate','facial_canal_tympanic_segment','carotid_canal_and_middle_ear_boundary','sigmoid_sinus_plate_and_bony_boundary']:
            s=structures['temporal_bone.'+side+'_'+key]
            assert s['modality_scope']==['CT'] and s['laterality']==side and s['requires_site_instantiation']
    assert {i for s in structures.values() for i in s['walkthrough_step_indices']}==set(range(5))
    assert {r['checklist_index'] for s in structures.values() for r in s['report_refs']}==set(range(5))


def test_CT_bony_canals_do_not_supply_MRI_neural_or_membranous_tissue():
    structures={s['id']:s for s in item()['structures']}
    for side in ['left','right']:
        for key in ['cochlear_nerve','superior_vestibular_nerve','inferior_vestibular_nerve','covered_facial_nerve_and_actual_branches','membranous_semicircular_and_ampullary_regions_if_reported']:
            assert structures['temporal_bone.'+side+'_'+key]['modality_scope']==['MRI']
        assert 'temporal_bone.'+side+'_cochlear_implant_electrode_array_and_each_actual_contact' in structures
        assert 'temporal_bone.'+side+'_postoperative_fat_cartilage_or_other_graft_and_mimic' in structures
    assert len(requirements_for(item()))==1380
    assert item()['functional_evidence_requirements'] and 'draft_requires' in item()['clinical_validation_status']

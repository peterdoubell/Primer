"""The limited five-label native case must not erase reportable operative and extension anatomy."""
import json
from pathlib import Path
from tools.check_msk_fidelity import requirements_for

ROOT = Path(__file__).resolve().parents[1]


def item():
    rows = json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations']
    return next(r for r in rows if r['investigation_id'] == 'ra.mri-sinuses')


def test_bilateral_operative_landmarks_require_actual_CT_and_all_report_steps_are_bound():
    r = item()
    structures = {s['id']: s for s in r['structures']}
    for side in ['left', 'right']:
        for name in ['lamina_papyracea', 'cribriform_plate', 'lateral_lamella_and_olfactory_fossa', 'optic_canal_boundary', 'carotid_canal_boundary', 'anterior_ethmoidal_artery_canal', 'onodi_cell_if_present']:
            s = structures['sinonasal.'+side+'_'+name]
            assert s['laterality'] == side and s['modality_scope'] == ['CT']
            assert 2 in s['walkthrough_step_indices'] and s['requires_site_instantiation']
    assert {i for s in structures.values() for i in s['walkthrough_step_indices']} == set(range(5))
    assert {r['checklist_index'] for s in structures.values() for r in s['report_refs']} == set(range(5))


def test_five_native_label_names_do_not_substitute_for_drainage_or_extension_requirements():
    r = item()
    ids = {s['id'] for s in r['structures']}
    for side in ['left', 'right']:
        for name in ['frontal_sinus', 'sphenoid_sinus', 'posterior_ethmoid_cells', 'ethmoid_infundibulum', 'frontal_recess_and_ostium', 'pterygopalatine_fossa', 'V2_infraorbital_pterygopalatine_foramen_rotundum_route', 'cavernous_sinus_and_covered_carotid']:
            assert 'sinonasal.'+side+'_'+name in ids
    assert all(s['requires_site_instantiation'] for s in r['structures'])
    assert len(requirements_for(r)) == 800
    assert 'draft_requires' in r['clinical_validation_status']
    assert r['functional_evidence_requirements']

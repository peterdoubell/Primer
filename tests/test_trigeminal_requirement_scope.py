import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1];INV='ra.mri-trigeminal'
def item():return next(x for x in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if x['investigation_id']==INV)
def test_full_central_and_peripheral_routes_remain_in_scope():
    i=item();assert i['module_id']=='rad.5.trigeminal' and len(i['structures'])==112 and len(requirements_for(i))==672
    ids={x['id'] for x in i['structures']}
    for side in ['left','right']:
        for key in ['mesencephalic_nucleus_and_tract','principal_sensory_nucleus','motor_nucleus_and_fascicles','spinal_trigeminal_nucleus_and_tract','cisternal_sensory_root_and_rootlets','cisternal_motor_root_and_rootlets','motor_root_ganglion_bypass','V3_and_motor_foramen_ovale_course','superior_orbital_fissure','foramen_rotundum','foramen_ovale','lingual_and_encountered_connections','inferior_alveolar_and_mandibular_canal','tensor_veli_palatini_and_tensor_tympani_motor']:
            assert 'trigeminal.'+side+'_'+key in ids
    assert all(s['requires_site_instantiation'] and s['modality_scope']==['MRI'] for s in i['structures'])
    assert all(0<=r['checklist_index']<5 for s in i['structures'] for r in s['report_refs'])
def test_normality_clinical_diagnosis_and_function_are_not_inferred_from_geometry():
    r=detail(Curriculum(),resolve(INV))['radiology_reference'];w=r['walkthrough']
    assert all(s['normal']=={} for s in w['steps'])
    assert w['spatial_model']['family']=='trigeminal' and 'Partial pathway orientation' in w['spatial_model']['reporting_aim']
    assert 'motor root bypasses' in w['steps'][3]['tip']
    assert 'not the clinical diagnosis' in w['steps'][1]['tip']
    assert 'limited proximal MRI does not exclude distal disease' in w['steps'][4]['tip']
    assert 'microscopic perineural invasion' in ' '.join(item()['functional_evidence_requirements'])

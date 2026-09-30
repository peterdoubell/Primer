"""All report-required Gruen zones retain their projection-specific scope."""
from pathlib import Path
import copy,json
from tools.check_msk_fidelity import requirements_for,inspect_binding
ROOT=Path(__file__).resolve().parents[1]
def records():
 r=json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text());h=next(i for i in r['investigations'] if i['investigation_id']=='ra.hip-arthroplasty');return h,{x['id']:x for x in requirements_for(h)}
def test_all_fourteen_zones_are_required_without_removing_existing_parts():
 h,leaves=records();parent=next(x for x in h['structures'] if x['id']=='hip_arthroplasty.femoral_host_bone');before=json.loads((ROOT/'docs/msk-hip-arthroplasty-gruen-scope-proposal-2026-09-30.json').read_text())['preserve_existing_required_parts'];after={p['id']:p for p in parent['required_parts']}
 for old in before:
  for key,value in old.items():assert after[old['id']][key]==value
 for zone in range(1,15):
  target=leaves[parent['id']+'.gruen_zone_'+str(zone)]
  assert target['modality_scope']==['Radiography']
  assert target['context_requirements'][-1]['projection']==('anteroposterior' if zone<=7 else 'lateral')
 assert 'hip_arthroplasty.femoral_host_bone.stem_tip_adjacent_diaphysis' in leaves

def test_an_ap_or_unspecified_reference_cannot_satisfy_a_lateral_zone():
 _,leaves=records();target=leaves['hip_arthroplasty.femoral_host_bone.gruen_zone_14'];asset={'kind':'clinical_image','modality':'Radiography','source_context':{'projection':'anteroposterior'}}
 assert 'source_context_projection_mismatch' in inspect_binding(asset,target)
 asset['source_context']={};assert 'source_context_projection_unresolved' in inspect_binding(asset,target)
 asset['source_context']['projection']='lateral';assert not inspect_binding(asset,target)
 asset['source_context']['projection']='imagined';assert 'source_context_projection_invalid' in inspect_binding(asset,target)

def test_lateral_reference_cannot_be_relabelled_as_ap_zone():
 _,leaves=records();target=leaves['hip_arthroplasty.femoral_host_bone.gruen_zone_7'];asset={'kind':'schematic','source_context':{'projection':'lateral'}}
 assert 'source_context_projection_mismatch' in inspect_binding(asset,target)


def test_native_hip_reference_does_not_claim_implants_or_zonal_geometry():
 from primer.curriculum import Curriculum
 from primer.radiology_catalog import detail,resolve
 ref=detail(Curriculum(),resolve('ra.hip-arthroplasty'))['radiology_reference']
 assert ref['spatial_model']['family']=='hip'
 assert 'labrum' not in ref['spatial_model']['instructions'].lower()
 assert 'no Gruen-zone mapping' in ref['spatial_model']['population_note']
 assert 'does not depict the implanted' in ref['walkthrough']['spatial_model']['reporting_aim']
 assert 'labrum' not in ref['walkthrough']['spatial_model']['instructions'].lower()
 assert '8–14' in ref['walkthrough']['steps'][1]['look']
 figure=next(i for i in ref['key_images'] if i['id']=='ra-hip-arthroplasty-detail-2')
 assert figure['projection']=='anteroposterior' and 'not depicted' in figure['caption']

"""Reported accessory variants cannot borrow ordinary-muscle or other-variant anatomy."""
from pathlib import Path
import json
import pytest
from tools.check_msk_fidelity import requirements_for,inspect_binding
ROOT=Path(__file__).resolve().parents[1]
VARIANTS={'ankle.peroneus_quartus_muscle':'peroneus_quartus','ankle.accessory_soleus_muscle':'accessory_soleus','ankle.flexor_digitorum_accessorius_longus_muscle':'flexor_digitorum_accessorius_longus'}
def records():return json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text())
def test_additive_scope_preserves_all_original_named_structures_and_fields():
 req=records();proposal=json.loads((ROOT/'docs/msk-hip-aiis-ankle-accessory-scope-proposal-2026-09-30.json').read_text())
 for change in proposal['investigations']:
  item=next(i for i in req['investigations'] if i['investigation_id']==change['investigation_id']);ids={s['id'] for s in item['structures']};assert set(change['existing_named_structure_ids'])<=ids
  for new in change['append_structures']:assert new['id'] in ids
 hip=next(i for i in req['investigations'] if i['investigation_id']=='ra.hip-fai');parts={p['id'] for p in requirements_for(hip)}
 assert {'hip.anterior_inferior_iliac_spine.inferior_prominence','hip.anterior_inferior_iliac_spine.subspine_region'}<=parts
 ankle=next(i for i in req['investigations'] if i['investigation_id']=='ra.mri-ankle');assert set(VARIANTS)<=set(ankle['expansion_rules'][0]['named_sites_or_targets'])
 for structure in ankle['structures']:
  if structure['id'] in VARIANTS:assert 'when this variant is present/suspected' in structure['condition'] and 'within the actual MRI coverage' in structure['condition']
 assert sum(len(requirements_for(i))*3 for i in req['investigations'])==5292
@pytest.mark.parametrize('identifier,variant',VARIANTS.items())
def test_ordinary_or_wrong_variant_cannot_be_relabelled(identifier,variant):
 ankle=next(i for i in records()['investigations'] if i['investigation_id']=='ra.mri-ankle');target=next(r for r in requirements_for(ankle) if r['id']==identifier+'.muscle_belly')
 asset={'kind':'model','source_context':{'anatomical_variant':'none'}}
 assert 'source_context_anatomical_variant_mismatch' in inspect_binding(asset,target)
 asset['source_context']={};assert 'source_context_anatomical_variant_unresolved' in inspect_binding(asset,target)
 other=next(v for v in VARIANTS.values() if v!=variant);asset['source_context']['anatomical_variant']=other;assert 'source_context_anatomical_variant_mismatch' in inspect_binding(asset,target)
 asset['source_context']['anatomical_variant']=variant;assert not inspect_binding(asset,target)

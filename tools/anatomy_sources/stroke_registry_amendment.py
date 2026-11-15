"""Exact stroke-only in-memory restoration for immutable historical data guards.

No registry writes. Only independently reviewed current stroke values/ID tokens
may be removed/restored; every other semantic value and raw token is retained.
"""
import copy
import hashlib
import json
from pathlib import Path
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.integrate_myelopathy_sources import member,object_members
from tools.pulmonary_data_compatibility import restore_main_raw
ROOT=Path(__file__).resolve().parents[2]
AMENDMENT=ROOT/'docs/acute-stroke-source-review-20261011/stroke-registry-additive-amendment-20261011.json'
AMENDMENT_SHA256='c8e9d7ee4f023314e1a6e5901db2e9247694ea12b56339c5771c32043f961d36'
INVESTIGATION='ra.acute-stroke'
PREFIX='open-acute-stroke-ctp2023-fig'
CAPTION_AMENDMENT=ROOT/'docs/acute-stroke-source-review-20261011/source-caption-full-addition-amendment-20261011.json'
CAPTION_AMENDMENT_SHA256='bcba087d7928bbcac5f84656682a790c90fc2c2a1069846ff0c84e472919425c'
PATHS=(
 'data/radiology/radiology-open-images.json',
 'data/radiology/radiology-asset-evidence.json',
 'data/radiology/non-msk-structure-requirements.json',
 'data/radiology/reporting-steps/neuroradiology.json',
 'data/radiology/investigation-overrides-non-msk.json',
)

def sha(raw):return hashlib.sha256(raw).hexdigest()


def reviewed_amendment():
 raw=AMENDMENT.read_bytes()
 if sha(raw)!=AMENDMENT_SHA256:raise ValueError('Stroke additive amendment fingerprint changed')
 r=json.loads(raw)
 if (r.get('investigation_id')!=INVESTIGATION or set(r.get('files',{}))!=set(PATHS)
     or r.get('approved_image_ids')!=[PREFIX+str(i) for i in range(1,14)]
     or r.get('current_quiz_count')!=12 or r.get('named_group_count')!=369 or r.get('named_required_parts_floor')!=3692
     or any(r.get(k) is not False for k in ('clinical_approval','fine_anatomical_approval','structure_coverage_granted','native_ISLES_publication_approved','patient_specific_3D_approved'))):raise ValueError('Stroke amendment scope or approval changed')
 for path,expected in r['pinned_source_reviews_SHA256'].items():
  if sha((ROOT/path).read_bytes())!=expected:raise ValueError('Pinned original/source dependency changed: '+path)
 return caption_comparison_amendment(r)


def caption_comparison_amendment(original):
 """Repin only exact13 image-row caption additions; original review stays frozen."""
 raw=CAPTION_AMENDMENT.read_bytes()
 if sha(raw)!=CAPTION_AMENDMENT_SHA256:raise ValueError('Caption-only amendment fingerprint changed')
 c=json.loads(raw)
 if (c.get('investigation_id')!=INVESTIGATION or c.get('added_field')!='source_caption_full'
     or c.get('approved_image_ids')!=original['approved_image_ids'] or c.get('only_caption_field_added') is not True
     or c.get('source_pixels_or_original_caption_changed') is not False or c.get('current_quiz_changed') is not False
     or any(c.get(k) is not False for k in ('clinical_approval','fine_anatomical_approval','structure_coverage_granted','patient_specific_3D_approved'))):raise ValueError('Caption amendment leaves its reviewed scope')
 for path,expected in c['frozen_original_evidence_SHA256'].items():
  if sha((ROOT/path).read_bytes())!=expected:raise ValueError('Frozen caption source/dependency changed: '+path)
 for path,expected in [(c['primary_XML_path'],c['primary_XML_SHA256']),(c['current_data_receipt_path'],c['current_data_receipt_SHA256'])]:
  if sha((ROOT/path).read_bytes())!=expected:raise ValueError('Caption current source/receipt changed: '+path)
 if sha(restore_main_raw('data/curriculum/11-radiology.json',(ROOT/'data/curriculum/11-radiology.json').read_bytes()))!=c['current_quiz_file_SHA256']:raise ValueError('Frozen current quiz changed during caption repair')
 before,after=c['before_image_rows'],c['caption_complete_image_rows']
 if len(before)!=13 or len(after)!=13 or [r['id'] for r in after]!=original['approved_image_ids']:raise ValueError('Exact caption row selection changed')
 for a,b in zip(before,after):
  restored=copy.deepcopy(b)
  if restored.pop('source_caption_full',None)!=a.get('original_caption') or restored!=a:raise ValueError('Caption repair changed source text or other metadata')
 old_record=original['files'][PATHS[0]]
 if c['original_guard_image_record']!=old_record or digest(before)!=old_record['current_semantic_SHA256'] or c['before_collection_raw_value_token_SHA256']!=old_record['current_raw_value_token_SHA256']:raise ValueError('Caption amendment borrows a different original guard')
 record=c['caption_complete_guard_image_record'];check=copy.deepcopy(record);check['current_semantic_SHA256']=old_record['current_semantic_SHA256'];check['current_raw_value_token_SHA256']=old_record['current_raw_value_token_SHA256']
 if check!=old_record or record['current_semantic_SHA256']!=digest(after) or record['current_raw_value_token_SHA256']!=c['after_collection_raw_value_token_SHA256']:raise ValueError('Caption repair repins an unreviewed guard field')
 result=copy.deepcopy(original);result['files'][PATHS[0]]=copy.deepcopy(record)
 return result


def token_key(tokens,record):
 keys=[k for k in record['token_keys'] if k in tokens]
 if len(keys)!=1:raise ValueError('Stroke addition has missing or ambiguous raw value token namespace')
 return keys[0]


def require_exact(value,tokens,record):
 key=token_key(tokens,record)
 if digest(value)!=record['current_semantic_SHA256'] or tokens[key]!=record['current_raw_value_token_SHA256']:
  raise ValueError('Stroke addition differs from exact reviewed semantics or raw value token')
 return key


def restore_prior_view(path,data,tokens):
 """Restore only these five reviewed additions, without masking other changes."""
 path=str(path)
 if path not in PATHS:raise ValueError('Unreviewed historical stroke registry path')
 review=reviewed_amendment();record=review['files'][path];data=copy.deepcopy(data);tokens=dict(tokens)
 if path in (PATHS[0],PATHS[4]):
  value=data.get(INVESTIGATION);key=require_exact(value,tokens,record)
  if path==PATHS[0] and (len(value)!=13 or {r['id'] for r in value}!=set(review['approved_image_ids'])):raise ValueError('Stroke image selection changed')
  if record['prior_present']:raise ValueError('Unexpected pre-stroke member in additive scope')
  del data[INVESTIGATION];tokens.pop(key)
 elif path==PATHS[1]:
  expected={r['id']:r for r in record['added_assets']};rows=[r for r in data['assets'] if r['id'] in expected]
  if len(rows)!=13 or {r['id'] for r in rows}!=set(review['approved_image_ids']):raise ValueError('Stroke assets incomplete or duplicated')
  for r in rows:tokens.pop(require_exact(r,tokens,expected[r['id']]))
  data['assets']=[r for r in data['assets'] if r['id'] not in expected]
 elif path==PATHS[2]:
  rows=[r for r in data['investigations'] if r['investigation_id']==INVESTIGATION]
  if len(rows)!=1:raise ValueError('Stroke requirement addition incomplete or duplicated')
  key=require_exact(rows[0],tokens,record)
  if len(rows[0]['structures'])!=369:raise ValueError('Whole stroke requirement scope changed')
  ids=data['scope']['catalog_investigation_ids'];scope_record=record['scope_id'];scope_key=require_exact(INVESTIGATION,tokens,scope_record)
  if ids.count(INVESTIGATION)!=1:raise ValueError('Stroke catalogue scope ID incomplete or duplicated')
  data['investigations']=[r for r in data['investigations'] if r['investigation_id']!=INVESTIGATION]
  data['scope']['catalog_investigation_ids']=[i for i in ids if i!=INVESTIGATION];tokens.pop(key);tokens.pop(scope_key)
 else:
  key=require_exact(data['investigations'].get(INVESTIGATION),tokens,record);prior=record['prior_value']
  if digest(prior)!=record['prior_semantic_SHA256'] or sha(record['prior_raw_value_token'].encode())!=record['prior_raw_value_token_SHA256'] or json.loads(record['prior_raw_value_token'])!=prior:raise ValueError('Historical stroke walkthrough baseline changed')
  data['investigations'][INVESTIGATION]=copy.deepcopy(prior);tokens[key]=record['prior_raw_value_token_SHA256']
 return data,tokens


def restore_prior_step_raw(raw):
 """Replace only the exactly reviewed stroke value span with its original token."""
 from tools.hippunfold_runtime_compatibility import before_hippunfold_bytes
 raw=before_hippunfold_bytes(PATHS[3],raw.encode(),allow_older=True).decode()
 review=reviewed_amendment();record=review['files'][PATHS[3]];value,a,b=member(raw,['investigations',INVESTIGATION])
 if digest(value)!=record['current_semantic_SHA256'] or sha(raw[a:b].encode())!=record['current_raw_value_token_SHA256']:raise ValueError('Current stroke step value or raw token differs')
 old=record['prior_raw_value_token']
 if json.loads(old)!=record['prior_value'] or sha(old.encode())!=record['prior_raw_value_token_SHA256']:raise ValueError('Original stroke step token differs')
 return raw[:a]+old+raw[b:]

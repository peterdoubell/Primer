"""Exact additive comparison views retain every unrelated historical guard."""
import copy
import json
from pathlib import Path
import pytest
from tools.anatomy_sources import stroke_registry_amendment as bridge
from tools.anatomy_sources import integrate_acute_stroke_sources as current
from tools.anatomy_sources import integrate_myelopathy_sources as myelopathy
from tools.anatomy_sources import integrate_traumatic_haemorrhage_sources as trauma
from tools.anatomy_sources import traumatic_registry_amendment as old_format
ROOT=Path(__file__).resolve().parents[1]


def observations(path,style='trauma'):
 raw=(ROOT/path).read_text();data=json.loads(raw)
 tokens=trauma.unrelated_tokens(raw,Path(path),set()) if style=='trauma' else myelopathy.unrelated_token_fingerprints(raw,Path(path),set())
 return raw,data,tokens


def test_current_quiz_and_source_pins_allow_only_reviewed_CTP_stroke_view():
 r=bridge.reviewed_amendment();assert len(r['approved_image_ids'])==13
 assert r['current_quiz_count']==12 and r['named_group_count']==369 and r['named_required_parts_floor']==3692
 assert r['current_quiz_sha256']!=r['original_quiz_sha256']
 assert r['native_ISLES_publication_approved'] is False
 for path in bridge.PATHS:
  raw,data,tokens=observations(path);restored,old_tokens=bridge.restore_prior_view(path,data,tokens)
  assert data==json.loads(raw) # comparison never mutates caller data
  if path==bridge.PATHS[3]:assert restored['investigations'][bridge.INVESTIGATION]==r['files'][path]['prior_value']
  elif path in (bridge.PATHS[0],bridge.PATHS[4]):assert bridge.INVESTIGATION not in restored
  elif path==bridge.PATHS[1]:assert not any(v['id'].startswith(bridge.PREFIX) for v in restored['assets'])
  else:assert not any(v['investigation_id']==bridge.INVESTIGATION for v in restored['investigations'])


@pytest.mark.parametrize('style',['trauma','myelopathy'])
def test_both_real_historical_token_namespaces_restore_only_exact_stroke_values(style):
 r=bridge.reviewed_amendment()
 for path in bridge.PATHS[:4] if style=='myelopathy' else bridge.PATHS:
  raw,data,tokens=observations(path,style);restored,old=bridge.restore_prior_view(path,data,tokens)
  changed=set(tokens)^set(old)
  assert changed and all(bridge.INVESTIGATION in key or bridge.PREFIX in key for key in changed) if path!=bridge.PATHS[3] else old!=tokens
  assert all(old[k]==tokens[k] for k in set(old)&set(tokens) if bridge.INVESTIGATION not in k and bridge.PREFIX not in k)


@pytest.mark.parametrize('path,mutation',[
 (bridge.PATHS[0],'source_caption'),(bridge.PATHS[0],'extra_figure'),
 (bridge.PATHS[1],'anatomy_credit'),(bridge.PATHS[1],'cross_scope'),
 (bridge.PATHS[2],'clinical_credit'),(bridge.PATHS[2],'duplicate_scope'),(bridge.PATHS[2],'omitted_group'),
 (bridge.PATHS[3],'normal_finding'),(bridge.PATHS[4],'unknown_source'),
])
def test_modified_scoped_semantics_are_rejected(path,mutation):
 _,data,tokens=observations(path)
 if mutation=='source_caption':data[bridge.INVESTIGATION][0]['caption']+=' Invented source claim.'
 elif mutation=='extra_figure':data[bridge.INVESTIGATION].append(copy.deepcopy(data[bridge.INVESTIGATION][0]))
 elif mutation in ('anatomy_credit','cross_scope'):
  asset=next(a for a in data['assets'] if a['id'].startswith(bridge.PREFIX))
  if mutation=='anatomy_credit':asset['structure_ids']=['whole_brain']
  else:asset['investigation_ids']=['ra.mri-sella']
 elif mutation in ('clinical_credit','omitted_group'):
  item=next(i for i in data['investigations'] if i['investigation_id']==bridge.INVESTIGATION)
  if mutation=='clinical_credit':item['clinical_approval']=True
  else:item['structures'].pop()
 elif mutation=='duplicate_scope':data['scope']['catalog_investigation_ids'].append(bridge.INVESTIGATION)
 elif mutation=='normal_finding':data['investigations'][bridge.INVESTIGATION]['steps'][0]['normal']['BRAIN PARENCHYMA']='No infarct; ASPECTS10.'
 else:data[bridge.INVESTIGATION]['reading'].append({'id':'unreviewed','url':'https://example.org','title':'unreviewed'})
 with pytest.raises(ValueError):bridge.restore_prior_view(path,data,tokens)


@pytest.mark.parametrize('path',bridge.PATHS)
def test_changed_raw_tokens_without_changed_semantics_are_rejected(path):
 _,data,tokens=observations(path);r=bridge.reviewed_amendment()['files'][path]
 record=r['added_assets'][0] if path==bridge.PATHS[1] else r;key=next(k for k in record['token_keys'] if k in tokens);tokens[key]='0'*64
 with pytest.raises(ValueError,match='raw value token'):bridge.restore_prior_view(path,data,tokens)


def test_unreviewed_paths_and_ambiguous_token_namespaces_are_rejected():
 path=bridge.PATHS[0];_,data,tokens=observations(path)
 with pytest.raises(ValueError,match='Unreviewed'):bridge.restore_prior_view('data/radiology/unreviewed.json',data,tokens)
 tokens['image_collection:'+bridge.INVESTIGATION]=tokens[bridge.INVESTIGATION]
 with pytest.raises(ValueError,match='ambiguous'):bridge.restore_prior_view(path,data,tokens)


def test_unrelated_semantic_and_raw_drift_survives_bridge_for_old_guards_to_reject():
 path=bridge.PATHS[0];_,data,tokens=observations(path);other=next(k for k in data if k!=bridge.INVESTIGATION)
 data[other][0]['caption']+=' An unreviewed unrelated change.';tokens[other]='f'*64
 restored,old=bridge.restore_prior_view(path,data,tokens)
 assert restored[other][0]['caption'].endswith('An unreviewed unrelated change.') and old[other]=='f'*64
 assert restored[other]==data[other]


def test_original_canonical_trauma_format_gate_still_checks_all_actual_other_bytes():
 path=bridge.PATHS[3];raw,data,tokens=observations(path);restored=bridge.restore_prior_step_raw(raw)
 record=old_format.validate_format_amendment(raw=restored)
 assert bridge.sha(restored.encode())==record['after_raw_file_SHA256']
 assert json.loads(restored)['investigations'][bridge.INVESTIGATION]==bridge.reviewed_amendment()['files'][path]['prior_value']
 # An unrelated value change remains and fails the exact original format/semantic gate.
 other=next(k for k in data['investigations'] if k!=bridge.INVESTIGATION)
 bad=current.replace_member(raw,['investigations',other],{'steps':[]});view=bridge.restore_prior_step_raw(bad)
 with pytest.raises(ValueError,match='formatting differs'):old_format.validate_format_amendment(raw=view)
 # Whitespace in the scoped current value is not silently normalised as reviewed.
 _,a,b=current.member(raw,['investigations',bridge.INVESTIGATION]);bad=raw[:a]+json.dumps(data['investigations'][bridge.INVESTIGATION])+raw[b:]
 with pytest.raises(ValueError,match='raw token'):bridge.restore_prior_step_raw(bad)

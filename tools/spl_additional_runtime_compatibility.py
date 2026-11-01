"""Bounded historical projection for the additional94 source reference."""
from pathlib import Path
import copy
import hashlib
import json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/spl-additional-source-review-20261101/runtime-inverse.json'
PROOF_SHA256='b80ab178bba389cefa6e3a4c310115b62de75989de6c10cadd6060f43793c7e1'
PATHS=frozenset(['.vercelignore','primer/server.py','primer/source_native_inspectors.py','web/app.js','tools/spl_epilepsy_runtime_compatibility.py','tests/test_spl_epilepsy_context.py','tools/hippocampal_rater_runtime_compatibility.py','tests/test_pulmonary_source_delivery.py','tools/check_pulmonary_delivery.py','docs/radiology-fidelity-scope.json','vercel.json'])
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def reviewed():
 raw=(ROOT/PROOF).read_bytes()
 if sha(raw)!=PROOF_SHA256:raise ValueError('Additional SPL inverse evidence changed')
 p=json.loads(raw)
 if p['base_commit']!='69c1b1e8fed3c3edb891f84cedc93a4d4f7eca3d' or p['scope']!='exact_additional_94_source_classes' or set(p['files'])!=PATHS or p['bindings']!=['ra.brain-anatomy','ra.mri-sella','ra.mri-neck-spaces'] or set(p['lessons'])!={'rad.5.sella','rad.5.deep-neck-spaces'} or p['inspector']['id']!='spl-additional-native-source-reference' or any(p[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Additional SPL inverse scope differs')
 return p

def before_additional_bytes(path,raw,allow_older=False):
 path=str(path)
 if path not in PATHS:return raw
 row=reviewed()['files'][path]
 if sha(raw)==row['before_sha256']:return raw
 if sha(raw)!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed additional SPL byte change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Additional SPL inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if sha(restored)!=row['before_sha256']:raise ValueError('Additional SPL inverse changed unrelated bytes')
 return restored

def before_additional_fields(identifier,fields):
 p=reviewed();result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);addition=p['inspector'];matches=[item for item in items if item.get('id')==addition['id']]
 if not matches:return result
 if identifier not in p['bindings']or matches!=[addition]:raise ValueError('Unreviewed additional SPL descriptor')
 items.remove(matches[0]);return result


def before_additional_bindings(bindings):
 result={}
 for identifier,items in bindings.items():
  restored=before_additional_fields(identifier,{'source_native_inspectors':items})['source_native_inspectors']
  if restored or identifier not in ['ra.mri-sella','ra.mri-neck-spaces']:result[identifier]=restored
 return result


def before_additional_lesson_fields(identifier,fields):
 p=reviewed();result=copy.deepcopy(fields)
 if identifier not in p['lessons']:return result
 row=p['lessons'][identifier];items=result.get('lesson_media',[])
 before=row['fields']['lesson_media']['before'];after=row['fields']['lesson_media']['after']
 additions=[item for item in after if item not in before]
 if len(additions)!=1 or [item for item in after if item not in additions]!=before or additions[0]['kind']!='source-native-inspectors':raise ValueError('Additional SPL lesson evidence differs')
 addition=additions[0];matches=[item for item in items if item.get('id')==addition['id']]
 if not matches:return result
 if matches!=[addition]:raise ValueError('Unreviewed additional SPL lesson wrapper')
 items.remove(matches[0]);return result

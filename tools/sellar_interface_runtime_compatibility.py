"""Exact historical projection for sellar interfaces and static CT byte identities."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/sellar-source-interfaces-review-20261101/runtime-inverse.json'
PROOF_SHA256='718792fc8c0d6a288ea2d348ad13a473deff0abc055fd682a25615e87335eff8'
PATHS=frozenset(['.vercelignore','vercel.json','primer/server.py','primer/source_native_inspectors.py','primer/source_volume_integrity.py','data/radiology/radiology-static-source-volumes.json','web/app.js','docs/radiology-fidelity-scope.json','tools/spl_additional_runtime_compatibility.py','tests/test_spl_additional_reference.py'])
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def reviewed():
 raw=(ROOT/PROOF).read_bytes()
 if sha(raw)!=PROOF_SHA256:raise ValueError('Sellar interface inverse evidence changed')
 data=json.loads(raw)
 if data['base_commit']!='994775ae4617573b300fcd71bd04399f7582314e'or set(data['files'])!=PATHS or data['bindings']!=['ra.brain-anatomy','ra.mri-sella']or data['inspector']['id']!='spl-sellar-source-interfaces-reference'or any(data[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Sellar inverse scope differs')
 return data

def before_interfaces_bytes(path,raw,allow_older=False):
 path=str(path)
 if path not in PATHS:return raw
 row=reviewed()['files'][path]
 if sha(raw)==row['before_sha256']:return raw
 if sha(raw)!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed sellar interface byte change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Sellar inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if sha(restored)!=row['before_sha256']:raise ValueError('Sellar inverse changed unrelated bytes')
 return restored

def before_interfaces_fields(identifier,fields):
 proof=reviewed();result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);addition=proof['inspector'];matches=[r for r in items if r.get('id')==addition['id']]
 if not matches:return result
 if identifier not in proof['bindings']or matches!=[addition]:raise ValueError('Unreviewed sellar source descriptor')
 items.remove(matches[0]);return result

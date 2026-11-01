"""Exact historical projection for the processed pituitary case."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/pituitary-case-source-review-20261101/runtime-inverse.json'
PROOF_SHA256='0124c4a2516d0ee832595d4003edc267904226810b168b6fae9179a9cbe83373'
PATHS=frozenset(['.vercelignore','primer/server.py','primer/source_native_inspectors.py','web/app.js','docs/radiology-fidelity-scope.json','tools/sellar_interface_runtime_compatibility.py','tests/test_sellar_interface_runtime.py'])
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def reviewed():
 raw=(ROOT/PROOF).read_bytes()
 if sha(raw)!=PROOF_SHA256:raise ValueError('Pituitary case inverse evidence changed')
 data=json.loads(raw)
 if data['base_commit']!='ce3ef51494c0c055cdffd4d6ded9acb1e0479126'or set(data['files'])!=PATHS or data['bindings']!=['ra.mri-sella']or data['inspector']['id']!='pandit-pituitary-case1-processed-reference'or any(data[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Sellar inverse scope differs')
 return data

def before_pituitary_bytes(path,raw,allow_older=False):
 path=str(path)
 if path not in PATHS:return raw
 row=reviewed()['files'][path]
 if sha(raw)==row['before_sha256']:return raw
 if sha(raw)!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed pituitary case byte change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Sellar inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if sha(restored)!=row['before_sha256']:raise ValueError('Sellar inverse changed unrelated bytes')
 return restored

def before_pituitary_fields(identifier,fields):
 proof=reviewed();result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);addition=proof['inspector'];matches=[r for r in items if r.get('id')==addition['id']]
 if not matches:return result
 if identifier not in proof['bindings']or matches!=[addition]:raise ValueError('Unreviewed pituitary source descriptor')
 items.remove(matches[0]);return result

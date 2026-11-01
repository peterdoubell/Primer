"""Exact temporal/ventricular context reversal; historical scope stays bounded."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/epilepsy-source-context-review-20261101/runtime-inverse.json'
PROOF_SHA256='f7ee45c4e676e8df9f6349dd5ab0fcf5136474050ccd18a0cc2eec6ac2e37cf5'
PATHS=frozenset(['.vercelignore','data/radiology/spl-reporting-reference.json','docs/radiology-fidelity-scope.json','primer/server.py','primer/source_native_inspectors.py','primer/spl_reporting_reference.py','web/anatomy/spl-nac-reporting/viewer.js','web/app.js','tools/cortical_mri_runtime_compatibility.py','tools/cortical_contact_runtime_compatibility.py','tools/spl_reporting_runtime_compatibility.py'])
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def reviewed():
 raw=(ROOT/PROOF).read_bytes()
 if sha(raw)!=PROOF_SHA256:raise ValueError('Epilepsy context inverse evidence changed')
 p=json.loads(raw)
 if p['base_commit']!='bcac80df81b4dee23b4d62cc1c98c5d0dfadd496'or p['scope']!='exact_epilepsy_temporal_ventricular_source_context'or set(p['files'])!=PATHS or p['bindings']!=['ra.mri-epilepsy']or p['inspector']['id']!='spl-epilepsy-temporal-ventricular-source-context'or any(p[k]is not False for k in ['sourcePayloadsChanged','clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Epilepsy context inverse scope differs')
 return p

def before_context_bytes(path,raw,allow_older=False):
 path=str(path)
 if path not in PATHS:return raw
 row=reviewed()['files'][path]
 if sha(raw)==row['before_sha256']:return raw
 if sha(raw)!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed epilepsy context byte change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Epilepsy context inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if sha(restored)!=row['before_sha256']:raise ValueError('Epilepsy context inverse changed unrelated bytes')
 return restored

def before_context_fields(identifier,fields):
 p=reviewed();result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);addition=p['inspector'];matches=[item for item in items if item.get('id')==addition['id']]
 if not matches:return result
 if identifier not in p['bindings']or matches!=[addition]:raise ValueError('Unreviewed epilepsy source context descriptor')
 items.remove(matches[0]);return result

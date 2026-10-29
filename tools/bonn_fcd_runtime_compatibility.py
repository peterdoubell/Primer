"""Exact historical projection; new source evidence is validated separately."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/fcd-native-source-review-20261028/runtime-inverse.json'
PROOF_SHA256='7054fc71a5ba99e8e9b7bef652d0acbb40cb47ca5a239ed70bf98ee9427fed82'
PATHS=frozenset(['docs/radiology-fidelity-scope.json','primer/server.py','primer/source_native_inspectors.py','web/app.js'])
BASE='333d4819aa600304dd087cf6a6bb85802fc97e90'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('FCD integration evidence changed')
    data=json.loads(raw)
    if (data['base_commit']!=BASE or data['scope']!='exact_bonn_fcd_reference_integration'
        or set(data['files'])!=PATHS or data['bindings']!=['ra.mri-epilepsy'] or data['lesson']!='rad.5.epilepsy-mri'
        or data['inspector']['id']!='bonn-fcd-case4-native-reference'
        or any(data[k]is not False for k in ['clinical_approval','extends_historical_approval','whole_goal_complete'])):
        raise ValueError('FCD inverse leaves its reviewed scope')
    return data

def before_fcd_bytes(path,raw,allow_older=False):
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed fcd integration byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('FCD inverse literal differs')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('FCD inverse changed unrelated bytes')
    return restored

def before_fcd_reference_fields(identifier,fields):
    result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);addition=reviewed()['inspector'];matches=[r for r in items if r.get('id')==addition['id']]
    if not matches:return result
    if identifier!='ra.mri-epilepsy' or matches!=[addition]:raise ValueError('Unreviewed fcd descriptor')
    items.remove(matches[0]);return result


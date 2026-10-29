"""Exact historical projection; new source evidence is validated separately."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/hippocampal-rater-review-20261028/runtime-inverse.json'
PROOF_SHA256='0ee6fbf5d66b17749e2e2700d7e22ace710686af99a164eb84bbfa65f1db5d85'
PATHS=frozenset(['docs/radiology-fidelity-scope.json','primer/module_media.py','primer/server.py','primer/source_native_inspectors.py','web/app.js'])
BASE='ba86c0671693da95e9906f2bca5b6252376122e4'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Hippocampal integration evidence changed')
    data=json.loads(raw)
    if (data['base_commit']!=BASE or data['scope']!='exact_hippocampal_rater_reference_integration'
        or set(data['files'])!=PATHS or data['bindings']!=['ra.mri-epilepsy'] or data['lesson']!='rad.5.epilepsy-mri'
        or data['inspector']['id']!='dryad-hippocampal-case10-rater-reference'
        or any(data[k]is not False for k in ['clinical_approval','extends_historical_approval','whole_goal_complete'])):
        raise ValueError('Hippocampal inverse leaves its reviewed scope')
    return data

def before_hippocampal_bytes(path,raw,allow_older=False):
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed hippocampal integration byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Hippocampal inverse literal differs')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('Hippocampal inverse changed unrelated bytes')
    return restored

def before_hippocampal_reference_fields(identifier,fields):
    result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);addition=reviewed()['inspector'];matches=[r for r in items if r.get('id')==addition['id']]
    if not matches:return result
    if identifier!='ra.mri-epilepsy' or matches!=[addition]:raise ValueError('Unreviewed hippocampal descriptor')
    items.remove(matches[0]);return result

def before_hippocampal_lesson_fields(identifier,fields):
    if identifier!='rad.5.epilepsy-mri':return fields
    row=reviewed()['lessonWrapper'];result=copy.deepcopy(fields);items=result.get('lesson_media',[]);matches=[r for r in items if r.get('id')==row['after']['id']]
    if not matches or matches==[row['before']]:return result
    if matches!=[row['after']]:
        from tools.spl_limbic_runtime_compatibility import reviewed as spl_reviewed
        if matches==[spl_reviewed()['lessons'][identifier]['before']]:return result
        raise ValueError('Unreviewed hippocampal lesson wrapper')
    items[items.index(matches[0])]=copy.deepcopy(row['before']);return result

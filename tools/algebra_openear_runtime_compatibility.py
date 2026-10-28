"""Exact prior views for historical evidence; no approval transfers to new work."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE_COMMIT='e2d2003d22f0e8516d9066ab15fc9ac5346c795d'
PROOF='docs/algebra-openear-integration-review-20261027/runtime-inverse.json'
PROOF_SHA256='6b4220a855c1a84e0caed36b652beab575050d9070a605cbf4b338cf7fd38040'
PATHS=frozenset(['data/curriculum/01-mathematics.json', 'data/module-models.json', 'data/radiology/nextbrain-reference.json', 'docs/radiology-fidelity-scope.json', 'primer/curriculum.py', 'primer/module_media.py', 'primer/nextbrain_reference.py', 'primer/server.py', 'primer/source_native_inspectors.py', 'web/anatomy/nextbrain/viewer.js', 'web/app.js', 'web/index.html', 'web/lesson-models.js', 'web/lesson-state.js', 'web/spatial-module-objects.js'])
FLAGS=('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Algebra/OpenEar inverse evidence changed')
    d=json.loads(raw)
    if (d['base_commit']!=BASE_COMMIT or d['scope']!='exact_algebra_openear_and_native_context_recovery'
        or set(d['files'])!=PATHS or d['bindings']!=['ra.ct-temporal-bone','ra.tinnitus']
        or set(d['lessons'])!={'rad.5.temporal-bone','rad.5.tinnitus'}
        or any(d.get(k)is not False for k in ['clinical_approval','extends_historical_approval','whole_goal_complete'])
        or d['added_inspector']['id']!='openear-zeta-native-reference'
        or any(d['added_inspector'].get(k)is not False for k in FLAGS)):
        raise ValueError('Algebra/OpenEar inverse leaves its reviewed scope')
    return d

def before_algebra_openear_bytes(path,raw,allow_older=False):
    from tools.coordinate_plane_runtime_compatibility import before_coordinate_plane_bytes
    raw = before_coordinate_plane_bytes(path, raw, allow_older=True)
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed algebra/OpenEar integration byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Algebra/OpenEar inverse literal differs')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('Algebra/OpenEar inverse changes unrelated bytes')
    return restored

def before_algebra_openear_reference_fields(identifier,fields):
    result=copy.deepcopy(fields);items=result.get('source_native_inspectors')or[]
    matches=[r for r in items if r.get('id')=='openear-zeta-native-reference']
    if not matches:return result
    d=reviewed()
    if identifier not in d['bindings']or matches!=[d['added_inspector']]:raise ValueError('Unreviewed OpenEar descriptor')
    items.remove(matches[0])
    if not items:result.pop('source_native_inspectors',None)
    return result

def before_algebra_openear_lesson_fields(identifier,fields):
    d=reviewed()
    if identifier not in d['lessons']:return fields
    result=copy.deepcopy(fields);items=result.get('lesson_media',[]);addition=d['lessons'][identifier]['added_media']
    matches=[r for r in items if r.get('id')==addition['id']]
    if not matches:return result
    if matches!=[addition]:raise ValueError('Unreviewed OpenEar lesson wrapper')
    items.remove(matches[0]);return result

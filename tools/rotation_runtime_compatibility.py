"""Exact byte projection for the calibrated rotation lesson; no approval transfer."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/physics-rotation-review-20261102/runtime-inverse.json'
PROOF_SHA256='4d67f5aaaf38d50f4de41a83a469273efd84b8f5e528ccaa61af4eb15ce6607c'
PATHS=frozenset(['data/curriculum/03-physics.json', 'data/module-models.json', 'tools/check_module_models.js', 'tools/check_spatial_models.js', 'web/index.html', 'web/lesson-models.js', 'web/spatial-models.js', 'web/spatial-module-objects.js', 'tools/cavernous_photo_runtime_compatibility.py', 'tests/test_api.py', 'tests/test_circuits_lesson_integration.py', 'tests/test_hosted_safety.py', 'tests/test_module_models.py', 'tools/check_cross_subject_models.js', 'primer/curriculum.py', 'tests/test_primer.py', 'tools/check_physics_models.js', 'tests/test_linear_algebra_integration.py'])
sha=lambda b:hashlib.sha256(b).hexdigest()
def reviewed():
 raw=(ROOT/PROOF).read_bytes()
 if sha(raw)!=PROOF_SHA256:raise ValueError('Rotation inverse evidence changed')
 data=json.loads(raw)
 if data['base_commit']!='a245d6da5f6ad62f461a1347d5c20052bc451bcf' or data['lesson']!='phys.5.frontier'or set(data['files'])!=PATHS or any(data[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Rotation inverse scope differs')
 return data

def before_rotation_bytes(path,raw,allow_older=False):
 from tools.condensed_runtime_compatibility import before_condensed_bytes
 raw=before_condensed_bytes(path,raw,allow_older=True)
 path=str(path)
 if path not in PATHS:return raw
 row=reviewed()['files'][path]
 if sha(raw)==row['before_sha256']:return raw
 if sha(raw)!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed rotation byte change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Rotation inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if sha(restored)!=row['before_sha256']:raise ValueError('Rotation inverse changed unrelated bytes')
 return restored

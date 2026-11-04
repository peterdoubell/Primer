"""Exact byte projection for the calibrated transition lesson; no approval transfer."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/physics-condensed-review-20261102/runtime-inverse.json'
PROOF_SHA256='870a8de67d024c54d42ee1e2fe5db9620fe71f1d9c3942214168c0ee3c85e42b'
PATHS=frozenset(['data/curriculum/03-physics.json', 'data/module-models.json', 'primer/curriculum.py', 'tests/test_api.py', 'tests/test_hosted_safety.py', 'tests/test_module_models.py', 'tests/test_primer.py', 'tests/test_linear_algebra_integration.py', 'tests/test_rotation_lesson.py', 'tools/check_cross_subject_models.js', 'tools/check_module_models.js', 'tools/check_physics_models.js', 'tools/check_spatial_models.js', 'web/index.html', 'web/lesson-models.js', 'web/spatial-module-objects.js', 'tools/rotation_runtime_compatibility.py'])
sha=lambda b:hashlib.sha256(b).hexdigest()
def reviewed():
 raw=(ROOT/PROOF).read_bytes()
 if sha(raw)!=PROOF_SHA256:raise ValueError('Condensed inverse evidence changed')
 data=json.loads(raw)
 if data['base_commit']!='c37a84cc8626688b4970be58863d034d2bce0714' or data['lesson']!='phys.5.condensed'or set(data['files'])!=PATHS or any(data[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Condensed inverse scope differs')
 return data

def before_condensed_bytes(path,raw,allow_older=False):
 from tools.particle_runtime_compatibility import before_particle_bytes
 raw=before_particle_bytes(path,raw,allow_older=True)
 path=str(path)
 if path not in PATHS:return raw
 row=reviewed()['files'][path]
 if sha(raw)==row['before_sha256']:return raw
 if sha(raw)!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed rotation byte change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Condensed inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if sha(restored)!=row['before_sha256']:raise ValueError('Condensed inverse changed unrelated bytes')
 return restored

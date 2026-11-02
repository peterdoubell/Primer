"""Exact restoration of pre-particle bytes, solely for historical evidence checks.

This projection grants no clinical approval and does not replace current runtime
verification. Unknown bytes in a reviewed path are rejected by default.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/physics-particle-review-20261102/runtime-inverse.json'
PROOF_SHA256='a62763aff4345ff972e2e46e2d5a060dedae2f66772a8d0e138e526fabbd6c73'
PATHS=frozenset(['data/curriculum/03-physics.json','primer/curriculum.py','tests/test_condensed_lesson.py','tests/test_primer.py','tests/test_linear_algebra_integration.py','tools/check_physics_models.js','tools/condensed_runtime_compatibility.py','web/index.html','web/app.js','web/lesson-models.js'])
sha=lambda b:hashlib.sha256(b).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Particle inverse evidence changed')
    data=json.loads(raw)
    if (data['base_commit']!='086e516b2a4a6616ce87acceb086f6365efd993e'
        or data['lesson']!='phys.4.particles' or set(data['files'])!=PATHS
        or any(data[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete'])):
        raise ValueError('Particle inverse scope differs')
    return data

def before_particle_bytes(path,raw,allow_older=False):
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed particle byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:
            raise ValueError('Particle inverse literal differs')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('Particle inverse changed unrelated bytes')
    return restored

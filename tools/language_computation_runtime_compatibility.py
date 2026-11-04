"""Exact prior-source projection for historical checks; no approval transfer."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/language-computation-review-20261104/runtime-inverse.json'
PROOF_SHA256='5d2dc6cf749190957da4df90116b033b13b1ae0f7a349a201f9af5946a4c3518'
PATHS=frozenset(['data/curriculum/02-language.json','primer/curriculum.py','tests/test_api.py','tests/test_hosted_safety.py','tests/test_primer.py','tests/test_particle_lesson.py','tools/check_remaining_models.js','tools/check_spatial_models.js','tools/check_cross_subject_models.js','tools/particle_runtime_compatibility.py','web/index.html','web/lesson-models.js'])
sha=lambda b:hashlib.sha256(b).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Language computation inverse evidence changed')
    data=json.loads(raw)
    if(data['base_commit']!='1745be69605caec443708330884b0d7db34440b8'
       or data['lesson']!='lang.5.comp-ling' or set(data['files'])!=PATHS
       or any(data[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete'])):
        raise ValueError('Language computation inverse scope differs')
    return data

def before_language_computation_bytes(path,raw,allow_older=False):
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed language computation byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Language inverse literal differs')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('Language inverse changed unrelated bytes')
    return restored

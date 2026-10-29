"""Exact vector activity delta; historical evidence remains historical."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/vector-components-review-20261029/runtime-inverse.json'
PROOF_SHA256='1219b93c318c43e29c3c22a3e5326bc76ba7cfe7b9e9122c6356d7c5c0815cf3'
PATHS=frozenset(['data/curriculum/01-mathematics.json', 'primer/curriculum.py', 'primer/server.py', 'web/index.html', 'web/lesson-models.js'])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Vector inverse evidence changed')
    data=json.loads(raw)
    if data['base_commit']!='054efd15b86ab93a1f31b48fa95ca9fc88dd504a' or data['scope']!='exact_vector_components_integration' or data['lesson']!='math.3.vectors' or set(data['files'])!=PATHS or data['extends_historical_approval'] is not False or data['whole_goal_complete'] is not False:raise ValueError('Vector inverse scope changed')
    return data
def before_vector_components_bytes(path,raw,allow_older=False):
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed vector activity byte change')
    lines=raw.decode().splitlines(keepends=True)
    for c in reversed(row['changes']):
        if ''.join(lines[c['start']:c['end']])!=c['after']:raise ValueError('Vector inverse literal differs')
        lines[c['start']:c['end']]=c['before'].splitlines(keepends=True)
    result=''.join(lines).encode()
    if sha(result)!=row['before_sha256']:raise ValueError('Vector inverse changed unrelated bytes')
    return result

"""Exact geometry activity delta; historical evidence remains historical."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/geometry-measures-review-20261029/runtime-inverse.json'
PROOF_SHA256='88e7a656caaaa0c2906defaf84b565fcb1aad9ba348818d4db8da64d3bc76351'
PATHS=frozenset(['data/curriculum/01-mathematics.json', 'primer/curriculum.py', 'primer/server.py', 'web/index.html', 'web/lesson-models.js'])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Geometry inverse evidence changed')
    data=json.loads(raw)
    if data['base_commit']!='9a4e5ebfc78a9db7d2639a0324e962fda5966072' or data['scope']!='exact_geometry_measures_integration' or data['lesson']!='math.2.geometry' or set(data['files'])!=PATHS or data['extends_historical_approval'] is not False or data['whole_goal_complete'] is not False:raise ValueError('Geometry inverse scope changed')
    return data
def before_geometry_measures_bytes(path,raw,allow_older=False):
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed geometry activity byte change')
    lines=raw.decode().splitlines(keepends=True)
    for c in reversed(row['changes']):
        if ''.join(lines[c['start']:c['end']])!=c['after']:raise ValueError('Geometry inverse literal differs')
        lines[c['start']:c['end']]=c['before'].splitlines(keepends=True)
    result=''.join(lines).encode()
    if sha(result)!=row['before_sha256']:raise ValueError('Geometry inverse changed unrelated bytes')
    return result

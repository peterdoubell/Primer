"""Exact unmarked comparison delta; prior source proofs retain their original scope."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/epilepsy-structure-coverage-20261030/runtime-inverse.json'
PROOF_SHA256='4f2d3f752b0d099173dca028f825dfa9a3dfa9ece3bc450fad0768cb53e22bb8'
PATHS=frozenset(['data/radiology/spl-limbic-reference.json', 'primer/spl_limbic_reference.py', 'web/anatomy/spl-nac-limbic/index.html', 'web/anatomy/spl-nac-limbic/viewer.css', 'web/anatomy/spl-nac-limbic/viewer.js', 'docs/radiology-fidelity-scope.json'])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Comparison inverse evidence changed')
    p=json.loads(raw)
    if p['base_commit']!='9a940214cb5aeff900710e45ccbf28d1acb4b597' or p['scope']!='exact_spl_unmarked_comparison' or set(p['files'])!=PATHS or p['bindings']!=['ra.brain-anatomy','ra.mri-dementia','ra.mri-epilepsy'] or any(p[k]is not False for k in ['sourcePayloadsChanged','sourceManifestChanged','clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Comparison inverse scope differs')
    return p
def before_unmarked_bytes(path,raw,allow_older=False):
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed unmarked comparison byte change')
    lines=raw.decode().splitlines(keepends=True)
    for c in reversed(row['changes']):
        if ''.join(lines[c['start']:c['end']])!=c['after']:raise ValueError('Comparison inverse literal differs')
        lines[c['start']:c['end']]=c['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('Comparison inverse altered unrelated bytes')
    return restored
def before_unmarked_reference_fields(identifier,fields):
    p=reviewed();result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);row=p['descriptor'];matches=[x for x in items if x.get('id')==row['after']['id']]
    if not matches:return result
    if identifier not in p['bindings'] or matches not in [[row['before']],[row['after']]]:raise ValueError('Unreviewed SPL source comparison descriptor')
    items[items.index(matches[0])]=copy.deepcopy(row['before']);return result

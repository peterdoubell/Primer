"""Exact contact-reference integration; earlier evidence retains its original scope."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/cortical-source-contacts-review-20261101/runtime-inverse.json'
PROOF_SHA256='940c800589fd89dd2ef3da1e9dfd6d15d6cdacb1c061773672f1d953801fa3a2'
PATHS=frozenset(['primer/server.py', 'primer/source_native_inspectors.py', 'web/app.js', 'docs/radiology-fidelity-scope.json'])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('Contact inverse evidence changed')
    p=json.loads(raw)
    if p['base_commit']!='9eefed98a433128b1a800759dfea4fd97c27168e' or p['scope']!='exact_cortical_contact_reference_integration' or set(p['files'])!=PATHS or p['bindings']!=['ra.brain-anatomy','ra.mri-epilepsy'] or p['inspector']['id']!='spl-cortical-source-contacts-reference' or any(p[k]is not False for k in ['clinicalApproval','extendsHistoricalApproval','wholeGoalComplete']):raise ValueError('Contact inverse scope differs')
    return p
def before_contact_bytes(path,raw,allow_older=False):
    from tools.spl_epilepsy_runtime_compatibility import before_context_bytes
    raw=before_context_bytes(path,raw,allow_older=True)
    from tools.cortical_mri_runtime_compatibility import before_mri_bytes
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    raw=before_mri_bytes(path,raw,allow_older=allow_older)
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed contact integration byte change')
    lines=raw.decode().splitlines(keepends=True)
    for c in reversed(row['changes']):
        if ''.join(lines[c['start']:c['end']])!=c['after']:raise ValueError('Contact inverse literal differs')
        lines[c['start']:c['end']]=c['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('Contact inverse altered unrelated bytes')
    return restored
def before_contact_reference_fields(identifier,fields):
    from tools.spl_epilepsy_runtime_compatibility import before_context_fields
    fields=before_context_fields(identifier,fields)
    from tools.cortical_mri_runtime_compatibility import before_mri_reference_fields
    fields=before_mri_reference_fields(identifier,fields)
    p=reviewed();result=copy.deepcopy(fields);items=result.get('source_native_inspectors',[]);addition=p['inspector'];matches=[x for x in items if x.get('id')==addition['id']]
    if not matches:return result
    if identifier not in p['bindings'] or matches!=[addition]:raise ValueError('Unreviewed contact descriptor')
    items.remove(matches[0]);return result

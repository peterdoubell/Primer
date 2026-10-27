"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '235c55832e2a738c4683fb8a85ce955339380e4e'
PROOF = 'docs/schirmer-vascular-review-20261026/runtime-inverse.json'
PROOF_SHA256 = '3d6e806ebd2a8293d7083081614f0ac22f13a5384496843591623f58cbdf8921'
PATHS = frozenset(['.vercelignore', 'docs/radiology-fidelity-scope.json', 'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Vascular template inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_vascular_template_reference_integration'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Vascular template inverse leaves exact scope')
    item=proof['added_inspector']
    if proof['bindings']!=['ra.brain-anatomy','ra.acute-stroke'] or item.get('id')!='schirmer-vascular-template-reference' or any(item.get(k)is not False for k in ('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')):
        raise ValueError('Vascular template inverse changes interpretation scope')
    return proof


def before_schirmer_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The historical caller must check its own exact fingerprint.
        raise ValueError('Unreviewed current labs byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Vascular template inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Vascular template inverse changes unrelated baseline bytes')
    return restored


def before_schirmer_reference_fields(identifier, fields):
    import copy
    result=copy.deepcopy(fields)
    items=result.get('source_native_inspectors',[])
    matches=[row for row in items if row.get('id')=='schirmer-vascular-template-reference']
    if not matches:
        return result
    proof=reviewed()
    if identifier not in proof['bindings'] or matches!=[proof['added_inspector']]:
        raise ValueError('Unreviewed vascular template descriptor')
    items.remove(matches[0])
    return result

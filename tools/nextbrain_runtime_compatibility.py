"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '6bc3731b702f6a41e6c2078ce298a2d091178f88'
PROOF = 'docs/nextbrain-reader-review-20261027/runtime-inverse.json'
PROOF_SHA256 = '328fd9478fb208629e40ea5e77de66eecc99edd9595aa1f878dc4a72e14982d9'
PATHS = frozenset(['primer/server.py', 'primer/source_native_inspectors.py', 'web/app.js', 'docs/radiology-fidelity-scope.json'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('NextBrain inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_nextbrain_reference_integration'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('NextBrain inverse leaves exact scope')
    item=proof['added_inspector']
    if proof['bindings']!=['ra.brain-anatomy'] or item.get('id')!='nextbrain-exvivo-reference' or any(item.get(k)is not False for k in ('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')):
        raise ValueError('NextBrain inverse changes interpretation scope')
    return proof


def before_nextbrain_bytes(path, raw, allow_older=False):
    from tools.algebra_openear_runtime_compatibility import before_algebra_openear_bytes
    raw = before_algebra_openear_bytes(path, raw, allow_older=True)
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
            raise ValueError('NextBrain inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('NextBrain inverse changes unrelated baseline bytes')
    return restored


def before_nextbrain_reference_fields(identifier, fields):
    from tools.algebra_openear_runtime_compatibility import before_algebra_openear_reference_fields
    fields = before_algebra_openear_reference_fields(identifier, fields)
    import copy
    result=copy.deepcopy(fields)
    items=result.get('source_native_inspectors',[])
    matches=[row for row in items if row.get('id')=='nextbrain-exvivo-reference']
    if not matches:
        return result
    proof=reviewed()
    if identifier not in proof['bindings'] or matches!=[proof['added_inspector']]:
        raise ValueError('Unreviewed NextBrain descriptor')
    items.remove(matches[0])
    return result

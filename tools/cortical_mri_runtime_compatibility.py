"""Recover only the exact pre-MRI runtime for historical contact evidence."""
from pathlib import Path
import copy
import hashlib
import json
ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/cortical-native-mri-review-20261101/runtime-inverse.json'
PROOF_SHA256 = 'ddb63d265eb450187573dfaf4ccbc8a328a62840d391e95104ccff4bdcbabf40'
PATHS = frozenset(['primer/cortical_contact_reference.py', 'web/anatomy/spl-source-contacts/index.html',
                   'web/anatomy/spl-source-contacts/registry.json', 'docs/radiology-fidelity-scope.json'])
sha = lambda raw: hashlib.sha256(raw).hexdigest()

def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('MRI inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != 'd3cbd4ea438b7cc78832cec4346467a15276a89d' or
            proof['scope'] != 'exact_cortical_native_mri_integration' or set(proof['files']) != PATHS or
            proof['bindings'] != ['ra.brain-anatomy', 'ra.mri-epilepsy'] or
            any(proof[key] is not False for key in ['clinicalApproval', 'extendsHistoricalApproval', 'wholeGoalComplete'])):
        raise ValueError('MRI inverse scope differs')
    return proof

def before_mri_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw
        raise ValueError('Unreviewed MRI integration byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('MRI inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('MRI inverse altered unrelated bytes')
    return restored

def before_mri_reference_fields(identifier, fields):
    proof = reviewed(); result = copy.deepcopy(fields)
    items = result.get('source_native_inspectors', [])
    matches = [item for item in items if item.get('id') == proof['after_inspector']['id']]
    if not matches:
        return result
    if identifier not in proof['bindings']:
        raise ValueError('Unreviewed MRI binding')
    if matches == [proof['before_inspector']]:
        return result
    if matches != [proof['after_inspector']]:
        raise ValueError('Unreviewed MRI reference descriptor')
    items[items.index(matches[0])] = copy.deepcopy(proof['before_inspector'])
    return result

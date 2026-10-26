"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'a8d9ee0998d263396e41923ca5a26dc41dfdb452'
PROOF = 'docs/holiatlas-schematic-review-20261026/runtime-inverse.json'
PROOF_SHA256 = '3e6f7c44c5d892bcf658606f15ffd88047628986e315eec077f27ba8c22cee25'
PATHS = frozenset(['data/radiology/holiatlas-hierarchy.json.gz', 'data/radiology/holiatlas-reference.json', 'docs/radiology-fidelity-scope.json', 'primer/holiatlas_reference.py', 'tools/anatomy_sources/build_holiatlas_registry.py', 'web/anatomy/holiatlas/ATTRIBUTION.txt', 'web/anatomy/holiatlas/config.json', 'web/anatomy/holiatlas/hierarchy.json', 'web/anatomy/holiatlas/index.html', 'web/anatomy/holiatlas/viewer.css', 'web/anatomy/holiatlas/viewer.js'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Atlas schematic inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_atlas_schematic_and_two_compositions_only'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Atlas schematic inverse leaves exact scope')
    replacement = proof.get('source_inspector_replacement', {})
    flags = ('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')
    if (set(replacement) != {'before','after'} or any(v.get('id') != 'holiatlas-source-template-reference' or any(v.get(k) is not False for k in flags) for v in replacement.values())
            or proof['files']['data/radiology/holiatlas-hierarchy.json.gz'].get('before_fixture') != 'docs/holiatlas-schematic-review-20261026/before-hierarchy.json.gz'):
        raise ValueError('Atlas schematic inverse leaves exact source scope')
    return proof


def before_atlas_schematic_bytes(path, raw, allow_older=False):
    from tools.percentage_runtime_compatibility import before_percentage_bytes
    raw = before_percentage_bytes(path, raw, allow_older=True)
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
    if 'before_fixture' in row:
        restored = (ROOT / row['before_fixture']).read_bytes()
        if sha(restored) != row['before_sha256']:
            raise ValueError('Atlas schematic baseline fixture differs')
        return restored
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Atlas schematic inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Atlas schematic inverse changes unrelated baseline bytes')
    return restored


def before_atlas_schematic_reference_fields(identifier, fields, allow_older=False):
    import copy
    if identifier != 'ra.brain-anatomy':
        return fields
    result = copy.deepcopy(fields)
    replacement = reviewed()['source_inspector_replacement']
    items = result.get('source_native_inspectors', [])
    matches = [i for i in items if i.get('id') == 'holiatlas-source-template-reference']
    if not matches or matches == [replacement['before']]:
        return result
    if matches == [replacement['after']]:
        items[items.index(matches[0])] = copy.deepcopy(replacement['before'])
    elif not allow_older:
        raise ValueError('Unreviewed atlas schematic descriptor')
    return result

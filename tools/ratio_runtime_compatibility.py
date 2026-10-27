"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '326b06a83e96867de25207de953ebd31d2a4ed84'
PROOF = 'docs/ratio-fidelity-review-20261027/runtime-inverse.json'
PROOF_SHA256 = 'bc9c9cc65d289713556ecedc2adfa6bc44e47fdd68fcb2338d103f9c6cf962d4'
PATHS = frozenset(['data/curriculum/01-mathematics.json', 'data/module-models.json', 'primer/server.py', 'web/index.html', 'web/lesson-models.js', 'web/spatial-module-objects.js'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Ratio inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_ratio_workbench_and_calibrated_spatial_integration'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Ratio inverse leaves exact scope')
    return proof


def before_ratio_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The historical caller must check its own exact fingerprint.
        raise ValueError('Unreviewed ratio integration byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Ratio inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Ratio inverse changes unrelated baseline bytes')
    return restored

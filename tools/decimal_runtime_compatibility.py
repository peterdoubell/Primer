"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'aafeeb0dd029257cf1b4da28775686c420bb5836'
PROOF = 'docs/decimal-fidelity-review-20261026/runtime-inverse.json'
PROOF_SHA256 = '0b6931fdfe8b2df990059a5242c899a66c4436577e1f3bbd613f705573490938'
PATHS = frozenset(['data/curriculum/01-mathematics.json', 'data/module-models.json', 'primer/server.py', 'web/index.html', 'web/lesson-models.js', 'web/spatial-module-objects.js'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Decimal inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_decimal_workbench_and_base_ten_integration'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Decimal inverse leaves exact scope')
    return proof


def before_decimal_bytes(path, raw, allow_older=False):
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
            raise ValueError('Decimal inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Decimal inverse changes unrelated baseline bytes')
    return restored

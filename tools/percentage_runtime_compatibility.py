"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '236b7680e77d64740865d02eb09eba6615a2a10f'
PROOF = 'docs/percentage-fidelity-review-20261026/runtime-inverse.json'
PROOF_SHA256 = '78a77591d21a6aed279ef4889d3448da1cf2a54be9112e50136741067eeff4a6'
PATHS = frozenset(['data/curriculum/01-mathematics.json', 'primer/server.py', 'web/index.html', 'web/lesson-models.js'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Percentage inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_percentage_lesson_integration_only'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Percentage inverse leaves exact scope')
    return proof


def before_percentage_bytes(path, raw, allow_older=False):
    from tools.decimal_runtime_compatibility import before_decimal_bytes
    raw = before_decimal_bytes(path, raw, allow_older=True)
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
            raise ValueError('Percentage inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Percentage inverse changes unrelated baseline bytes')
    return restored

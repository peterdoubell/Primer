"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'e672744a2d66e94af8e063d09bc7819e218f2298'
PROOF = 'docs/base-ten-fidelity-review-20261027/runtime-inverse.json'
PROOF_SHA256 = 'e85ad90440e4ebc6a51bf48deb4fcd8eb392af078513cd70c48d6a8cf82038e5'
PATHS = frozenset(['data/curriculum/01-mathematics.json', 'data/module-models.json', 'primer/curriculum.py', 'primer/server.py', 'web/index.html', 'web/lesson-models.js', 'web/spatial-module-objects.js', 'web/spatial-models.js'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Base-ten inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_five_lesson_base_ten_and_callout_integration'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Base-ten inverse leaves exact scope')
    return proof


def before_base_ten_bytes(path, raw, allow_older=False):
    from tools.nextbrain_runtime_compatibility import before_nextbrain_bytes
    raw = before_nextbrain_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The historical caller must check its own exact fingerprint.
        raise ValueError('Unreviewed base-ten integration byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Base-ten inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Base-ten inverse changes unrelated baseline bytes')
    return restored

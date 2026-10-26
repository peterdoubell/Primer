"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'ae974fcda00827d4617de9ae52da519327dcc743'
PROOF = 'docs/current-labs-release-20261026/runtime-inverse.json'
PROOF_SHA256 = 'fd7be82f1ce58b6145add3d48a3a5963d18bdb28d61bbe28a55b018674e52122'
PATHS = frozenset({
    'data/curriculum/01-mathematics.json', 'data/curriculum/03-physics.json',
    'data/radiology/non-msk-structure-requirements.json', 'primer/curriculum.py',
    'primer/server.py', 'web/index.html', 'web/lesson-models.js',
    'web/spatial-module-objects.js', 'docs/radiology-fidelity-scope.json',
})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Current labs inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_current_lesson_and_requirement_deltas_only'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Current labs inverse leaves exact scope')
    return proof


def before_current_labs_bytes(path, raw, allow_older=False):
    from tools.circuits_runtime_compatibility import before_circuits_bytes
    raw = before_circuits_bytes(path, raw, allow_older=True)
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
            raise ValueError('Current labs inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Current labs inverse changes unrelated baseline bytes')
    return restored

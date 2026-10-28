"""Restore exact historical bytes; this does not extend past evidence to new code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '000f68c16bcdecaae999e8a0c3679a3d4b90e859'
PROOF = 'docs/coordinate-plane-review-20261028/runtime-inverse.json'
PROOF_SHA256 = 'c53641be6e25d20d7f5c1ee4b4cea45cf96a071282623c6f922c5eb3f44a79ab'
PATHS = frozenset(['data/curriculum/01-mathematics.json', 'data/module-models.json',
                  'primer/curriculum.py', 'primer/server.py', 'web/index.html',
                  'web/lesson-models.js', 'web/lesson-state.js', 'web/spatial-module-objects.js'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Coordinate-plane inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE or proof['scope'] != 'exact_coordinate_plane_lesson_integration'
            or set(proof['files']) != PATHS or any(proof[k] is not False for k in
            ['clinical_approval', 'extends_historical_approval', 'whole_goal_complete'])):
        raise ValueError('Coordinate-plane inverse scope changed')
    return proof


def before_coordinate_plane_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # Caller must still validate its own exact fingerprint.
        raise ValueError('Unreviewed coordinate-plane integration change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Coordinate-plane inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Coordinate-plane inverse changes unrelated bytes')
    return restored

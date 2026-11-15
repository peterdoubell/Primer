"""Exact prior byte views for frozen evidence; this does not validate new content."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '3f04127f67a52173a12aa141031bfac1a12cb142'
PROOF = 'docs/circuits-induction-review-20261026/runtime-inverse.json'
PROOF_SHA256 = 'd6814a6ec03e5585638fc9a7005593a02bce92135b2782b055a695f47b0e9250'
PATHS = frozenset({'data/curriculum/03-physics.json','primer/server.py','web/index.html','web/lesson-models.js'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Circuits inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'exact_electricity_and_em_integration_only'
            or set(proof['files']) != PATHS
            or any(proof.get(key) is not False for key in
                   ('clinical_approval', 'extends_historical_approval', 'whole_goal_complete'))):
        raise ValueError('Circuits inverse leaves exact scope')
    return proof


def before_circuits_bytes(path, raw, allow_older=False):
    from tools.atlas_schematic_runtime_compatibility import before_atlas_schematic_bytes
    raw = before_atlas_schematic_bytes(path, raw, allow_older=True)
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
            raise ValueError('Circuits inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Circuits inverse changes unrelated baseline bytes')
    return restored

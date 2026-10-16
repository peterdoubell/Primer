"""Reconstruct the exact pre-fluids runtime for earlier frozen evidence only."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/fluids-fidelity-review-20261016/runtime-inverse.json'
PROOF_SHA = 'dd72ad7785b648665174051c86e19f158b1cd09ec55dbfca651d0f8dc034ed80'
PATHS = frozenset(['web/index.html', 'web/lesson-models.js', 'data/curriculum/03-physics.json', 'primer/curriculum.py'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA:
        raise ValueError('Fluids inverse evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS
            or proof['base_commit'] != '20e467094ece94c5cbf90207c38f69cbe62c74af'
            or proof['module_id'] != 'phys.4.fluids'
            or any(proof[key] is not False for key in ['extends_historical_approval',
                'new_fluids_science_and_reader_validated_by_this_inverse', 'clinical_approval'])):
        raise ValueError('Fluids inverse leaves its exact scope')
    return proof


def before_fluids_bytes(path, raw, allow_older=False):
    from tools.spl_limbic_runtime_compatibility import before_spl_bytes
    raw = before_spl_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The historical caller still checks its own exact identity.
        raise ValueError('Unreviewed fluids runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        start, end = change['start'], change['end']
        if ''.join(lines[start:end]) != change['after']:
            raise ValueError('Fluids inverse literal differs')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Fluids inverse changes unrelated bytes')
    return restored

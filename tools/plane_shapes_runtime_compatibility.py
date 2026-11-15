"""Exact pre-shapes source view; historical approvals do not cover new geometry."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/plane-shapes-review-20261023/runtime-inverse.json'
PROOF_SHA256 = '02b63859fdda5451165986e517b4d2a67602a25336e744bf1bfa07a37c08c39a'
PATHS = frozenset({'web/spatial-module-objects.js', 'data/module-models.json'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Plane shapes inverse evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['scope'] != 'math.0.shapes_only'
            or proof['base_commit'] != '6d8ee107da8c29fd62de5a5d93fd18b533a543c3'
            or any(proof[key] is not False for key in ('clinical_approval',
                'extends_historical_approval', 'new_geometry_validated_by_this_inverse'))):
        raise ValueError('Plane shapes inverse leaves exact scope')
    return proof


def before_shapes_bytes(path, raw, allow_older=False):
    from tools.holiatlas_runtime_compatibility import before_holiatlas_bytes
    raw = before_holiatlas_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # Earlier consumers retain their own exact identity guard.
        raise ValueError('Unreviewed plane shapes byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Plane shapes inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Plane shapes inverse changes unrelated bytes')
    return restored

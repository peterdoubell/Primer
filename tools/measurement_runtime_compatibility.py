"""Exact pre-measurement view of one script mount and one quiz correction."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/measurement-fidelity-review-20261016/runtime-inverse.json'
PROOF_SHA = 'a6cd1d2528be59baa65ecaec9af48c9a623c03da731059a1714c57bfe7db24bb'
PATHS = frozenset({'web/index.html', 'web/lesson-models.js', 'data/curriculum/03-physics.json'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA:
        raise ValueError('Measurement inverse evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['base_commit'] != '6881f3238f26c4c3fba36d4970faa8e01045ad36'
            or proof['module_id'] != 'phys.4.experiment'
            or any(proof[key] is not False for key in ['clinical_approval', 'fine_anatomical_approval',
                                                      'extends_historical_approval',
                                                      'new_measurement_script_science_and_reader_validated_by_this_inverse'])):
        raise ValueError('Measurement inverse leaves its exact scope')
    return proof


def before_measurement_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # An earlier historical caller still checks its own exact fingerprint.
        raise ValueError('Unreviewed measurement runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        start, end = change['start'], change['end']
        if ''.join(lines[start:end]) != change['after']:
            raise ValueError('Measurement inverse literal differs')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Measurement inverse changes unrelated bytes')
    return restored

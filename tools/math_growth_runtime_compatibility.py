"""Exact offline view of four math activity description lines; no approval waiver."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = 'data/curriculum/01-mathematics.json'
PROOF = 'docs/math-growth-series-fidelity-20261014/curriculum-runtime-inverse.json'
PROOF_SHA = 'c3fcc054543fab633a8aa17f7e0c6a3609fccf634d219a65bafedd6e22507591'
BEFORE_SHA = '01a28ef358fd66fc06873cb3d23d18592c7651c3a443062f7bb969996a27cedc'
AFTER_SHA = 'f57ab18d5a4657547b7f9bdaf725bad6486d109be640fe5acc683e3759f62d4c'


def before_growth_bytes(path, raw, allow_older=False):
    if path != PATH:
        return raw
    encoded = (ROOT / PROOF).read_bytes()
    if hashlib.sha256(encoded).hexdigest() != PROOF_SHA:
        raise ValueError('Math growth inverse evidence changed')
    proof = json.loads(encoded)
    if (proof['path'] != PATH or proof['before_sha256'] != BEFORE_SHA
            or proof['after_sha256'] != AFTER_SHA or len(proof['changes']) != 2
            or proof['clinical_approval'] is not False
            or proof['extends_historical_approval'] is not False):
        raise ValueError('Math growth inverse leaves its four-line scope')
    digest = hashlib.sha256(raw).hexdigest()
    if digest == BEFORE_SHA:
        return raw
    if digest != AFTER_SHA:
        if allow_older:
            # Existing callers retain their own strict historical SHA guards.
            return raw
        raise ValueError('Unreviewed math growth curriculum byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(proof['changes']):
        start, end = change['start'], change['end']
        if end - start != 2 or ''.join(lines[start:end]) != change['after']:
            raise ValueError('Math growth inverse literal differs')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if hashlib.sha256(restored).hexdigest() != BEFORE_SHA:
        raise ValueError('Math growth inverse changes unrelated bytes')
    return restored

"""Exact candidate-to-main correspondence; caller retains its original byte guards."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/systems-equations-fidelity-review-20261013/previous-main-inverses.json'
PROOF_SHA256='e8f9e61f8f4781c81952d896980c5ee0287421a1f2d087f94db467e56b97aba9'


def previous_runtime_bytes(relative,raw):
    evidence=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(evidence).hexdigest()!=PROOF_SHA256:
        raise ValueError('Systems exact inverse evidence changed')
    row=json.loads(evidence)['files'].get(relative)
    # This layer only removes its own known addition. Every other byte stream
    # is passed intact to the caller's existing historical/current SHA guard.
    if row is None or hashlib.sha256(raw).hexdigest()!=row['current_sha256']:
        return raw
    text=raw.decode()
    for change in row['changes']:
        if text.count(change['after'])!=1:
            raise ValueError('Systems source lacks its unique reviewed change')
        text=text.replace(change['after'],change['before'],1)
    restored=text.encode()
    if hashlib.sha256(restored).hexdigest()!=row['before_sha256']:
        raise ValueError('Systems inverse changed unrelated bytes')
    return restored

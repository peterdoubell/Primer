"""Restore only the reviewed optics attachment for frozen historical reviews."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/optics-fidelity-review-20261016/runtime-inverse.json'
PROOF_SHA='9fa04fac92ddd30c45797078e9237397e78242757c097b90c21b2373b9e8c90c'

def before_optics_bytes(path, raw, allow_older=False):
    if path != 'web/lesson-models.js':
        return raw
    encoded=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(encoded).hexdigest()!=PROOF_SHA:
        raise ValueError('Optics inverse evidence changed')
    row=json.loads(encoded)
    if row['clinical_approval'] is not False or row['extends_historical_approval'] is not False:
        raise ValueError('Optics inverse cannot extend approval')
    digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:
        return raw
    if digest!=row['after_sha256']:
        if allow_older:
            return raw
        raise ValueError('Unreviewed optics attachment byte change')
    before=row['before_literal'].encode(); after=row['after_literal'].encode()
    if raw.count(after)!=1:
        raise ValueError('Optics attachment literal changed')
    result=raw.replace(after,before,1)
    if hashlib.sha256(result).hexdigest()!=row['before_sha256']:
        raise ValueError('Optics inverse changes unrelated bytes')
    return result

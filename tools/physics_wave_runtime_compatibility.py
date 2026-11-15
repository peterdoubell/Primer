"""Exact historical view of the calibrated-wave change; no approval extension."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF="docs/physics-calibrated-wave-review-20261014/runtime-inverse.json"
PROOF_SHA="f1f925cb726d003708b19dea3899618e6f730af32b370929aaa77a9ea44508be"

def before_wave_bytes(path,raw,allow_older=False):
    from tools.thoracic_label_runtime_compatibility import before_label_bytes
    raw=before_label_bytes(path,raw,allow_older=True)
    if path!='web/lesson-models.js':return raw
    encoded=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(encoded).hexdigest()!=PROOF_SHA:raise ValueError('Physics inverse evidence changed')
    row=json.loads(encoded)
    if row['clinical_approval'] is not False or row['extends_historical_approval'] is not False:raise ValueError('Physics inverse cannot extend approval')
    digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed calibrated-wave byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        a,b=change['start'],change['end']
        if ''.join(lines[a:b])!=change['after']:raise ValueError('Physics inverse literal changed')
        lines[a:b]=change['before'].splitlines(keepends=True)
    result=''.join(lines).encode()
    if hashlib.sha256(result).hexdigest()!=row['before_sha256']:raise ValueError('Physics inverse changes unrelated bytes')
    return result

"""Exact historical view of the dipole-orientation change; no approval extension."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF="docs/physics-dipole-orientation-review-20261014/runtime-inverse.json"
PROOF_SHA="163f4eff460cdc5d8e26de8ebc3be3facaa0a596fe686ab82cbc672f0aaa8a98"

def before_dipole_bytes(path,raw,allow_older=False):
    from tools.cardiac_native_runtime_compatibility import before_cardiac_bytes
    raw=before_cardiac_bytes(path,raw,allow_older=allow_older)
    from tools.math_growth_runtime_compatibility import before_growth_bytes
    raw=before_growth_bytes(path,raw,allow_older=allow_older)
    if path!='web/lesson-models.js':return raw
    encoded=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(encoded).hexdigest()!=PROOF_SHA:raise ValueError('Physics inverse evidence changed')
    row=json.loads(encoded)
    if row['clinical_approval'] is not False or row['extends_historical_approval'] is not False:raise ValueError('Physics inverse cannot extend approval')
    digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed dipole-orientation byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        a,b=change['start'],change['end']
        if ''.join(lines[a:b])!=change['after']:raise ValueError('Physics inverse literal changed')
        lines[a:b]=change['before'].splitlines(keepends=True)
    result=''.join(lines).encode()
    if hashlib.sha256(result).hexdigest()!=row['before_sha256']:raise ValueError('Physics inverse changes unrelated bytes')
    return result

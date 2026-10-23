"""Bounded source view; descriptor UI changes do not extend historical approvals."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/descriptor-reporting-release-20261023/runtime-inverse.json'
PROOF_SHA='ba930365a6ed28c3912f0e96d9a0d429f1e9eb8ccba650b47c5a359f149363c7'
PATHS=frozenset({'primer/reporting_bridge.py','web/app.js','web/radiology-structured.js','web/radiology-structured.css'})
def before_descriptor_bytes(path,raw,allow_older=False):
    if str(path) not in PATHS:return raw
    source=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(source).hexdigest()!=PROOF_SHA:raise ValueError('Descriptor report proof changed')
    proof=json.loads(source)
    if set(proof['files'])!=PATHS or proof['scope']!='descriptor_reporting_ui_and_bridge_only' or any(proof[key] is not False for key in ('clinical_approval','extends_historical_approval','canonical_lesson_data_changed')):raise ValueError('Descriptor proof scope changed')
    row=proof['files'][str(path)]
    if hashlib.sha256(raw).hexdigest()==row['before_sha256']:return raw
    if hashlib.sha256(raw).hexdigest()!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed descriptor report change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Descriptor source delta changed')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if hashlib.sha256(restored).hexdigest()!=row['before_sha256']:raise ValueError('Descriptor source baseline changed')
    return restored

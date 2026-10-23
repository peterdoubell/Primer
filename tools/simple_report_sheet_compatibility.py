"""Exact presentation-only view for the older report-control receipt."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/simple-report-sheet-20261023.json'
PROOF_SHA='6b65ce71ddab4b094797121e446188f896fb54558631726c6671c463edafec8f'
def before_simple_asset(path,raw):
    from tools.descriptor_report_compatibility import before_descriptor_bytes
    raw=before_descriptor_bytes(path,raw,allow_older=True)
    source=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(source).hexdigest()!=PROOF_SHA:raise ValueError('Report sheet proof changed')
    proof=json.loads(source)
    if proof['scope']!='report_sheet_presentation_only' or proof['clinical_rules_changed'] is not False:raise ValueError('Report sheet scope changed')
    if set(proof['files'])!={'web/radiology-structured.js','web/radiology-structured.css'}:raise ValueError('Report sheet file scope changed')
    row=proof['files'].get(str(path))
    if row is None:return raw
    if hashlib.sha256(raw).hexdigest()==row['before_sha256']:return raw
    if hashlib.sha256(raw).hexdigest()!=row['after_sha256']:raise ValueError('Unreviewed report sheet change')
    previous=row['before'].encode()
    if hashlib.sha256(previous).hexdigest()!=row['before_sha256']:raise ValueError('Report sheet baseline changed')
    return previous

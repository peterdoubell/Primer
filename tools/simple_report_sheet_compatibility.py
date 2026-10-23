"""Exact presentation-only view for the older report-control receipt."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/simple-report-sheet-20261023.json'
PROOF_SHA='4df6ccc193498329cdb6b20a4deee5780d0a6e91e92f3768067c05fd23cc48f3'
def before_simple_asset(path,raw):
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

"""Exact inverse of reporting presentation changes for older evidence checks."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/report-compartments-20261028/runtime-inverse.json'
PROOF_SHA256='730b597bddb3a963dfd29a57dbbc1d8ec02264e30284d99e0c29860a3fe3e324'

def before_compartments_bytes(path,raw,allow_older=False):
 if str(path) not in ('web/radiology-structured.js','web/radiology-structured.css'):return raw
 encoded=(ROOT/PROOF).read_bytes()
 if hashlib.sha256(encoded).hexdigest()!=PROOF_SHA256:raise ValueError('Compartment inverse evidence changed')
 proof=json.loads(encoded)
 if proof['scope']!='report_compartment_presentation_only' or proof['clinical_approval'] is not False or set(proof['files'])!={'web/radiology-structured.js','web/radiology-structured.css'}:raise ValueError('Compartment inverse scope changed')
 row=proof['files'][str(path)];digest=hashlib.sha256(raw).hexdigest()
 if digest==row['before_sha256']:return raw
 if digest!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed compartment presentation change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Compartment inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if hashlib.sha256(restored).hexdigest()!=row['before_sha256']:raise ValueError('Compartment inverse differs')
 return restored

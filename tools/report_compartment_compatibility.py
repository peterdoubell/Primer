"""Exact inverse of reporting presentation changes for older evidence checks."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/report-compartments-20261028/runtime-inverse.json'
PROOF_SHA256='62a914d24f7c50e2f4bd7a932adfb0410200f2f77fe699a87169493fdb7ce628'

def before_compartments_bytes(path,raw,allow_older=False, *, retain_compartments=False):
 if str(path) not in ('web/radiology-structured.js','web/radiology-structured.css','primer/descriptor_reporting.py'):return raw
 encoded=(ROOT/PROOF).read_bytes()
 if hashlib.sha256(encoded).hexdigest()!=PROOF_SHA256:raise ValueError('Compartment inverse evidence changed')
 proof=json.loads(encoded)
 if proof['scope']!='report_compartment_presentation_only' or proof['clinical_approval'] is not False or set(proof['files'])!={'web/radiology-structured.js','web/radiology-structured.css'}:raise ValueError('Compartment inverse scope changed')
 document=proof['report_document_structure'][str(path)]
 if hashlib.sha256(raw).hexdigest()==document['after_sha256']:
  raw=restore_presentation_bytes(raw,document)
 if str(path)=='primer/descriptor_reporting.py':
  engine=proof['report_format_engine']
  if hashlib.sha256(raw).hexdigest()==engine['after_sha256']:
   return restore_presentation_bytes(raw,engine)
  return raw
 row=proof['files'][str(path)]
 upgrade=proof['navigation_upgrade'][str(path)]
 if upgrade['before_sha256']!=row['after_sha256']:
  raise ValueError('Navigation inverse does not match the compartment release')
 if hashlib.sha256(raw).hexdigest()==upgrade['after_sha256']:
  raw=restore_presentation_bytes(raw,upgrade)
 digest=hashlib.sha256(raw).hexdigest()
 if retain_compartments and digest==row['after_sha256']:return raw
 if digest==row['before_sha256']:return raw
 if digest!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed compartment presentation change')
 return restore_presentation_bytes(raw,row)

def restore_presentation_bytes(raw,row):
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Compartment inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if hashlib.sha256(restored).hexdigest()!=row['before_sha256']:raise ValueError('Compartment inverse differs')
 return restored

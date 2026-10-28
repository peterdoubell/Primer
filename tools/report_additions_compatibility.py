"""Hash-bound compatibility view for report additions; no clinical approval."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/report-additions-20261026/runtime-inverse.json'
PROOF_SHA256='6d26fe953504d745f7465659a780727b451eba104d4eed04695ba6e242841011'
BASE_COMMIT='3f04127f67a52173a12aa141031bfac1a12cb142'
PATHS=frozenset({'primer/reporting_bridge.py','primer/descriptor_reporting.py','web/radiology-structured.js'})
SCOPE='new_selectable_examinations_acquisition_scope_calculator_routing_and_widget_availability_only'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
 raw=(ROOT/PROOF).read_bytes()
 if sha(raw)!=PROOF_SHA256:raise ValueError('Report addition inverse evidence changed')
 proof=json.loads(raw)
 if (proof['base_commit']!=BASE_COMMIT or proof['scope']!=SCOPE or set(proof['files'])!=PATHS or any(proof.get(k) is not False for k in ('clinical_approval','extends_historical_approval','native_anatomy_or_canonical_lessons_changed'))):
  raise ValueError('Report addition inverse leaves exact scope')
 return proof
def before_report_additions_bytes(path,raw,allow_older=False):
 from tools.report_compartment_compatibility import before_compartments_bytes
 raw=before_compartments_bytes(path,raw,allow_older=True)
 path=str(path)
 if path not in PATHS:return raw
 row=reviewed()['files'][path]
 if sha(raw)==row['before_sha256']:return raw
 if sha(raw)!=row['after_sha256']:
  if allow_older:return raw
  raise ValueError('Unreviewed report addition byte change')
 lines=raw.decode().splitlines(keepends=True)
 for change in reversed(row['changes']):
  if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Report addition inverse literal differs')
  lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
 restored=''.join(lines).encode()
 if sha(restored)!=row['before_sha256']:raise ValueError('Report addition inverse changed unrelated bytes')
 return restored

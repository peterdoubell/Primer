"""The new reporting controls cannot inherit anatomy approvals or hide unknown deltas."""
import json
from pathlib import Path
import pytest
from tools import report_additions_compatibility as receipt
from tools.current_labs_runtime_compatibility import before_current_labs_bytes
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('path',sorted(receipt.PATHS))
def test_exact_receipt_is_idempotent_and_preserves_unknown_changes(path):
 from tools.report_compartment_compatibility import before_compartments_bytes
 raw=before_compartments_bytes(path,(ROOT/path).read_bytes());row=receipt.reviewed()['files'][path]
 assert receipt.sha(raw)==row['after_sha256']
 restored=receipt.before_report_additions_bytes(path,raw)
 assert receipt.sha(restored)==row['before_sha256']
 assert receipt.before_report_additions_bytes(path,restored)==restored
 assert before_current_labs_bytes(path,raw)==restored
 with pytest.raises(ValueError,match='Unreviewed'):
  receipt.before_report_additions_bytes(path,raw+b'\nunknown\n')
 assert receipt.before_report_additions_bytes(path,raw+b'\nunknown\n',allow_older=True)==raw+b'\nunknown\n'

@pytest.mark.parametrize('mutation',['path','scope','clinical'])
def test_receipt_cannot_broaden_scope_even_if_hash_is_rebound(tmp_path,monkeypatch,mutation):
 proof=json.loads((ROOT/receipt.PROOF).read_text())
 if mutation=='path':proof['files']['primer/server.py']=proof['files']['primer/reporting_bridge.py']
 if mutation=='scope':proof['scope']='arbitrary-runtime'
 if mutation=='clinical':proof['clinical_approval']=True
 raw=json.dumps(proof).encode();p=tmp_path/receipt.PROOF;p.parent.mkdir(parents=True);p.write_bytes(raw)
 monkeypatch.setattr(receipt,'ROOT',tmp_path);monkeypatch.setattr(receipt,'PROOF_SHA256',receipt.sha(raw))
 with pytest.raises(ValueError,match='scope'):receipt.reviewed()

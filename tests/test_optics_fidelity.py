"""Optics must obey its physical equations and preserve earlier reviewed behavior."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from tools.optics_runtime_compatibility import before_optics_bytes

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js required')
@pytest.mark.parametrize('script,counts',[
 ('check_optics_core.cjs',{'lensStates':14400,'slitStates':105}),
 ('check_optics_interfaces.cjs',{'refractionStates':4500,'filmStates':18180}),
 ('check_optics_contract.cjs',{'lensUIStates':8832}),
])
def test_scientific_oracles_and_input_domains(script,counts):
    result=subprocess.run(['node','tools/'+script],cwd=ROOT,text=True,capture_output=True,timeout=45)
    assert result.returncode==0,result.stdout+result.stderr
    proof=json.loads(result.stdout)
    assert all(proof[k]==v for k,v in counts.items())

def test_only_exact_optics_attachment_restores_frozen_history():
    proof=json.loads((ROOT/'docs/optics-fidelity-review-20261016/runtime-inverse.json').read_text())
    raw=(ROOT/proof['path']).read_bytes()
    previous=before_optics_bytes(proof['path'],raw)
    assert hashlib.sha256(previous).hexdigest()==proof['before_sha256']
    assert raw.count(proof['after_literal'].encode())==1
    assert before_optics_bytes(proof['path'],previous)==previous
    assert before_optics_bytes('unrelated.js',b'anything')==b'anything'
    with pytest.raises(ValueError,match='Unreviewed'):
        before_optics_bytes(proof['path'],raw+b'changed')
    assert proof['clinical_approval'] is proof['extends_historical_approval'] is False

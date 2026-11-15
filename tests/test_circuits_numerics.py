"""Independent circuit, field, energy and trajectory oracles run against current JS."""
import json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('tool',['check_circuits_core.py','check_circuits_extensions.py','check_circuits_pipe.py'])
def test_independent_current_physics_oracle(tool):
 run=subprocess.run([sys.executable,str(ROOT/'tools'/tool)],cwd=ROOT,text=True,capture_output=True,timeout=120)
 assert run.returncode==0,run.stdout+run.stderr
 proof=json.loads(run.stdout)
 assert proof['allPassed'] is True

"""Independent exact equations and high-precision roots for the current core."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]

def test_independent_fraction_decimal_oracle():
    run=subprocess.run([sys.executable,str(ROOT/'tools/check_algebra_functions_independent.py')],cwd=ROOT,capture_output=True,text=True,timeout=180)
    assert run.returncode==0,run.stdout+run.stderr
    proof=json.loads(run.stdout)
    assert proof['allPassed'] and proof['models']==17706 and proof['practiceCases']==9823 and proof['checks']==171549 and proof['explicitRejections']==37
    assert proof['sourceSHA256']==hashlib.sha256((ROOT/'web/algebra-functions-core.js').read_bytes()).hexdigest()
    assert not proof['wholeGoalComplete']

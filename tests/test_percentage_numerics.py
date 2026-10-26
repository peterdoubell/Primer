"""Independent exact rational oracle against the current percentage core."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_independent_percentage_oracle():
 run=subprocess.run([sys.executable,str(ROOT/'tools/check_percentage_core.py')],cwd=ROOT,text=True,capture_output=True,timeout=60)
 assert run.returncode==0,run.stdout+run.stderr
 proof=json.loads(run.stdout)
 assert proof['allPassed'] and proof['cases']==873

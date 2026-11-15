"""Current exact decimal operations and real base-ten spatial geometry."""
import json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('tool',['check_decimal_core.py','check_decimal_spatial.py'])
def test_independent_decimal_oracles(tool):
 run=subprocess.run([sys.executable,str(ROOT/'tools'/tool)],cwd=ROOT,text=True,capture_output=True,timeout=60)
 assert run.returncode==0,run.stdout+run.stderr
 p=json.loads(run.stdout);assert p['allPassed']
 if tool=='check_decimal_core.py':assert p['cases']==3265 and p['columnIdentities']==7448 and p['groupWindowChecks']==1930
 else:assert p['appBindingIntegrated'] and p['states']==130 and p['closedOutwardFaceChecks']==4734 and p['pieceVolumesChecked']==789 and p['regroupingVolumeEqualities']==3 and p['nonoverlappingPiecePairsChecked']==4389 and p['exactInspectionGapsChecked']==642

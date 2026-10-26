"""Independent SI-to-Torr/cm conversion and coefficient-domain classification."""
import itertools,json,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_fitted_domain_uses_both_imposed_and_threshold_fields():
 states=[dict(chargeNC=q,gapMM=d,pressureKPa=p,secondary=g) for q,d,p,g in itertools.product([-5000,-3000,0,1500,3000,5000],[.1,1,5],[20,101.325,120],[.005,.01,.05])]
 code="const c=require('./web/circuits-induction-core.js');console.log(JSON.stringify(JSON.parse(require('fs').readFileSync(0)).map(s=>c.spark(s))));"
 models=json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT,input=json.dumps(states),text=True))
 classified=set()
 for s,m in zip(states,models):
  pressure_torr=s['pressureKPa']*1000*760/101325;gap_cm=s['gapMM']/10
  applied=abs(m['voltage'])/(gap_cm*pressure_torr)
  threshold=m['threshold']/(gap_cm*pressure_torr)
  assert math.isclose(m['reducedField'],applied,rel_tol=2e-15,abs_tol=1e-12)
  assert math.isclose(m['thresholdReducedField'],threshold,rel_tol=2e-15)
  assert m['coefficientFitRange']==[100,800]
  assert m['appliedWithinFit']==(100<=applied<=800)
  assert m['thresholdWithinFit']==(100<=threshold<=800)
  classified.add(m['appliedWithinFit'])
  for point in m['curve']:
   ep=point['threshold']/(point['gap']*100*pressure_torr)
   assert math.isclose(ep,point['thresholdReducedField'],rel_tol=2e-15)
   assert point['thresholdWithinFit']==(100<=ep<=800)
 assert classified=={True,False}

from pathlib import Path
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
from decimal import Decimal,localcontext
import itertools,json,subprocess,math
D=Path(__file__).resolve().parents[1]/'docs/physics-particle-review-20261102';requests=[dict(fraction=f,cosine=c,azimuth=a)for f,c,a in itertools.product([0,1e-10,.01,.25,.5,.9,1-1e-10,1],[-1,-.5,0,.5,1],[0,.7,2.4])];script="const fs=require('fs'),c=require('./tools/load_particle_runtime.cjs');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(p=>c.beta(p))));";rows=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(requests),text=True));worstE=worstP=worstMassShell=0
with localcontext()as ctx:
 ctx.prec=50;mn=Decimal('939.56542194');mp=Decimal('938.27208943');me=Decimal('.51099895069');endpoint=((mn-me)**2-mp**2)/(2*mn)
 for q,r in zip(requests,rows):
  assert abs(r['electronKineticMeV']-float(Decimal(str(q['fraction']))*endpoint))<1e-12
  momenta=r['momentaMeVPerC'];total=[sum(momenta[k][j]for k in ['electron','neutrino','proton'])for j in range(3)];worstP=max(worstP,max(map(abs,total)));assert max(map(abs,total))<1e-12
  Ee=Decimal(str(r['electronEnergyMeV']));En=Decimal(str(r['neutrinoEnergyMeV']));Ep=Decimal(str(r['protonEnergyMeV']));error=abs(float(Ee+En+Ep-mn));worstE=max(worstE,error);assert error<1e-10
  for key,E,mass in [('electron',Ee,me),('neutrino',En,Decimal(0)),('proton',Ep,mp)]:
   p2=sum(Decimal(str(v))**2 for v in momenta[key]);error=abs(float(E*E-p2-mass*mass));worstMassShell=max(worstMassShell,error);assert error<1e-7
  if q['fraction']==0:assert not r['electronDirectionDefined']
  if q['fraction']==1:assert not r['neutrinoDirectionDefined']and r['neutrinoEnergyMeV']==0
proof={'allPassed':True,'kinematicCases':len(rows),'maxEnergyResidualMeV':worstE,'maxMomentumResidualMeVPerC':worstP,'maxMassShellResidualMeV2':worstMassShell,'masslessAntineutrinoApproximation':True,'decayRatesOrMeasuredEventsClaimed':False,'wholeGoalComplete':False};(args.output or D/'four-momentum-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

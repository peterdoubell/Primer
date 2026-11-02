from pathlib import Path
from fractions import Fraction
from decimal import Decimal
import json,subprocess,itertools
D=Path(__file__).resolve().parent;particles={'neutron':(Fraction(0),Fraction(1),0),'proton':(Fraction(1),Fraction(1),0),'electron':(Fraction(-1),Fraction(0),1),'positron':(Fraction(1),Fraction(0),-1),'neutrino':(Fraction(0),Fraction(0),1),'antineutrino':(Fraction(0),Fraction(0),-1)};masses={'neutron':Decimal('939.56542194'),'proton':Decimal('938.27208943'),'electron':Decimal('.51099895069'),'positron':Decimal('.51099895069'),'neutrino':Decimal(0),'antineutrino':Decimal(0)}
requests=[{'initial':[parent],'final':list(final)}for parent in ['neutron','proton']for length in [1,2,3]for final in itertools.product(particles,repeat=length)]
script="const fs=require('fs'),{audit}=require('./.research/physics-particle-20261102/ledger.cjs');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(p=>audit(p.initial,p.final))));";rows=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(requests),text=True));worst=0
for p,r in zip(requests,rows):
 before=[sum(particles[k][i]for k in p['initial'])for i in range(3)];after=[sum(particles[k][i]for k in p['final'])for i in range(3)];diff=[after[i]-before[i]for i in range(3)]
 assert r['differences']=={'chargeThirds':int(diff[0]*3),'baryonThirds':int(diff[1]*3),'electronLepton':int(diff[2])}
 assert r['numbersBalance']==all(d==0 for d in diff)
 Q=sum(masses[k]for k in p['initial'])-sum(masses[k]for k in p['final']);error=abs(float(Q)-r['restEnergyBudgetMeV']);worst=max(worst,error);assert error<1e-9
 assert r['checksPass']==(Q>0 and all(d==0 for d in diff))
proof={'allPassed':True,'channels':len(rows),'fractionArithmeticForQuantumNumbers':True,'decimalRestEnergyChecks':True,'maxBudgetErrorMeV':worst,'checksAreNecessaryNotCompleteSelectionRules':True,'wholeGoalComplete':False};(D/'ledger-independent-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

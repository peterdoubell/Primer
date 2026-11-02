from pathlib import Path
from decimal import Decimal,localcontext
import argparse,json,subprocess,hashlib,math
R=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=R/'docs/physics-condensed-review-20261102/runtime-core-proof.json');args=parser.parse_args()
requests=[{'temperature':T,'appliedMilliTesla':B}for T in [i*.5 for i in range(21)]+[7.2]for B in range(0,101,5)]
script="global.window={};require("+json.dumps(str(R/'web/physics-condensed-core.js'))+");const c=window.CondensedCore,fs=require('fs');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(p=>c.build(p))));"
rows=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(requests),text=True));worst=0
with localcontext()as ctx:
 ctx.prec=50;tc=Decimal('7.2');mu=Decimal(str(4*math.pi*1e-7))
 for p,m in zip(requests,rows):
  t=Decimal(str(p['temperature']));B=Decimal(str(p['appliedMilliTesla']));bc=Decimal(80)*(1-(t/tc)**2)if t<tc else Decimal(0)
  assert abs(m['criticalMilliTesla']-float(bc))<1e-12
  assert m['superconducting']==(t<tc and B<bc)
  if t>=tc:assert m['gibbsDifferenceJPerM3']is None
  else:
   energy=(B*B-bc*bc)*Decimal('0.000001')/(2*mu);error=abs(m['gibbsDifferenceJPerM3']-float(energy));worst=max(worst,error);assert error<1e-9
  if B<=80:assert abs(m['transitionTemperatureK']-float(tc*(1-B/80).sqrt()))<2e-14
  else:assert m['transitionTemperatureK']is None
proof={'allPassed':True,'states':len(rows),'decimalPrecision':50,'independentCriticalFieldAndGibbsEnergyChecks':True,'maximumAbsoluteEnergyErrorJPerM3':worst,'coreSHA256':hashlib.sha256((R/'web/physics-condensed-core.js').read_bytes()).hexdigest(),'wholeGoalComplete':False};args.output.write_text(json.dumps(proof,indent=2)+'\n');print(proof)

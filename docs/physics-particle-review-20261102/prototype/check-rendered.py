from pathlib import Path
from decimal import Decimal,localcontext
import json,math
D=Path(__file__).resolve().parent;cases=json.loads((D/'browser-cases.json').read_bytes());count=0;worst=0
with localcontext()as ctx:
 ctx.prec=50;mn=Decimal('939.56542194');mp=Decimal('938.27208943');me=Decimal('.51099895069');endpoint=((mn-me)**2-mp**2)/(2*mn)
 for c in cases:
  s=c['state'];t=Decimal(str(s['fraction']))*endpoint;e=me+t;p=(t*(t+2*me)).sqrt();cos=Decimal(str(s['cosine']));nu=Decimal(0)if s['fraction']==1 else(mn*mn+me*me-mp*mp-2*mn*e)/(2*(mn-e+p*cos));v_e=[float(p),0,0];v_n=[float(nu*cos),float(nu)*math.sqrt(1-float(cos)**2)*math.cos(s['azimuth']),float(nu)*math.sqrt(1-float(cos)**2)*math.sin(s['azimuth'])];v_p=[-v_e[i]-v_n[i]for i in range(3)];vectors={'electron':v_e,'neutrino':v_n,'proton':v_p};origin=[0,0,0]
  def project(v):
   x=math.cos(c['yaw'])*v[0]-math.sin(c['yaw'])*v[1];y=math.sin(c['yaw'])*v[0]+math.cos(c['yaw'])*v[1];up=math.cos(c['pitch'])*v[2]-math.sin(c['pitch'])*y;return[300+180*x,240-180*up]
  for name in ['electron','neutrino','proton']:
   v=vectors[name];end=[origin[i]+v[i]for i in range(3)];matches=[r for r in c['lines']if r['name']==name]
   if any(abs(x)>1e-35 for x in v)and(name!='proton'or math.hypot(*v)>64*2**-52*float(mn+mp)):
    assert len(matches)==1;row=matches[0];expected=project(origin)+project(end);error=max(abs(row[k]-val)for k,val in zip(['x1','y1','x2','y2'],expected));worst=max(worst,error);assert error<1e-8
    assert all(0<=val<=600 if i%2==0 else 0<=val<=500 for i,val in enumerate(expected));count+=1
   else:assert not matches and name in c['zeroVectors']
   origin=end
  assert max(map(abs,origin))<1e-12
proof={'allPassed':True,'browserCases':len(cases),'renderedNonzeroVectors':count,'maxSVGCoordinateError':worst,'independentRelativisticKinematics':True,'zeroMomentumDoesNotInventDirection':True,'equalMomentumScaleVerified':True,'wholeGoalComplete':False};(D/'rendered-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

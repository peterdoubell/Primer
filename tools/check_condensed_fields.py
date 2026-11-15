from pathlib import Path
import json,math
D=Path(__file__).resolve().parents[1]/'docs/physics-condensed-review-20261102/reader';cases=json.loads((D/'field-browser-cases.json').read_bytes());mu=4*math.pi*1e-7;count=0;maxerr=0
for c in cases:
 T=c['temperature'];B=c['appliedMilliTesla']*.001;screened=T<7.2 and B<.08*(1-(T/7.2)**2);inside=0 if screened else B;expected_count=(24 if B else 0)+(27 if inside else 0)+(16 if screened and B else 0)
 assert len(c['shafts'])==expected_count and c['zeroSamples']==67-expected_count
 def project(q):
  x,y,z=q;horizontal=math.cos(c['yaw'])*x-math.sin(c['yaw'])*y;depth=math.sin(c['yaw'])*x+math.cos(c['yaw'])*y;vertical=math.cos(c['pitch'])*z-math.sin(c['pitch'])*depth
  return [400+70*horizontal,220-70*vertical]
 for row in c['shafts']:
  g=row['source'];p=g['originMM'];radius=math.hypot(p[0],p[1]);kind=row['kind']
  if kind=='surface-K':
   assert abs(radius-1)<1e-12;vector=[(B-inside)/mu*p[1],-(B-inside)/mu*p[0],0];scale=1e-5
  else:
   value=inside if kind=='inside-B'else B;assert (radius<1)if kind=='inside-B'else(radius>1);vector=[0,0,value];scale=10
  assert all(abs(a-b)<1e-10 for a,b in zip(vector,g['value']))
  q=[p[i]+scale*vector[i]for i in range(3)];start=project(p);end=project(q)
  error=max(abs(row[k]-v)for k,v in zip(['x1','y1','x2','y2'],start+end));assert error<1e-9;maxerr=max(maxerr,error);count+=1
proof={'allPassed':True,'cameraStateCases':len(cases),'renderedNonzeroVectors':count,'maxSVGCoordinateError':maxerr,'independentMagneticPhaseAndSheetCurrentValues':True,'zeroValueCountsVerified':True,'wholeGoalComplete':False};(D/'rendered-field-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

from pathlib import Path
import json,math
D=Path(__file__).resolve().parent;cases=json.loads((D/'browser-cases.json').read_bytes());count=0
for c in cases:
 B=c['appliedMilliTesla'];boundary=7.2*math.sqrt(1-B/80)if B<=80 else None
 assert c['transitionTemperatureK']==boundary
 for curve in c['paths']:
  points=[tuple(map(float,p.split(',')))for p in curve['points'].split()]
  for x,y in points:
   T=(x-70)/660*10;q=(370-y)/300
   if curve['kind']=='normal':assert abs(q)<1e-12 and T>=max(0,boundary or 0)-1e-12
   else:assert T<=boundary+1e-12 and abs(q*q-(1-T/7.2))<1e-12
   count+=1
  if curve['kind']=='superconducting-limit':assert abs((points[-1][0]-70)/660*10-boundary)<1e-12
  if B>0 and boundary is not None:
   assert not any((a[1]-370)*(b[1]-370)<0 for a,b in zip(points,points[1:]))
 if 0<B<80:
  assert len(c['openEnds'])==2
  for e in c['openEnds']:assert abs((e['x']-70)/660*10-boundary)<1e-12
  assert c['selected']==0 and c['orderParameterIndex']is None and c['gibbsDifferenceJPerM3']==0
proof={'allPassed':True,'browserCases':len(cases),'renderedBranchVertices':count,'separateBranchPathsVerified':True,'nonzeroFieldCoexistenceNoUniqueMarker':True,'exactTransitionCoordinatesVerified':True,'wholeGoalComplete':False};(D/'geometry-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

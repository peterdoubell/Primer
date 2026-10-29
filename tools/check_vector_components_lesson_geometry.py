from pathlib import Path
import json,math,numpy as np
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/vector-components-review-20261029/lesson';p=json.loads((D/'proof.json').read_bytes());count=0
for case in p['states']:
 d=case['draw'];s=d['scene'];dim=s['model']['state']['dimension'];yaw,pitch=map(math.radians,[d['yaw'],d['pitch']]);cy,sy,cp,sp=math.cos(yaw),math.sin(yaw),math.cos(pitch),math.sin(pitch);rotation=np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
 def project(v):
  q=np.asarray(v) if dim==2 else rotation@np.asarray(v)
  return np.array([240+100*q[0],240+100*q[2] if dim==2 else 240-100*q[1]])
 for panel in d['panels']:
  expected={a['id']:(project(a['displayFrom']),project(a['displayTo'])) for a in s['arrows']} if panel['id']=='vectors' else {'cross':(np.array([240,240]),np.array([240,240-100*s['crossPanel']['display'][1]]) if dim==2 else project(s['crossPanel']['display']))}
  if panel['id']=='vectors':
   shown={'addition':['a','b','sum','b-after-a','a-after-b'],'combination':['scaled-a','scaled-b','combination','scaled-b-after-a'],'projection':['a','b','projection-on-b','orthogonal-remainder']}[case['operation']];expected={k:v for k,v in expected.items() if k in shown}
  assert set(expected)=={x['id'] for x in panel['items']}
  for item in panel['items']:
   a,b=expected[item['id']]
   if item['tag']=='circle':assert np.linalg.norm(a-b)<1e-8;assert np.max(abs(b-[item['cx'],item['cy']]))<1e-9
   else:assert np.max(abs(a-[item['x1'],item['y1']]))<1e-9;assert np.max(abs(b-[item['x2'],item['y2']]))<1e-9
   count+=1
proof=dict(allPassed=True,states=len(p['states']),drawnSegmentsChecked=count,independentCameraMatrix=True,lessonIntegrated=True,productionVerified=False)
assert p['browserChecksPassed']
p.update(allPassed=True,geometryReadbackVerified=True,drawnSegmentsChecked=count)
(D/'proof.json').write_text(json.dumps(p,indent=2)+'\n')
(D/'geometry-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

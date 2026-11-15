from pathlib import Path
import json,subprocess,math,hashlib
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'.research/vector-fidelity-20261029'
D.mkdir(exist_ok=True)
subprocess.run(['node','-e',"const fs=require('fs'),s=require('../../web/vector-components-scene.js');fs.writeFileSync('scenes.json',JSON.stringify(JSON.parse(fs.readFileSync('cases.json')).map(s.scene)));"],cwd=D,check=True)
cases=json.loads((D/'cases.json').read_bytes());scenes=json.loads((D/'scenes.json').read_bytes());segments=0
for case,s in zip(cases,scenes,strict=True):
 a,b=case['a'],case['b'];m=s['model'];expected={'a':([0,0,0],a),'b':([0,0,0],b),'sum':([0,0,0],[x+y for x,y in zip(a,b)]),'combination':([0,0,0],[case['alpha']*x+case['beta']*y for x,y in zip(a,b)]),'b-after-a':(a,m['sum']),'a-after-b':(b,m['sum'])}
 expected.update({'scaled-a':([0,0,0],[case['alpha']*x for x in a]),'scaled-b':([0,0,0],[case['beta']*x for x in b]),'scaled-b-after-a':([case['alpha']*x for x in a],m['combination'])})
 if m['projectionOnB']:
  p=[r['n']/r['d'] for r in m['projectionOnB']];expected.update({'projection-on-b':([0,0,0],p),'orthogonal-remainder':(p,a)})
 assert set(expected)=={r['id'] for r in s['arrows']}
 for row in s['arrows']:
  assert (row['from'],row['to'])==expected[row['id']]
  assert row['zero']==(row['from']==row['to'])
  for source,display in [(row['from'],row['displayFrom']),(row['to'],row['displayTo'])]:
   recovered=[display[0]/s['gain'],-display[2]/s['gain'],display[1]/s['gain']]
   assert max(abs(x-y)for x,y in zip(source,recovered))<1e-12
   assert math.sqrt(sum(x*x for x in display))<=1.8+1e-12
  segments+=1
 # Uniform gain preserves dot products and the right-handed cross-product orientation.
 da,db=[s['arrows'][i]['displayTo'] for i in [0,1]];cross=[da[(i+1)%3]*db[(i+2)%3]-da[(i+2)%3]*db[(i+1)%3] for i in range(3)];wanted=[m['cross'][0],m['cross'][2],-m['cross'][1]]
 assert max(abs(x-y*s['gain']**2)for x,y in zip(cross,wanted))<1e-12
 panel=s['crossPanel'];assert max(abs(x-y*panel['gain'])for x,y in zip(panel['display'],wanted))<1e-12
proof=dict(allPassed=True,states=len(scenes),sourceSegmentsChecked=segments,coordinateInverseTolerance=1e-12,rightHandedOrientationVerified=True,separateCrossProductScale=True,sourceSHA256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()for name in ['web/vector-components-core.js','web/vector-components-scene.js']},integrated=False)
(D/'scene-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

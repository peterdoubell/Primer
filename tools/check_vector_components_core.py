from pathlib import Path
import json,random,subprocess,math,hashlib
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'.research/vector-fidelity-20261029'
D.mkdir(exist_ok=True);r=random.Random(20261029)
cases=[dict(a=a,b=b,alpha=alpha,beta=beta,dimension=2) for a,b,alpha,beta in [([2,3,0],[4,-1,0],1,1),([1,2,0],[3,-5,0],1,1),([2,-1,0],[4,2,0],3,-1),([0,8,0],[6,0,0],1,1),([3,4,0],[-4,3,0],1,1),([0,0,0],[0,0,0],0,0)]]
for _ in range(5000):cases.append(dict(a=[r.randint(-32,32) for _ in range(3)],b=[r.randint(-32,32) for _ in range(3)],alpha=r.randint(-8,8),beta=r.randint(-8,8),dimension=3))
(D/'cases.json').write_text(json.dumps(cases));subprocess.run(['node','-e',"const fs=require('fs'),c=require('../../web/vector-components-core.js');fs.writeFileSync('results.json',JSON.stringify(JSON.parse(fs.readFileSync('cases.json')).map(c.model)));"],cwd=D,check=True)
for s,m in zip(cases,json.loads((D/'results.json').read_bytes()),strict=True):
 a,b=s['a'],s['b'];ab=sum(x*y for x,y in zip(a,b));a2=sum(x*x for x in a);b2=sum(y*y for y in b)
 # Independent cyclic 2x2 determinants.
 cross=[a[(i+1)%3]*b[(i+2)%3]-a[(i+2)%3]*b[(i+1)%3] for i in range(3)]
 assert m['dot']==ab and m['cross']==cross and m['cross2']==a2*b2-ab*ab
 assert sum(x*y for x,y in zip(a,cross))==sum(x*y for x,y in zip(b,cross))==0
 assert m['sum']==[x+y for x,y in zip(a,b)] and m['combination']==[s['alpha']*x+s['beta']*y for x,y in zip(a,b)]
 for key,vec in [('a2',a),('b2',b),('sum2',m['sum']),('combination2',m['combination'])]:assert m[key]==sum(x*x for x in vec)
 if b2:
  projection=[Fraction(ab*y,b2) for y in b];assert m['projectionOnB']==[dict(n=x.numerator,d=x.denominator) for x in projection];assert sum((Fraction(x)-p)*y for x,p,y in zip(a,projection,b))==0
 else:assert m['projectionOnB'] is None
 if a2 and b2:assert abs(m['angleRadians']-math.acos(max(-1,min(1,ab/math.sqrt(a2*b2)))))<1e-10
 else:assert m['angleRadians'] is None and m['parallel'] is None and m['perpendicular'] is None
proof=dict(allPassed=True,cases=len(cases),coreSHA256=hashlib.sha256((ROOT/'web/vector-components-core.js').read_bytes()).hexdigest(),oracle='Integer dot products, cyclic determinants, Lagrange identity, Fraction projections and independent acos angles',integrated=False)
(D/'core-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

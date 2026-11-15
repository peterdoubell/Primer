from pathlib import Path
import json,math,collections
import numpy as np
D=Path(__file__).resolve().parent;data=json.loads((D/'density-surfaces.json').read_bytes());p=data['parameters'];M,a,b=p['diskMass'],p['diskA'],p['diskB'];maxerr=0;vertices=triangles=0
# Density oracle: finite-difference Cartesian Laplacian of Phi/G, using Poisson's equation.
def potential(q):
 x,y,z=q;return -M/math.sqrt(x*x+y*y+(a+math.sqrt(z*z+b*b))**2)
def density(q):
 step=1e-4*b;f=potential(q);lap=0
 for axis in range(3):
  v=np.zeros(3);v[axis]=step;lap+=(-potential(q+2*v)+16*potential(q+v)-30*f+16*potential(q-v)-potential(q-2*v))/(12*step*step)
 return lap/(4*math.pi)
for surface in data['surfaces']:
 xyz=np.array(surface['positions']);faces=np.array(surface['triangles']);edges=collections.Counter();directed=collections.Counter();vertices+=len(xyz);triangles+=len(faces)
 for t in faces:
  assert len(set(t))==3
  u,v,w=xyz[t];normal=np.cross(v-u,w-u);assert np.linalg.norm(normal)>1e-12
  assert np.dot(normal,(u+v+w)/3)>0
  for i,j in zip(t,np.roll(t,-1)):edges[tuple(sorted((int(i),int(j))))]+=1;directed[int(i),int(j)]+=1
 assert all(n==2 for n in edges.values());assert len(xyz)-len(edges)+len(faces)==2
 assert all(directed[i,j]==directed[j,i]==1 for i,j in edges)
 for q in xyz[::31]:
  actual=density(q);err=abs(actual-surface['density'])/surface['density'];maxerr=max(maxerr,err);assert err<3e-4,(q,err)
proof={'allPassed':True,'surfaces':3,'vertices':vertices,'triangles':triangles,'closedOrientedManifoldMeshes':True,'outwardNondegenerateFaces':True,'independentPoissonDensityChecks':True,'maximumRelativeFiniteDifferenceDensityError':maxerr,'surfacesAreMaterialBoundaries':False,'wholeGoalComplete':False};(D/'density-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

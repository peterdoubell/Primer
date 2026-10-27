"""Measure actual closed renderer faces against volume and similarity formulas."""
from collections import Counter
from pathlib import Path
import hashlib,itertools,json,math,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 states=[dict(mode='mixture',a=a,b=b,batches=n,gap=gap)for a,b,n,gap in itertools.product(range(9),range(9),range(5),[0,.3])]+[dict(mode='similarity',factor=k/4)for k in range(1,9)]
 script="""global.window={};const fs=require('fs');require('./web/spatial-models.js');require('./web/ratio-spatial.js');require('./web/spatial-module-objects.js');const b=JSON.parse(fs.readFileSync('data/module-models.json')).models.find(m=>m.node_id==='math.2.ratio'),p={scenario:'module.math.2.ratio',family:b.family,mode:b.mode,context:b.context,lesson:'Ratio and Proportion'};if(!window.PrimerModuleObjects.ensure({props:p}))throw Error('Ratio companion absent');if(window.PrimerModuleObjects.ensure({props:{...p,scenario:'module.math.2.percent'}}))throw Error('Cross-lesson ratio family accepted');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(s=>window.PrimerSpatial.build(p.scenario,s))));"""
 models=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,input=json.dumps(states),text=True));faces_checked=pieces_checked=pairs_checked=0
 def near(a,b):assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10),(a,b)
 def sub(a,b):return tuple(x-y for x,y in zip(a,b))
 def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def key(p):return tuple(round(v,12)for v in p)
 for m in models:
  s=m['state'];geometry=m['ratioGeometry'];mixture=s['mode']=='mixture';groups={};bounds=[];volume=0
  polygons=[p for p in m['primitives']if p['kind']=='polygon'];references=[p for p in m['primitives']if p.get('ratio_reference')]
  if mixture:
   assert len(references)==12
   vertices={key(p)for r in references for p in r['points']};assert len(vertices)==8
   for axis,dim in enumerate([.2,.5,.5]):near(max(p[axis]for p in vertices)-min(p[axis]for p in vertices),dim)
   assert geometry['totalA']==s['a']*s['batches']and geometry['totalB']==s['b']*s['batches'];assert geometry['total']==(s['a']+s['b'])*s['batches']
   assert geometry['ratioDefined']==bool(s['a']+s['b']);assert geometry['combinedRatioDefined']==bool((s['a']+s['b'])*s['batches'])
  else:assert references==[]
  for face in polygons:groups.setdefault((face.get('ratio_ingredient'),face.get('ratio_batch'))if mixture else face['ratio_shape'],[]).append(face)
  expected_groups=s['batches']*((s['a']>0)+(s['b']>0))if mixture else 2;assert len(groups)==expected_groups
  for identity,rows in groups.items():
   assert len(rows)==6;points={key(p)for row in rows for p in row['points']};assert len(points)==8;center=tuple(sum(p[k]for p in points)/8 for k in range(3));edges=Counter();part=0
   box=tuple((min(p[k]for p in points),max(p[k]for p in points))for k in range(3));bounds.append(box);dims=[hi-lo for lo,hi in box]
   wanted=[s[identity[0]]*.2,.5,.5]if mixture else[x*(s['factor']if identity=='scaled'else 1)for x in [1.2,.5,.8]]
   for x,y in zip(dims,wanted):near(x,y)
   for row in rows:
    ps=row['points'];assert all(math.isfinite(x)for p in ps for x in p)
    for a,b in zip(ps,ps[1:]+ps[:1]):edges[(key(a),key(b))]+=1
    normal=cross(sub(ps[1],ps[0]),sub(ps[2],ps[0]));centroid=tuple(sum(p[k]for p in ps)/4 for k in range(3));assert dot(normal,sub(centroid,center))>0
    for j in range(1,len(ps)-1):part+=dot(ps[0],cross(ps[j],ps[j+1]))/6
    faces_checked+=1
   assert all(n==1 and edges[(b,a)]==1 for(a,b),n in edges.items());near(part,math.prod(wanted));volume+=part;pieces_checked+=1
  for a,b in itertools.combinations(bounds,2):assert not all(min(a[k][1],b[k][1])-max(a[k][0],b[k][0])>1e-10 for k in range(3));pairs_checked+=1
  if mixture:near(volume,(s['a']+s['b'])*s['batches']*.05)
  else:
   near(volume,.48*(1+s['factor']**3));near(geometry['areaFactor'],s['factor']**2);near(geometry['volumeFactor'],s['factor']**3)
 result={'allPassed':True,'states':len(states),'closedOutwardFaceChecks':faces_checked,'pieceVolumeChecks':pieces_checked,'nonoverlapChecks':pairs_checked,'sourceSHA256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['web/ratio-spatial.js','tools/check_ratio_spatial.py']},'wholeGoalComplete':False};print(json.dumps(result))
if __name__=='__main__':main()

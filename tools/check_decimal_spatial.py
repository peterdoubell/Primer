"""Measure the actual decimal spatial family's closed faces and fixed unit scale."""
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
import hashlib,itertools,json,math,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 states=[dict(whole=0,tenths=0,hundredths=0,thousandths=0,**{})]
 for key,maxi in [('whole',3),('tenths',10),('hundredths',10),('thousandths',10)]:
  for n,gap in itertools.product(range(maxi+1),[0,.02,.04]):states.append(dict(whole=0,tenths=0,hundredths=0,thousandths=0,**{'separation':gap})|{key:n})
 for values,gap in itertools.product([(0,0,8,9),(0,7,0,0),(1,2,0,0),(2,3,5,0),(3,4,7,8),(3,10,10,10)], [0,.02,.04]):states.append(dict(zip(['whole','tenths','hundredths','thousandths'],values))|{'separation':gap})
 script="""global.window={};const fs=require('fs');require('./web/spatial-models.js');require('./web/decimal-spatial.js');require('./web/spatial-module-objects.js');const binding=JSON.parse(fs.readFileSync('data/module-models.json')).models.find(m=>m.node_id==='math.2.decimals');const item={props:{scenario:'module.math.2.decimals',family:binding.family,mode:binding.mode,context:binding.context,lesson:'Decimals'}};if(!window.PrimerModuleObjects.ensure(item))throw Error('Exact decimal companion binding absent');if(window.PrimerModuleObjects.ensure({props:{...item.props,scenario:'module.math.2.percent'}}))throw Error('Cross-lesson decimal family accepted');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(s=>window.PrimerSpatial.build(item.props.scenario,s))));"""
 models=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,input=json.dumps(states),text=True));faces_checked=0;pieces_checked=0;pair_checks=0;gap_checks=0;equivalences={}
 def sub(a,b):return tuple(x-y for x,y in zip(a,b))
 def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def key(p):return tuple(round(v,12)for v in p)
 def near(a,b):assert math.isclose(a,b,rel_tol=2e-10,abs_tol=2e-11),(a,b)
 for m in models:
  s=m['state'];expected=Q(s['whole'])+Q(s['tenths'],10)+Q(s['hundredths'],100)+Q(s['thousandths'],1000)
  assert Q(m['baseTen']['decimal'])==expected and m['baseTen']['milliunits']==expected*1000
  reference=[p for p in m['primitives']if p.get('decimal_reference')];assert len(reference)==12
  for line in reference:near(math.dist(*line['points']),1)
  vertices={key(p)for line in reference for p in line['points']};assert len(vertices)==8
  for axis in range(3):near(max(p[axis]for p in vertices)-min(p[axis]for p in vertices),1)
  faces=[p for p in m['primitives']if p['kind']=='polygon'];groups={}
  for face in faces:groups.setdefault((face['decimal_place'],face['decimal_piece']),[]).append(face)
  assert len(groups)==sum(s[k]for k in ['whole','tenths','hundredths','thousandths'])
  volume=0;boxes={}
  for (place,i),rows in groups.items():
   assert len(rows)==6;points={key(p)for row in rows for p in row['points']};assert len(points)==8
   center=tuple(sum(p[k]for p in points)/8 for k in range(3));edges=Counter();part=0
   boxes[(place,i)]=tuple((min(p[k]for p in points),max(p[k]for p in points))for k in range(3))
   dims=sorted(max(p[k]for p in points)-min(p[k]for p in points)for k in range(3));expected_dims={0:[1,1,1],-1:[.1,1,1],-2:[.1,.1,1],-3:[.1,.1,.1]}[place]
   for a,b in zip(dims,expected_dims):near(a,b)
   for row in rows:
    ps=row['points'];assert all(math.isfinite(c)for p in ps for c in p)
    for a,b in zip(ps,ps[1:]+ps[:1]):edges[(key(a),key(b))]+=1
    normal=cross(sub(ps[1],ps[0]),sub(ps[2],ps[0]));centroid=tuple(sum(p[k]for p in ps)/4 for k in range(3));assert dot(normal,sub(centroid,center))>0
    for j in range(1,len(ps)-1):part+=dot(ps[0],cross(ps[j],ps[j+1]))/6
    faces_checked+=1
   assert all(n==1 and edges[(b,a)]==1 for(a,b),n in edges.items());near(part,float(Q(10)**place));volume+=part;pieces_checked+=1
  for (ka,a),(kb,b) in itertools.combinations(boxes.items(),2):
   assert not all(min(a[k][1],b[k][1])-max(a[k][0],b[k][0])>1e-10 for k in range(3)),'Selected blocks must not overlap in volume'
   pair_checks+=1
  for (place,i),box in boxes.items():
   if i and(place,i-1)in boxes:
    axis={0:0,-1:1,-2:0,-3:2}[place];near(box[axis][0]-boxes[(place,i-1)][axis][1],s['separation']);gap_checks+=1
  near(volume,float(expected))
  if sum(s[k]>0 for k in ['whole','tenths','hundredths','thousandths'])==1 and s['separation']==0:equivalences[tuple(s[k]for k in ['whole','tenths','hundredths','thousandths'])]=volume
 for a,b in [((1,0,0,0),(0,10,0,0)),((0,1,0,0),(0,0,10,0)),((0,0,1,0),(0,0,0,10))]:near(equivalences[a],equivalences[b])
 proof={'allPassed':True,'states':len(models),'closedOutwardFaceChecks':faces_checked,'pieceVolumesChecked':pieces_checked,'regroupingVolumeEqualities':3,'nonoverlappingPiecePairsChecked':pair_checks,'exactInspectionGapsChecked':gap_checks,'actualEngineGeometryUsed':True,'appBindingIntegrated':True,'sourceSHA256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['web/decimal-spatial.js','web/spatial-models.js','web/spatial-module-objects.js','data/module-models.json']}};print(json.dumps(proof))
if __name__=='__main__':main()

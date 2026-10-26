"""Independently measure closed fraction-disk meshes from the actual spatial builder."""
from collections import Counter
from fractions import Fraction
import hashlib,itertools,json,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def key(p):return tuple(round(v,12) for v in p)
def polygon_area(points):return sum(norm(cross(sub(points[i],points[0]),sub(points[i+1],points[0])))/2 for i in range(1,len(points)-1))
def signed_volume(points):return sum(dot(points[0],cross(points[i],points[i+1]))/6 for i in range(1,len(points)-1))
def close(a,b):assert math.isclose(a,b,rel_tol=2e-10,abs_tol=2e-10),(a,b)
def main():
 states=[dict(parts=str(n),selected=selected,separation=separation) for n,selected,separation in itertools.product([2,4,8],range(1,9),[0,.1,.2,.3])]
 states += [dict(parts=p,selected=v,separation=w) for p,v,w in [('3',99,99),(2,-1,-1),(None,1.5,.15),(True,'7.5','0.2'),({},None,None),('8',False,'bad'),('4','bad','bad')]]
 script="""global.window={};const fs=require('fs');require('./web/spatial-models.js');require('./web/spatial-module-objects.js');const binding=JSON.parse(fs.readFileSync('data/module-models.json')).models.find(m=>m.node_id==='math.2.fractions');const item={renderer:'spatial-3d',props:{scenario:'module.math.2.fractions',family:binding.family,mode:binding.mode,context:binding.context,lesson:'Fractions'}};if(!window.PrimerModuleObjects.ensure(item))throw Error('Real companion binding absent');const api=window.PrimerSpatial;console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(s=>api.build(item.props.scenario,s))));"""
 models=json.loads(subprocess.run(['node','-e',script],cwd=ROOT,input=json.dumps(states),text=True,capture_output=True,check=True).stdout)
 polygons=0;face_checks=0
 for m in models:
  state=m['state'];assert state['parts'] in ['2','4','8'];n=int(state['parts']);assert isinstance(state['selected'],int) and 1<=state['selected']<=8;assert state['separation'] in [0,.1,.2,.3]
  selected=min(n,state['selected']);expected=float(Fraction(selected,n));assert f'{selected}/{n} = {expected:g} = {100*expected:g}%' in m['readout']
  assert 'separate example' in m['note'] and 'same 96 straight chords' in m['note']
  faces=[f for f in m['primitives'] if f['kind']=='polygon'];assert len(faces)==96+4*n;assert all(0<=f['fraction_sector']<n for f in faces);polygons+=len(faces)
  volumes=[];tops=[];colored_volume=0
  for sector in range(n):
   group=[f for f in faces if f['fraction_sector']==sector];counts=Counter(f['fraction_face'] for f in group);assert counts=={'top':1,'bottom':1,'curve':96//n,'start':1,'end':1}
   mid=(sector+.5)*2*math.pi/n;offset=(state['separation']*math.cos(mid),0,state['separation']*math.sin(mid));inside=(offset[0]+.5*math.cos(mid),-.05,offset[2]+.5*math.sin(mid));edges=Counter();volume=0
   for face in group:
    points=face['points'];assert all(math.isfinite(c) for p in points for c in p)
    for a,b in zip(points,points[1:]+points[:1]):edges[(key(a),key(b))]+=1
    normal=next(cross(sub(points[i],points[0]),sub(points[i+1],points[0])) for i in range(1,len(points)-1) if norm(cross(sub(points[i],points[0]),sub(points[i+1],points[0])))>1e-12)
    center=tuple(sum(p[k] for p in points)/len(points) for k in range(3));assert dot(normal,sub(center,inside))>0,'Every actual face must point outward'
    volume+=signed_volume(points);face_checks+=1
   for (a,b),count in edges.items():assert count==1 and edges[(b,a)]==1,'Every sector edge has one opposite face mate'
   top=next(f['points'] for f in group if f['fraction_face']=='top');bottom=next(f['points'] for f in group if f['fraction_face']=='bottom');assert all(abs(p[1]-.04)<1e-12 for p in top);assert all(abs(p[1]+.14)<1e-12 for p in bottom)
   area=polygon_area(top);close(area,48/n*math.sin(math.pi/48));close(polygon_area(bottom),area);close(volume,.18*area);volumes.append(volume);tops.append(area)
   for point in top:
    radius=math.hypot(point[0]-offset[0],point[2]-offset[2]);assert abs(radius)<1e-12 or abs(radius-1)<1e-12
   color=group[0]['color'];assert all(f['color']==color for f in group);assert color==('#3e7085' if sector<selected else '#e7dfc7')
   if sector<selected:colored_volume+=volume
  close(sum(tops),48*math.sin(math.pi/48));close(sum(volumes),.18*48*math.sin(math.pi/48));close(colored_volume/sum(volumes),expected)
 report={'allPassed':True,'validControlStates':96,'normalizedBoundaryStates':len(models)-96,'closedSectorFaceChecks':face_checks,'polygonsChecked':polygons,'methods':['Independent oriented-edge incidence and outward-face test','Triangulated signed polyhedron volume and polygon area','Common96-chord whole and exact selected-volume ratio across all separations','Exact decimal/percent readout versus Fraction for normalized2/4/8 denominator domain'],'sourceSHA256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['web/spatial-models.js','web/spatial-module-objects.js','data/module-models.json']},'productionVerified':False}
 print(json.dumps(report));return report
if __name__=='__main__':main()

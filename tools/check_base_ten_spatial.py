"""Independent geometry oracle for proposed place, operation and group families."""
from collections import Counter
from pathlib import Path
import hashlib,itertools,json,math,subprocess
R=Path.cwd();D=R/'docs/base-ten-fidelity-review-20261027';states=[]
def add(lesson,state):states.append({'lesson':lesson,'state':state})
values=[0,1,9,10,11,47,58,90,99,100,101,199,999]
for v,representation in itertools.product(values+[1000,1001,9999],['bundled','unbundleTen','unbundleHundred','unbundleThousand']):add('math.1.place-value',{'value':v,'representation':representation})
for a,b in itertools.product(values,repeat=2):
 for phase in ['unregrouped','regrouped']:add('math.1.addition',{'a':a,'b':b,'phase':phase})
for a,b,meaning in itertools.product([v for v in values if v<=100], [v for v in values if v<=100],['takeAway','difference']):add('math.1.subtraction',{'a':a,'b':b,'meaning':meaning})
for a,b,turned in itertools.product(range(13),range(13),['no','yes']):add('math.1.multiplication',{'a':a,'b':b,'turned':turned})
for n,d,mode in itertools.product([0,1,2,5,6,10,11,12,13,14,15,20,47,99,100,143,144],range(13),['share','group']):add('math.1.division',{'total':n,'divisor':d,'meaning':mode})
script="""global.window={};const fs=require('fs');require('./web/spatial-models.js');require('./web/base-ten-core.js');require('./web/base-ten-spatial.js');require('./web/spatial-module-objects.js');const bindings=JSON.parse(fs.readFileSync('data/module-models.json')).models;for(const[id]of Object.entries(window.PrimerBaseTenSpatialFamilies)){const b=bindings.find(b=>b.node_id===id),titles={'place-value':'Place Value',addition:'Addition',subtraction:'Subtraction',multiplication:'Multiplication',division:'Division'},p={scenario:'module.'+id,family:b.family,mode:b.mode,context:b.context,lesson:titles[id.split('.').at(-1)]};if(!window.PrimerModuleObjects.ensure({props:p}))throw Error('Missing exact binding '+id);if(window.PrimerModuleObjects.ensure({props:{...p,scenario:'module.math.2.ratio'}}))throw Error('Cross lesson binding accepted');}console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(r=>window.PrimerSpatial.build('module.'+r.lesson,r.state))));"""
def near(a,b):assert math.isclose(a,b,rel_tol=2e-8,abs_tol=1e-9),(a,b)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def key(p):return tuple(round(v,10)for v in p)
faces_checked=pieces_checked=pair_checks=0;max_primitives=0
for start in range(0,len(states),30):
 models=json.loads(subprocess.check_output(['node','-e',script],cwd=R,input=json.dumps(states[start:start+30]),text=True))
 for row,m in zip(states[start:start+30],models):
  s=m['state'];lesson=row['lesson'];v=m['baseTenGeometry'];groups={};boxes={};total_volume=0;max_primitives=max(max_primitives,len(m['primitives']));assert len(m['primitives'])<=3000
  for face in m['primitives']:
   assert all(math.isfinite(x)for p in face['points']for x in p)
   if face['kind']=='polygon':
    identity=(face.get('base_ten_place'),face.get('base_ten_piece'),face.get('base_ten_role'),face.get('base_ten_group'),face.get('base_ten_index'));groups.setdefault(identity,[]).append(face)
  for identity,faces in groups.items():
   assert len(faces)==6;points={key(p)for f in faces for p in f['points']};assert len(points)==8;bounds=tuple((min(p[k]for p in points),max(p[k]for p in points))for k in range(3));center=tuple(sum(p[k]for p in points)/8 for k in range(3));boxes[identity]=bounds;edges=Counter();volume=0
   p=identity[0];units=1 if p is None else 10**p;expected=[[.2,.2,.2],[2,.2,.2],[2,.2,2],[2,2,2]][p or 0]
   for axis,dim in enumerate(expected):near(bounds[axis][1]-bounds[axis][0],dim)
   for face in faces:
    ps=face['points'];normal=cross(sub(ps[1],ps[0]),sub(ps[2],ps[0]));centroid=tuple(sum(p[k]for p in ps)/4 for k in range(3));assert dot(normal,sub(centroid,center))>0
    for a,b in zip(ps,ps[1:]+ps[:1]):edges[(key(a),key(b))]+=1
    for j in range(1,len(ps)-1):volume+=dot(ps[0],cross(ps[j],ps[j+1]))/6
    faces_checked+=1
   assert all(n==1 and edges[(b,a)]==1 for(a,b),n in edges.items());near(volume,.008*units);total_volume+=volume;pieces_checked+=1
  for a,b in itertools.combinations(boxes.values(),2):assert not all(min(a[k][1],b[k][1])-max(a[k][0],b[k][0])>1e-8 for k in range(3));pair_checks+=1
  if lesson=='math.1.place-value':expected=s['value'];near(v['total'],expected)
  elif lesson=='math.1.addition':expected=s['a']+s['b'];near(v['total'],expected)
  elif lesson=='math.1.subtraction':
   expected=s['a'] if s['meaning']=='takeAway'else s['a']+s['b']
   roles=Counter(faces[0]['base_ten_role']for faces in groups.values())
   if s['meaning']=='takeAway':assert roles['retained']==max(s['a']-s['b'],0)and roles['removed']==min(s['a'],s['b']);assert len(v['ghosts'])==max(s['b']-s['a'],0)
   else:assert roles['first']==s['a']and roles['second']==s['b']
  elif lesson=='math.1.multiplication':
   expected=s['a']*s['b'];by_group=Counter(faces[0]['base_ten_group']for faces in groups.values());rows=s['b']if s['turned']=='yes'else s['a'];cols=s['a']if s['turned']=='yes'else s['b'];assert len(by_group)==(rows if cols else 0);assert all(n==cols for n in by_group.values())
  else:
   if s['divisor']==0:assert v['status']=='undefined'and not groups;expected=0
   else:
    expected=s['total'];q,r=divmod(expected,s['divisor']);group_count=s['divisor']if s['meaning']=='share'else q;group_size=q if s['meaning']=='share'else s['divisor'];grouped=Counter(faces[0]['base_ten_group']for faces in groups.values()if faces[0]['base_ten_role']=='equal-group');assert len(grouped)==(group_count if group_size else 0)and all(n==group_size for n in grouped.values());assert sum(faces[0]['base_ten_role']=='remainder'for faces in groups.values())==r
  near(total_volume,.008*expected)
result={'allPassed':True,'states':len(states),'closedOutwardFaceChecks':faces_checked,'pieceVolumeChecks':pieces_checked,'nonoverlapChecks':pair_checks,'maxPrimitives':max_primitives,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [R/'web/base-ten-core.js',R/'web/base-ten-spatial.js',R/'web/spatial-models.js',R/'web/spatial-module-objects.js',R/'data/module-models.json',Path(__file__)]},'scope':'Current shipped family and exact lesson-binding geometry; reader and delivery checks are separate','wholeGoalComplete':False};print(json.dumps(result))

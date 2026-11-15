'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
globalThis.window={};require('../web/spatial-models.js');require('../web/spatial-module-objects.js');
const binding=JSON.parse(fs.readFileSync('data/module-models.json')).models.find(x=>x.node_id==='math.0.shapes');
assert.equal(binding.family,'plane-shapes');
const item={title:binding.title,props:{scenario:'module.math.0.shapes',family:binding.family,context:binding.context,mode:binding.mode,lesson:'Shapes All Around'}};
assert(window.PrimerModuleObjects.ensure(item));
const difference=(a,b)=>a.map((v,i)=>v-b[i]),dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0);
const distance=(a,b)=>Math.hypot(...difference(a,b)),near=(a,b)=>assert(Math.abs(a-b)<1e-11,`${a} != ${b}`);
let states=0;
for(const shape of ['circle','triangle','square','rectangle'])for(let turn=0;turn<=360;turn+=15)for(let n=5;n<=15;n++){
 const size=n/10,m=window.PrimerSpatial.build(item.props.scenario,{shape,turn,size}),p=m.planeShape;
 const edges=m.primitives.filter(x=>x.shape_part==='boundary'),corners=m.primitives.filter(x=>x.shape_part==='corner');
 const count=shape==='circle'?0:shape==='triangle'?3:4;
 assert.equal(p.corners,count);assert.equal(p.straightSides,count);assert.equal(corners.length,count);
 assert.equal(edges.length,shape==='circle'?360:count);
 edges.forEach((e,i)=>{
  assert.deepEqual(e.points[1],edges[(i+1)%edges.length].points[0]);
  for(const v of e.points){assert(v.every(Number.isFinite));near(v[2],v[1]*Math.tan(25*Math.PI/180));}
 });
 if(shape==='circle'){
  for(const e of edges)for(const v of e.points)near(Math.hypot(...v),size);
  assert(p.maximumCircleChordError<.000058);
  const midpoint=edges[0].points[0].map((v,i)=>(v+edges[0].points[1][i])/2);
  near(size-Math.hypot(...midpoint),p.maximumCircleChordError);
 }else{
  const v=p.vertices,l=v.map((x,i)=>distance(x,v[(i+1)%count]));
  const expected=shape==='triangle'?Math.sqrt(3)*size:shape==='square'?1.6*size:null;
  if(expected)l.forEach(x=>near(x,expected));
  if(count===4){near(l[0],l[2]);near(l[1],l[3]);for(let i=0;i<4;i++)near(dot(difference(v[(i+1)%4],v[i]),difference(v[(i+3)%4],v[i])),0);}
  if(shape==='rectangle'){near(Math.min(...l),1.2*size);near(Math.max(...l),2*size);}
  // The shoelace formula in an independently recovered orthonormal plane
  // checks exact intrinsic area despite camera-independent rigid rotation.
  const xy=v.map(a=>[a[0],a[1]/Math.cos(25*Math.PI/180)]);
  const area=Math.abs(xy.reduce((sum,a,i)=>sum+a[0]*xy[(i+1)%count][1]-a[1]*xy[(i+1)%count][0],0))/2;
  near(area,(shape==='triangle'?3*Math.sqrt(3)/4:shape==='square'?2.56:2.4)*size*size);
 }
 states++;
}
console.log(JSON.stringify({states,allPassed:true,checks:'closed boundaries, true sides and corners, planarity, equal sides, right angles, intrinsic areas, circle radius and chord error'}));

#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
// This executable owns its fake browser globals. Load only these fixed, shipped
// modules through Node's module loader; no file contents become executable input.
const context = { window: {} };
globalThis.window = context.window;
require('../web/spatial-models.js');
require('../web/spatial-math.js');
require('../web/spatial-physical.js');
require('../web/spatial-molecular.js');
require('../web/spatial-cross-subject.js');
require('../web/spatial-radiology.js');
require('../web/spatial-module-objects.js');
const spatial = context.window.PrimerSpatial, objects = context.window.PrimerModuleObjects;
const prior = [...spatial.supported];
const manifest = JSON.parse(fs.readFileSync(path.join(root,'data/module-models.json'),'utf8'));
assert.equal(manifest.version,1);
const nodes = fs.readdirSync(path.join(root,'data/curriculum')).filter(f=>f.endsWith('.json')).flatMap(f=>JSON.parse(fs.readFileSync(path.join(root,'data/curriculum',f),'utf8')).nodes).filter(n=>!n.id.startsWith('rad.'));
assert.equal(manifest.models.length,nodes.length);
assert.deepEqual(manifest.models.map(m=>m.node_id).sort(),nodes.map(n=>n.id).sort());
const nodeMap = new Map(nodes.map(n=>[n.id,n]));
const familyIds = new Map();
function itemFor(binding) {return {title:binding.title,instructions:binding.instructions,props:{scenario:'module.'+binding.node_id,family:binding.family,context:binding.context,mode:binding.mode,lesson:nodeMap.get(binding.node_id).title}};}
for(const binding of manifest.models) {
  const item=itemFor(binding);
  assert.ok(objects.ensure(item),binding.node_id+': exact authored binding');
  assert.ok(objects.ensure(item),binding.node_id+': registration is idempotent');
  assert.equal(objects.ensure({...item,props:{...item.props,family:'untrusted'}}),false);
  assert.equal(objects.ensure({...item,props:{...item.props,context:'changed after registration'}}),false);
  if(!familyIds.has(binding.family)) familyIds.set(binding.family,item.props.scenario);
  const scene=spatial.build(item.props.scenario);
  assert.ok(scene.readout.startsWith(binding.context));
  if(binding.mode==='context') assert.ok(scene.note.startsWith('Physical study context for “'+item.props.lesson+'”.'));
}
assert.deepEqual([...familyIds.keys()].sort(),[...objects.families].sort());
for(const id of prior) assert.ok(spatial.supported.includes(id),'Preserve existing '+id);
for(const value of [null,{}, {props:{}}, {props:{scenario:'constructor'}}, {props:{scenario:'module.rad.3.ct-image',family:'book',mode:'context',context:'x',lesson:'x'}}, {props:{scenario:'module.math.0.counting',family:'book',mode:'invalid',context:'x',lesson:'x'}}])assert.equal(objects.ensure(value),false);
let builds=0,controls=0;
function verify(id,state={}) {
  const scene=spatial.build(id,state);
  assert.ok(scene&&scene.primitives.length>0&&scene.primitives.length<=3000,id+': geometry budget');
  assert.equal(JSON.stringify(scene),JSON.stringify(spatial.build(id,state)),id+': deterministic geometry');
  assert.ok(scene.note.length>30&&scene.readout.length>30&&scene.legend.length>0,id+': explanatory text');
  for(const primitive of scene.primitives){
    for(const point of primitive.points)assert.ok(point.length===3&&point.every(Number.isFinite),id+': finite coordinates');
    if(primitive.radius!==undefined)assert.ok(primitive.radius>0&&Number.isFinite(primitive.radius));
    if(primitive.opacity!==undefined)assert.ok(primitive.opacity>=0&&primitive.opacity<=1);
  }
  const points=scene.primitives.filter(p=>p.kind!=='label').flatMap(p=>p.points.flatMap(point=>p.radius?[-1,1].map(sign=>point.map(v=>v+sign*p.radius)):[point]));
  for(let axis=0;axis<3;axis++)assert.ok(Math.max(...points.map(p=>p[axis]))-Math.min(...points.map(p=>p[axis]))>.04,id+': real spatial extent on axis '+axis);
  builds++;return scene;
}
for(const [family,id] of familyIds){
  const initial=verify(id);let minimum={},maximum={};
  for(const control of spatial.controls(id)){
    const values=control.options?control.options.map(o=>o.value):Array.from({length:Math.floor((control.max-control.min)/control.step+1e-7)+1},(_,i)=>Number((control.min+i*control.step).toFixed(8)));
    const versions=values.map(value=>verify(id,{[control.key]:value}));
    assert.ok(versions.some(scene=>JSON.stringify(scene.primitives)!==JSON.stringify(initial.primitives)),family+': '+control.key+' visibly changes geometry');
    if(!control.options)for(const invalid of [NaN,Infinity,-Infinity,'not a number'])assert.equal(JSON.stringify(verify(id,{[control.key]:invalid})),JSON.stringify(initial),family+': invalid input fallback');
    minimum[control.key]=values[0];maximum[control.key]=values.at(-1);controls++;
  }
  verify(id,minimum);verify(id,maximum);
}
const byFamily=(family,state)=>verify(familyIds.get(family),state);
const near=(a,b,epsilon=1e-8)=>assert.ok(Math.abs(a-b)<epsilon,`${a} != ${b}`);
const C={blue:'#3e7085',teal:'#317e78',gold:'#b98a2f',coral:'#b96652',plum:'#876888',ink:'#263b46'};
const primitives=(scene,kind,color)=>scene.primitives.filter(p=>p.kind===kind&&(!color||p.color===color));
// Quantities and spatial coordinates are independently checked from geometry.
for(const count of [1,12,30])for(const group of [1,4,10])assert.equal(primitives(byFamily('unit-blocks',{count,group}),'polygon').length/6,count);
for(const blue of [0,3,10]){const balls=primitives(byFamily('urn',{blue}),'sphere');assert.equal(balls.length,10);assert.equal(balls.filter(p=>p.color===C.blue).length,blue);}
for(const shape of ['bowl','saddle','plane'])for(const height of [.25,1,1.5]){
  for(const face of primitives(byFamily('surface',{shape,height}),'polygon',C.teal))for(const [x,z,y] of face.points)near(z,height*(shape==='bowl'?x*x+y*y:shape==='saddle'?x*x-y*y:x+y));
}
for(const length of [.8,1.4,2])for(const angle of [-60,0,60]){
  const bob=primitives(byFamily('pendulum',{length,angle}),'sphere',C.coral)[0].points[0];near(Math.hypot(bob[0],bob[1]-1.15,bob[2]),length);near(bob[1]-(1.15-length),length*(1-Math.cos(angle*Math.PI/180)));
}
for(const cells of [1,2,3])assert.equal(primitives(byFamily('lattice',{cells}),'sphere',C.blue).length,(cells+1)**3);
for(const molecule of ['water','carbon-dioxide','methane']){
  const scene=byFamily('molecule',{molecule}),atoms=primitives(scene,'sphere'),other=atoms.slice(1).map(p=>p.points[0]);
  assert.equal(atoms.length,molecule==='water'?3:molecule==='carbon-dioxide'?3:5);
  const angle=Math.acos(other[0].reduce((sum,v,i)=>sum+v*other[1][i],0)/(Math.hypot(...other[0])*Math.hypot(...other[1])))*180/Math.PI;
  near(angle,molecule==='water'?104.5:molecule==='carbon-dioxide'?180:Math.acos(-1/3)*180/Math.PI);
}
for(const pairs of [6,10,14]){
  const scene=byFamily('dna',{pairs,separation:0}),blue=primitives(scene,'sphere',C.blue),coral=primitives(scene,'sphere',C.coral);
  assert.equal(blue.length,pairs);assert.equal(coral.length,pairs);
  blue.forEach((p,i)=>{near(p.points[0][0],-coral[i].points[0][0]);near(p.points[0][1],coral[i].points[0][1]);near(p.points[0][2],-coral[i].points[0][2]);near(Math.hypot(p.points[0][0],p.points[0][2]),.55);});
  // Around +y, x -> -z is the right-hand rotation as height increases.
  assert.ok(blue[1].points[0][1]>blue[0].points[0][1]);assert.ok(blue[1].points[0][2]<blue[0].points[0][2]);
}
for(const phase of [0,90,180,270])for(const inclination of [0,30,60]){
  const point=primitives(byFamily('orbit',{phase,inclination}),'sphere',C.teal)[0].points[0];near(Math.hypot(...point),1.35);
}
for(const latitude of [-75,0,75])for(const longitude of [-180,0,180]){
  const point=primitives(byFamily('globe',{latitude,longitude}),'sphere',C.coral)[0].points[0];near(Math.hypot(...point),1.04);near(point[1],1.04*Math.sin(latitude*Math.PI/180));
}
// Pole reversal reverses every sampled field direction without moving samples.
for(const distance of [1,1.4,1.6]) {
  const normal=primitives(byFamily('magnet',{distance,polarity:'normal'}),'line',C.teal);
  const reversed=primitives(byFamily('magnet',{distance,polarity:'reversed'}),'line',C.teal);
  assert.equal(normal.length,reversed.length);
  for(let i=0;i<normal.length;i+=12)for(let axis=0;axis<3;axis++) {
    near(normal[i].points[0][axis],reversed[i].points[0][axis]);
    near(normal[i+11].points[1][axis]-normal[i].points[0][axis],-(reversed[i+11].points[1][axis]-reversed[i].points[0][axis]));
  }
}
for(const separation of [0,.1,.3]) {
  const scene=byFamily('detector',{separation});
  [C.teal,C.gold,C.plum].forEach((color,i)=>{
    for(const face of primitives(scene,'polygon',color))for(const point of face.points)near(Math.hypot(point[0],point[1]),.4+i*(.3+separation));
  });
}
for(const gap of [.25,.35,.55])for(const distance of [1,1.4,2.2]) {
  const bands=primitives(byFamily('interference',{gap,distance}),'polygon',C.gold);
  assert.equal(bands.length,80);
  bands.forEach((band,i)=>near(band.opacity,bands.at(-1-i).opacity,1e-12));
  assert.ok(Math.max(...bands.map(b=>b.opacity))>.95);
  assert.ok(Math.min(...bands.map(b=>b.opacity))<.1);
}
const circuit=byFamily('circuit',{voltage:12,resistance:3,closed:'yes'});assert.ok(circuit.readout.includes('= 4 A'));assert.ok(byFamily('circuit',{closed:'no'}).readout.includes('current is zero'));
console.log(`Verified ${manifest.models.length} lesson bindings, ${familyIds.size} object families, ${controls} geometric controls and ${builds} deterministic finite builds; quantitative geometry invariants passed.`);

#!/usr/bin/env node
'use strict';
// Build the actual shipped geometry without a DOM. Browser verification remains
// necessary for interactions, framing and visual quality.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = path.resolve(__dirname, '..');
const json = file => JSON.parse(fs.readFileSync(path.join(ROOT,file),'utf8'));
const catalog = json('data/radiology/reporting-models.json');
const expected = json('data/curriculum/11-radiology.json').nodes.filter(n=>n.id.startsWith('rad.')).map(n=>n.id).sort();
const context = vm.createContext({ window:{} });
['spatial-models.js','radiology-reference-models.js'].forEach(file=>vm.runInContext(fs.readFileSync(path.join(ROOT,'web',file),'utf8'),context,{filename:file}));
const api=context.window.PrimerSpatial, wrapper=context.window.PrimerRadiologyReferenceModels;
assert.equal(expected.length,96,'All clinical radiology modules must be included');
assert.deepEqual(Object.keys(catalog).sort(),expected);
assert.deepEqual(Array.from(wrapper.supported).sort(),expected);
assert.equal(api.supported.length,96);
assert.ok(wrapper.families.length>=16,'Require distinct anatomy/acquisition families');
const seenFamilies=new Set(), groupGeometry=new Map();
let builds=0, controls=0, maxPrimitives=0;
function verify(id,state) {
  const scene=api.build(id,state);
  assert.ok(scene && scene.primitives.length>10 && scene.primitives.length<=3000,id+': geometry budget');
  maxPrimitives=Math.max(maxPrimitives,scene.primitives.length);
  assert.equal(JSON.stringify(scene),JSON.stringify(api.build(id,state)),id+': deterministic build');
  assert.ok(scene.readout.length>80 && scene.note.length>100,id+': reporting guidance');
  assert.match(scene.note,/not patient data/);
  assert.match(scene.note,/patient left/);
  assert.match(scene.note,/superior/);
  assert.match(scene.note,/anterior/);
  assert.ok(scene.legend.length>=3);
  scene.primitives.forEach(p=>{
    assert.ok(['polygon','line','sphere','label'].includes(p.kind));
    assert.ok(p.points.length>0);
    p.points.forEach(point=>{
      assert.ok(point.length===3 && point.every(Number.isFinite),id+': finite geometry');
      assert.ok(point.every(v=>Math.abs(v)<=1.8),id+': reasonable model framing');
    });
    if(p.opacity!=null)assert.ok(p.opacity>=0 && p.opacity<=1 && Number.isFinite(p.opacity));
    if(p.width!=null)assert.ok(p.width>0 && Number.isFinite(p.width));
    if(p.kind==='label')assert.ok(p.text.length>0 && p.text.length<40);
  });
  builds++;
  return scene;
}
const renderState=scene=>JSON.stringify({primitives:scene.primitives,readout:scene.readout,legend:scene.legend});
for(const node of expected) {
  const spec=catalog[node];
  assert.equal(spec.scenario,'radiology-reference:'+node);
  assert.equal(JSON.stringify(wrapper.specification(node)),JSON.stringify(spec));
  assert.ok(spec.title.length>12 && spec.instructions.length>50 && spec.reporting_aim.length>50);
  const first=verify(spec.scenario);
  assert.equal(first.state.focus,spec.focus[0]);
  seenFamilies.add(spec.family);
  if(!groupGeometry.has(spec.family))groupGeometry.set(spec.family,JSON.stringify(first.primitives));
  const definitions=Array.from(api.controls(spec.scenario));
  assert.ok(definitions.some(c=>c.key==='focus') && definitions.some(c=>c.key==='plane') && definitions.some(c=>c.key==='position'));
  for(const control of definitions) {
    const values=control.options?Array.from(control.options,o=>o.value):[control.min,(control.min+control.max)/2,control.max];
    const variants=values.map(value=>verify(spec.scenario,{...first.state,[control.key]:value}));
    assert.ok(new Set(variants.map(renderState)).size>1,node+': '+control.key+' changes the displayed model');
    if(!control.options)for(const invalid of [NaN,Infinity,-Infinity,'not a number'])assert.equal(renderState(verify(spec.scenario,{[control.key]:invalid})),renderState(first));
    controls++;
  }
  for(const plane of ['axial','coronal','sagittal'])for(const position of [-1.1,1.1]) {
    const scene=verify(spec.scenario,{plane,position,context:'outline',labels:'all'});
    const axis={axial:1,coronal:2,sagittal:0}[plane];
    const guide=scene.primitives.find(p=>p.kind==='polygon'&&p.opacity===.1&&p.stroke==='#b98a2f');
    assert.ok(guide,node+': section guide');
    guide.points.forEach(p=>assert.equal(p[axis],position));
  }
  const hidden=verify(spec.scenario,{labels:'hide'});
  assert.equal(hidden.primitives.filter(p=>p.kind==='label').length,0);
}
assert.equal(seenFamilies.size,wrapper.families.length);
assert.equal(new Set(groupGeometry.values()).size,seenFamilies.size,'Anatomy families must have distinct geometry');
for(const bad of ['missing','__proto__','constructor',null]) {
  assert.equal(wrapper.specification(bad),null);
  assert.equal(wrapper.render({scenario:bad}),null);
}
assert.equal(wrapper.render(null),null);
// Protect salient spatial relationships rather than only checking text coverage.
const getPoints=(node,focus)=>api.build('radiology-reference:'+node,{focus,labels:'hide'}).primitives
  .filter(p=>p.color==='#b96652').flatMap(p=>p.points);
const pz=getPoints('rad.5.prostate-mri','peripheral');
assert.ok(Math.max(...pz.map(p=>p[2]))<.19,'Peripheral zone remains posterior/lateral, not a full anterior shell');
const tz=getPoints('rad.5.prostate-mri','transition');
assert.ok(tz.some(p=>p[0]<0)&&tz.some(p=>p[0]>0),'Transition zone surrounds the urethral axis');
const anterior=getPoints('rad.5.prostate-mri','stroma');
assert.ok(Math.min(...anterior.map(p=>p[2]))>.4,'Anterior fibromuscular stroma must be anterior');
const liver=api.build('radiology-reference:rad.4.liver',{labels:'all'});
const loc=Object.fromEntries(liver.primitives.filter(p=>p.kind==='label').map(p=>[p.text,p.points[0]]));
assert.ok(loc.I[2]<0&&loc.V[2]>0&&loc.VIII[2]>0&&loc.VI[2]<0&&loc.VII[2]<0,'Couinaud posterior/anterior positions');
assert.ok(loc.II[0]>0&&loc.III[0]>0&&loc.V[0]<0&&loc.VII[0]<0,'Patient-left/right segment positions');
assert.ok(loc.VIII[1]>loc.V[1]&&loc.VII[1]>loc.VI[1],'Superior/inferior right segments');
console.log(JSON.stringify({modules:expected.length,families:seenFamilies.size,controls,builds,maxPrimitives,status:'passed'},null,2));

#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto');
global.window={PrimerPhysicsQftLab:require('../web/physics-qft-lab.js')};
require('../web/spatial-qft.js');require('../web/spatial-models.js');require('../web/spatial-module-objects.js');
const binding=JSON.parse(fs.readFileSync('data/module-models.json','utf8')).models.find(v=>v.node_id==='phys.5.qft');
assert.ok(window.PrimerModuleObjects.ensure({props:{scenario:'module.phys.5.qft',family:binding.family,context:binding.context,mode:binding.mode,lesson:'Quantum field theory'}}));
const build=state=>window.PrimerSpatial.build('module.phys.5.qft',state);
const near=(a,b,message,tol=2e-12)=>assert.ok(Math.abs(a-b)<=tol*Math.max(1,Math.abs(b)),message);
let singletonStates=0,facetStates=0,facets=0,facetProbes=0,maxObservedError=0,maxFaces=0;
for(const massMeV of [.01,.511,10])for(const momentumMeV of [0,1,10])for(const chargeUnits of [-3,0,3]){
 const scene=build({mode:'antiparticle',massMeV,momentumMeV,chargeUnits}),chart=scene.qft.charts[1];
 const marks=scene.primitives.filter(p=>p.fidelity_kind==='qft_singleton_curve'&&p.panel===1);
 assert.equal(marks.length,2,'Both physical excitation series must actually emit glyphs');
 const expected={particle:chargeUnits,antiparticle:-chargeUnits};
 for(const [key,charge] of Object.entries(expected)){
  const p=marks.find(p=>p.key===key);assert.ok(p&&p.kind==='sphere'&&p.radius>0&&p.opacity>0);
  const xyz=p.points[0];near((xyz[0]-chart.origin[0])/chart.xGain+chart.xmin,charge,key+' actual emitted charge');
  near((xyz[1]-chart.origin[1])/chart.yGain+chart.ymin,Math.hypot(massMeV,momentumMeV),key+' actual positive excitation');
  assert.ok(scene.primitives.some(label=>label.kind==='label'&&label.text===p.label));
 }
 assert.notEqual(marks[0].color,marks[1].color);assert.notEqual(marks[0].radius,marks[1].radius);singletonStates++;
}
for(const gapUm of [.1,.5,4.8,5])for(const normalMode of [1,6])for(const parallelK of [0,1,10]){
 const scene=build({mode:'casimir',gapUm,normalMode,parallelK}),e=scene.qft.extra.find(v=>v.kind==='standing-factor');
 const faces=scene.primitives.filter(p=>p.fidelity_kind==='qft_standing_factor');
 assert.equal(faces.length,2*e.nx*e.nz);assert.equal(e.errorBudget,.02);assert.ok(e.interpolationErrorBound<=.02+1e-15);
 assert.ok(e.nx>=16&&e.nz>=24);assert.ok(faces.length<=47500);maxFaces=Math.max(maxFaces,faces.length);
 const phaseX=parallelK*gapUm,phaseZ=normalMode*Math.PI,bound=(phaseX/e.nx+phaseZ/e.nz)**2/8;
 near(e.interpolationErrorBound,bound,'Conservative phase variance bound');
 for(const face of faces){
  assert.equal(face.points.length,3,'Emitted field display facets are actual triangles');
  const vertices=face.points.map(p=>({x:(p[0]-e.origin[0])/e.xGain,z:(p[2]-e.origin[2])/e.zGain,f:(p[1]-e.origin[1])/e.factorGain}));
  for(const v of vertices)near(v.f,Math.sin(phaseZ*v.z)*Math.cos(phaseX*v.x),'Every actual emitted vertex is the declared factor');
  for(const weights of [[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3,1/3,1/3]]){
   const sum=key=>vertices.reduce((v,p,i)=>v+weights[i]*p[key],0),error=Math.abs(sum('f')-Math.sin(phaseZ*sum('z'))*Math.cos(phaseX*sum('x')));
   assert.ok(error<=bound+2e-12,'Actual emitted facet interpolation must satisfy its full-control error budget');
   maxObservedError=Math.max(maxObservedError,error);facetProbes++;
  }facets++;
 }facetStates++;
}
const q=window.PrimerPhysicsQftLab;
for(const angleDeg of [0,Number.MIN_VALUE,1e-200,1e-7,90,180])for(const momentumMeV of [0,Number.MIN_VALUE,1,10]){
 const m=q.build({mode:'scattering',angleDeg,momentumMeV}),d=m.current,zero=angleDeg===0||momentumMeV===0;
 assert.equal(d.zeroTransfer,zero);assert.equal(d.photonOnShell,zero);
 if(!zero){assert.equal(d.transferClassification,'spacelike');assert.ok(d.t<=0);if(d.t===0){assert.ok(d.tUnderflow);assert.ok(m.readout.includes('underflows Float64')&&m.readout.includes('must not be read as an on-shell'));assert.ok(Number.isFinite(d.log10AbsT));}}
 if(angleDeg===180)assert.ok(d.u===0);
 if(angleDeg===1e-7&&momentumMeV===1){const expected=-4*Math.sin(Math.PI*angleDeg/360)**2;assert.ok(Math.abs((d.t-expected)/expected)<1e-14);}
 for(const point of m.panels[1].curves[0].points){const expected=-4*momentumMeV**2*Math.sin(Math.PI*point.x/360)**2;near(point.y,expected,'Stable actual plotted invariant');}
}
for(const [id,familyId,linkedStateKey] of [['unknown-qft-budget','qft-observable-geometry','phys.5.qft'],['module.phys.5.other-family','unknown-family','phys.5.qft']]){
 window.PrimerSpatial.register({[id]:{initial:{mode:'casimir'},controls:[],familyId,linkedStateKey,primitiveBudget:()=>50000,build(state,g){for(let n=0;n<3001;n++)g.sphere([0,0,0],.1,'#000000');return {};}}});
 assert.throws(()=>window.PrimerSpatial.build(id),/3D scene exceeds geometry limit/,'Unknown scene or family retains the original 3000 bound');
}
assert.throws(()=>window.PrimerSpatial.register({'module.phys.5.qft':{familyId:'unknown-family'}}),/Duplicate spatial scene/,'Existing trusted QFT identity cannot be replaced');
global.document={createElement(){throw new Error('QA sentinel: maximum-mesh initial bounds completed');},createElementNS(){throw new Error('QA sentinel: maximum-mesh initial bounds completed');}};
assert.throws(()=>window.PrimerSpatial.render({props:{scenario:'module.phys.5.qft'},title:'QFT',instructions:'test'},{state:{mode:'casimir',gapUm:5,parallelK:10,normalMode:6}}),/QA sentinel: maximum-mesh initial bounds completed/,'Maximum mesh must finish real renderer bounds without argument-spread overflow');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
console.log(JSON.stringify({status:'pass',singletonStates,facetStates,facets,facetProbes,maxObservedError,maxFaces,errorBudget:.02,runtime_sha256:sha('web/physics-qft-lab.js'),adapter_sha256:sha('web/spatial-qft.js')},null,2));

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
context.window.PrimerPhysicsThermalLab = require('../web/physics-thermal-lab.js');
context.window.PrimerPhysicsBuoyancyLab = require('../web/physics-buoyancy-lab.js');
context.window.PrimerPhysicsPhaseLab = require('../web/physics-phase-lab.js');
context.window.PrimerPhysicsCycleLab = require('../web/physics-cycle-lab.js');
context.window.PrimerMathOperatorLab = require('../web/math-operator-lab.js');
context.window.PrimerPhysicsEnsembleLab = require('../web/physics-ensemble-lab.js');
context.window.PrimerMathCurvatureLab = require('../web/math-curvature-lab.js');
context.window.PrimerPhysicsConstraintsLab = require('../web/physics-constraints-lab.js');
context.window.PrimerMathComplexLab = require('../web/math-complex-lab.js');
context.window.PrimerPhysicsQuantumLab = require('../web/physics-quantum-lab.js');
context.window.PrimerMathTopologyLab = require('../web/math-topology-lab.js');
context.window.PrimerPhysicsRelativityLab = require('../web/physics-relativity-lab.js');
context.window.PrimerMathAlgebraLab = require('../web/math-algebra-lab.js');
context.window.PrimerPhysicsQftLab = require('../web/physics-qft-lab.js');
require('../web/spatial-qft.js');
context.window.PrimerPhysicsQuantumInfoLab = require('../web/physics-quantum-info-lab.js');
context.window.PrimerMathLogicLab = require('../web/math-logic-lab.js');
context.window.PrimerMathNumberTheoryLab = require('../web/math-number-theory-lab.js');
context.window.PrimerNumberTheoryDiagrams = require('../web/number-theory-diagrams.js');
require('../web/spatial-number-theory.js');
require('../web/spatial-number-theory-relations.js');
context.window.PrimerPhysicsMaxwellLab = require('../web/physics-maxwell-lab.js');
context.window.PrimerPhysicsCosmologyLab = require('../web/physics-cosmology-lab.js');
require('../web/spatial-logic.js');
require('../web/spatial-maxwell.js');
require('../web/spatial-cosmology.js');
require('../web/spatial-algebra.js');
require('../web/spatial-quantum-information.js');
require('../web/spatial-fidelity.js');
context.window.PrimerMathNumericalLab = require('../web/math-numerical-lab.js');
context.window.PrimerMathConvergenceLab = require('../web/math-convergence-lab.js');
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
  if(binding.family==='number-theory-exact-traces') {
    assert.equal(binding.node_id,'math.4.numtheory');
    assert.equal(item.props.lesson,'Number Theory'); assert.equal(binding.mode,'model');
    assert.ok(scene.readout.startsWith(binding.context));
    assert.ok(scene.readout.includes(window.PrimerMathNumberTheoryLab.build(scene.state).readout));
    assert.equal(objects.ensure({...item,props:{...item.props,scenario:'module.math.5.logic'}}),false);
    assert.equal(objects.ensure({...item,props:{...item.props,lesson:'Other lesson'}}),false);
  } else assert.ok(scene.readout.startsWith(binding.context));
  if(binding.mode==='context') assert.ok(scene.note.startsWith('Physical study context for “'+item.props.lesson+'”.'));
}
assert.deepEqual([...familyIds.keys()].sort(),[...objects.families].sort());
for(const id of prior) assert.ok(spatial.supported.includes(id),'Preserve existing '+id);
for(const value of [null,{}, {props:{}}, {props:{scenario:'constructor'}}, {props:{scenario:'module.rad.3.ct-image',family:'book',mode:'context',context:'x',lesson:'x'}}, {props:{scenario:'module.math.0.counting',family:'book',mode:'invalid',context:'x',lesson:'x'}}])assert.equal(objects.ensure(value),false);
let builds=0,controls=0;
function verify(id,state={}) {
  const scene=spatial.build(id,state);
  assert.ok(scene&&scene.primitives.length>0&&scene.primitives.length<=(id==='module.phys.5.qft'&&scene.qft?.state?.mode==='casimir'?50000:3000),id+': geometry budget');
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
  if(family==='number-theory-exact-traces') {
    assert.equal(id,'module.math.4.numtheory');
    const lab=window.PrimerMathNumberTheoryLab,diagrams=window.PrimerNumberTheoryDiagrams;
    for(const control of spatial.controls(id)) {
      const mode=control.visibleWhen?.mode?.[0]||lab.initial.mode;
      const values=control.options?control.options.map(o=>o.value):control.key==='diagramPage'?[0,1,5000,10000]:
        [String(control.min),String(BigInt(control.min)+BigInt(control.step)),String((BigInt(control.min)+BigInt(control.max))/2n),String(control.max)];
      for(const value of values) {
        const scene=verify(id,{mode,[control.key]:value});
        const expected=diagrams.windowGraph(diagrams.graph(scene.state),scene.state.diagramPage);
        assert.deepEqual(scene.numberTheoryRelations.window.nodes,expected.nodes);
        assert.deepEqual(scene.numberTheoryRelations.window.edges,expected.edges);
        assert.equal(scene.primitives.filter(p=>p.nt_relation_kind==='node').length,expected.nodes.length);
        assert.equal(scene.primitives.filter(p=>p.nt_relation_kind==='edge').length,expected.edges.length);
      }
      if(!control.options)for(const value of [NaN,Infinity,-Infinity,'not an integer']) {
        const scene=verify(id,{mode,[control.key]:value});
        assert.deepEqual(scene.state,diagrams.normalize({mode,[control.key]:value}));
      }
      controls++;
    }
    continue;
  }
  for(const control of spatial.controls(id)){
    const coordinated=['complex-function-domain','quantum-state-geometry','topology-open-set-geometry','relativistic-event-geometry','algebra-operation-geometry','quantum-information-geometry','logic-witness-geometry','maxwell-field-geometry','cosmology-chart-geometry','qft-observable-geometry'].includes(family);
    // Large batch/seed ranges have no useful million-state exhaustive sweep.
    // Their distributions and geometry have separate independent oracles.
    const values=control.options?control.options.map(o=>o.value):coordinated
      ? [...new Set([control.min,Math.min(control.max,control.min+control.step),(control.min+control.max)/2,control.max])]
      : Array.from({length:Math.floor((control.max-control.min)/control.step+1e-7)+1},(_,i)=>Number((control.min+i*control.step).toFixed(8)));
    const versions=values.map(value=>verify(id,{[control.key]:value}));
    if(family==='operator-coordinate-graph' && ['realization','probe'].includes(control.key)) {
      // Cropping the same coefficient pairs must not fabricate a visible change
      // when a domain or spectral probe changes only the full operator ledger.
      for(const scene of versions) assert.deepEqual(scene.primitives,initial.primitives);
      assert.ok(versions.some(scene=>scene.readout!==initial.readout),family+': '+control.key+' changes its exact ledger');
      if(control.key==='realization') {
        assert.equal(versions[0].operator.selected.output.offscreenSquared.exact,'1');
        assert.equal(versions[1].operator.selected.output.normSquared.exact,'0');
      } else {
        assert.deepEqual(versions.map(v=>v.operator.lambda.exact),['0','2/5','1']);
        assert.deepEqual(versions.map(v=>v.operator.selected.residual.normSquared.exact),['1','29/25','2']);
      }
    } else if(family==='operator-coordinate-graph' && control.key==='second') {
      // The canonical e_N fixture puts its next coefficient beyond the crop.
      // Retain that crop while verifying the full hidden-coordinate ledger.
      for(let i=0;i<versions.length;i++) {
        assert.deepEqual(versions[i].primitives,initial.primitives);
        assert.equal(versions[i].operator.selected.input.offscreenSquared.value,(values[i]/4)**2);
        assert.equal(versions[i].operator.selected.output.offscreenSquared.value,1+(values[i]/4)**2);
      }
      // Move the same sparse input inside the view to test visible dependence.
      const visible=verify(id,{position:'first'});
      const visibleVersions=values.map(value=>verify(id,{position:'first',second:value}));
      assert.ok(visibleVersions.some(scene=>JSON.stringify(scene.primitives)!==JSON.stringify(visible.primitives)),family+': second changes visible coefficients when k = 1');
    } else if(coordinated && ((control.visibleWhen && !Object.entries(control.visibleWhen).every(([key,allowed])=>allowed.includes(initial.state[key]))) || (control.visibleWhenAny && !control.visibleWhenAny.some(group=>Object.entries(group).every(([key,allowed])=>allowed.includes(initial.state[key])))))) {
      // Inactive station parameters persist for the next station; they do not
      // fabricate geometry in the current station.
      for(const scene of versions)assert.deepEqual(scene.primitives,initial.primitives);
      const field={'complex-function-domain':'complex','quantum-state-geometry':'quantum','topology-open-set-geometry':'topology','relativistic-event-geometry':'relativity','algebra-operation-geometry':'algebra','quantum-information-geometry':'quantumInfo','logic-witness-geometry':'logic','maxwell-field-geometry':'maxwell','cosmology-chart-geometry':'cosmology','qft-observable-geometry':'qft'}[family];
      const api={'complex-function-domain':window.PrimerMathComplexLab,'quantum-state-geometry':window.PrimerPhysicsQuantumLab,'topology-open-set-geometry':window.PrimerMathTopologyLab,'relativistic-event-geometry':window.PrimerPhysicsRelativityLab,'algebra-operation-geometry':window.PrimerMathAlgebraLab,'quantum-information-geometry':window.PrimerPhysicsQuantumInfoLab,'logic-witness-geometry':window.PrimerMathLogicLab,'maxwell-field-geometry':window.PrimerPhysicsMaxwellLab,'cosmology-chart-geometry':window.PrimerPhysicsCosmologyLab,'qft-observable-geometry':window.PrimerPhysicsQftLab}[family];
      values.forEach((value,i)=>assert.deepEqual(versions[i][field].state,api.normalize({[control.key]:value})));
    } else if(family==='qft-observable-geometry'&&control.key==='areaMm2') {
      for(const scene of versions)assert.deepEqual(scene.primitives,initial.primitives);
      assert.ok(versions.some(scene=>scene.readout!==initial.readout));
    } else if(family==='algebra-operation-geometry'&&control.key==='tableCode'&&initial.state.axiomsSystem!=='custom') {
      for(const scene of versions)assert.deepEqual(scene.primitives,initial.primitives);
      const custom=values.map(value=>verify(id,{axiomsSystem:'custom',tableCode:value}));
      assert.ok(custom.some(scene=>JSON.stringify(scene.primitives)!==JSON.stringify(custom[0].primitives)));
    } else if(family==='algebra-operation-geometry'&&control.key==='sylowStep') {
      for(const scene of versions)assert.deepEqual(scene.primitives,initial.primitives);
      values.forEach((value,i)=>assert.deepEqual(versions[i].algebra.state,window.PrimerMathAlgebraLab.normalize({sylowStep:value})));
    } else if(family==='topology-open-set-geometry'&&control.key==='familyMask') {
      assert.ok(versions.some(scene=>JSON.stringify(scene.primitives)!==JSON.stringify(initial.primitives)));
    } else if(family==='quantum-state-geometry'&&control.key==='n'&&initial.state.wellState==='superposition') {
      for(const scene of versions){assert.deepEqual(scene.primitives,initial.primitives);assert.equal(scene.quantum.current.coefficients.length,2);}
      values.forEach((value,i)=>assert.equal(versions[i].state.n,Math.round(value)));
    } else assert.ok(versions.some(scene=>JSON.stringify(scene.primitives)!==JSON.stringify(initial.primitives)),family+': '+control.key+' visibly changes geometry');
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

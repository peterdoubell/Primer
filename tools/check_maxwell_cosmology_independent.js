#!/usr/bin/env node
'use strict';
// Independent review of the physical values actually passed through the shipped
// geometry engine. Audit records alone do not establish that a curve was drawn.
const assert = require('node:assert/strict');
global.window = {};
const maxwell = require('../web/physics-maxwell-lab.js');
const cosmos = require('../web/physics-cosmology-lab.js');
window.PrimerPhysicsMaxwellLab = maxwell;
window.PrimerPhysicsCosmologyLab = cosmos;
const mf = require('../web/spatial-maxwell.js');
const cf = require('../web/spatial-cosmology.js');
require('../web/spatial-models.js');
const spatial = window.PrimerSpatial;
for (const [id, family] of [['review-maxwell', mf], ['review-cosmology', cf]]) {
  spatial.register({[id]: {...family, initial: family.initialFactory(), controls: family.controlsFactory()}});
}
const norm = p => Math.hypot(...p), dot = (a,b) => a.reduce((s,x,i) => s+x*b[i],0);
const mul = (p,a) => p.map(x=>x*a), add = (a,b) => a.map((x,i)=>x+b[i]);
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function near(a,b,scale=0) {
  assert.ok(Number.isFinite(a)&&Number.isFinite(b));
  assert.ok(Math.abs(a-b) <= 3e-12*Math.max(Math.abs(a),Math.abs(b),scale,Number.MIN_VALUE), `${a} != ${b}`);
}
function point(a,b) {assert.equal(a.length,b.length); a.forEach((x,i)=>near(x,b[i],1));}
const MU = 1.25663706127e-6, C=299792458, EPS=1/(MU*C*C);
let maxwellStates=0, cosmologyStates=0, fieldVectors=0, engineArrowShafts=0, surfaceFaces=0, chartPoints=0, markers=0;

function physicalField(rec,s,d) {
  const p=rec.positionM, r=norm(p), rho=Math.hypot(p[0],p[1]);
  if(rec.key==='magnetic_B') {
    const M=s.magnetizationKA*1000, a=s.magnetRadiusM;
    if(r<a)return [0,0,2*MU*M/3];
    const moment=[0,0,4*Math.PI*a**3*M/3], n=mul(p,1/r);
    return mul(add(mul(n,3*dot(moment,n)),mul(moment,-1)),MU/(4*Math.PI*r**3));
  }
  if(rec.key==='electric_E') {
    const Q=s.chargeNC*1e-9, a=s.chargeRadiusM;
    if(!r)return [0,0,0];
    const enclosed=Q*Math.min(1,(r/a)**3);
    return mul(p,enclosed/(4*Math.PI*EPS*r**3));
  }
  if(['faraday_E','capacitor_B','coax_B'].includes(rec.key)) {
    let circulation;
    if(rec.key==='faraday_E')circulation=-s.magneticRateTS*Math.PI*Math.min(rho*rho,s.solenoidRadiusM**2);
    if(rec.key==='capacitor_B')circulation=MU*s.chargingCurrentA*Math.min(1,rho*rho/s.plateRadiusM**2);
    if(rec.key==='coax_B') {
      const a=d.aM,b=d.bM,c=d.cM;
      const core=s.coaxCurrentA*Math.min(1,rho*rho/(a*a));
      const returnPart=-s.coaxCurrentA*s.returnFraction*Math.min(1,Math.max(0,rho*rho-b*b)/(c*c-b*b));
      circulation=MU*(core+returnPart);
    }
    return rho?[-circulation*p[1]/(2*Math.PI*rho*rho),circulation*p[0]/(2*Math.PI*rho*rho),0]:[0,0,0];
  }
  if(rec.key==='capacitor_E')return [0,0,s.plateChargeNC*1e-9/(EPS*Math.PI*s.plateRadiusM**2)];
  if(rec.key==='capacitor_feed_current')return [0,0,s.chargingCurrentA];
  if(rec.key==='coax_core_signed_total_current')return [0,0,s.coaxCurrentA];
  if(rec.key==='coax_return_signed_total_current')return [0,0,-s.coaxCurrentA*s.returnFraction];
  if(rec.key.startsWith('wave_')) {
    const f=s.frequencyTHz*1e12, v=C/Math.sqrt(s.epsilonFactor*s.muFactor), dir=s.direction==='forward'?1:-1;
    const phase=2*Math.PI*(p[2]*f/v-dir*s.waveCycles), theta=s.polarizationDeg*Math.PI/180;
    const E=mul([Math.cos(theta),Math.sin(theta),0],s.fieldAmplitudeVM*Math.cos(phase));
    const B=mul(cross([0,0,dir],E),1/v);
    return rec.key==='wave_E'?E:rec.key==='wave_B'?B:mul(cross(E,B),1/(MU*s.muFactor));
  }
  if(rec.key==='radiation_mean_Poynting') {
    const n=mul(p,1/r), sintheta=Math.hypot(n[0],n[1]);
    const I=s.drive==='ac'?s.dipoleCurrentA:0, lambda=C/(s.dipoleFrequencyMHz*1e6), length=s.dipoleLengthFraction*lambda;
    const E=MU*C*(2*Math.PI/lambda)*I*length*sintheta/(4*Math.PI*r);
    // The exact axis has zero radiation; floating sin(pi) is not a physical field.
    return mul(n,(sintheta<1e-14?0:E*E/(2*MU*C)));
  }
  if(rec.key==='radiation_E'||rec.key==='radiation_B') {
    const theta=s.radiationAngleDeg*Math.PI/180, sine=[0,180].includes(s.radiationAngleDeg)?0:Math.sin(theta);
    const lambda=C/(s.dipoleFrequencyMHz*1e6), E=s.drive==='ac'?MU*C*(2*Math.PI/lambda)*s.dipoleCurrentA*s.dipoleLengthFraction*lambda*sine/(4*Math.PI*d.radiusM):0;
    return rec.key==='radiation_E'?mul([Math.cos(theta),0,-Math.sin(theta)],E):[0,E/C,0];
  }
  assert.fail('Unreviewed physical field '+rec.key);
}

const maxwellCases=maxwell.stations.flatMap(([mode])=>[
  {mode}, ...maxwell.controls.filter(c=>c.modes.includes(mode)).flatMap(c=>[{mode,[c.key]:c.min},{mode,[c.key]:c.max}]),
]);
maxwellCases.push({mode:'capacitor',capacitorLoopRatio:.5,chargingCurrentA:-5},
 {mode:'coax',coaxCurrentA:-4,returnFraction:1.25},
 {mode:'wave',direction:'backward',polarizationDeg:37,waveCycles:.173},
 {mode:'radiation',radiationAngleDeg:47,drive:'ac'},
 {mode:'radiation',radiationAngleDeg:0,drive:'ac'}, {mode:'radiation',drive:'dc'},
 {mode:'magnetic',magnetizationKA:5e-324},{mode:'wave',fieldAmplitudeVM:1e-305});
for(const raw of maxwellCases) {
 const scene=spatial.build('review-maxwell',raw),s=scene.state,d=scene.maxwell.current;
 assert.deepEqual(s,maxwell.normalize(raw));
 for(const r of scene.maxwell.primitives) {
  if(r.kind==='field') {
   const expected=physicalField(r,s,d);let scale=Math.max(norm(expected),norm(r.vector));
   // Independent phase evaluation can land a few ulps on opposite sides of an
   // exact cosine node. Bound error by the physical peak, never by arbitrary SI 1.
   if(r.key.startsWith('wave_')) {
    const speed=C/Math.sqrt(s.epsilonFactor*s.muFactor),e=s.fieldAmplitudeVM,b=e/speed;
    scale=Math.max(scale,r.key==='wave_E'?e:r.key==='wave_B'?b:e*b/(MU*s.muFactor));
   }
   expected.forEach((x,i)=>near(x,r.vector[i],scale)); fieldVectors++;
   const start=add(mul(r.positionM,r.positionGain),r.origin),end=add(start,mul(expected,r.fieldGain));
   point(r.start,start);point(r.end,end);
   const shafts=scene.primitives.filter(p=>p.kind==='line'&&p.fidelity_kind===r.key&&p.source_index===r.index);
   if(norm(add(end,mul(start,-1)))<1e-8)assert.equal(shafts.length,0);
   else {
    assert.equal(shafts.length,12);
    shafts.forEach((p,i)=> {point(p.points[0],add(start,mul(add(end,mul(start,-1)),i/12)));point(p.points[1],add(start,mul(add(end,mul(start,-1)),(i+1)/12)));});
    const first=scene.primitives.indexOf(shafts[0]);
    for(const head of scene.primitives.slice(first+12,first+18)){assert.equal(head.kind,'polygon');point(head.points[2],end);}
    engineArrowShafts+=12;
   }
  }
  if(r.kind==='curve'||r.kind==='field_endpoint_curve') {
   const actual=scene.primitives.filter(p=>p.kind==='line'&&p.fidelity_kind===r.key);
   // Repeated meridians/circles have the same kind. Every recorded curve must
   // appear in full as one real engine line, without relying on record labels.
   assert.ok(actual.some(p=>JSON.stringify(p.points)===JSON.stringify(r.points)));
  }
  if(r.kind==='surface') {
   const actual=scene.primitives.filter(p=>p.kind==='polygon'&&p.fidelity_kind===r.key);
   assert.equal(actual.length,r.nu*r.nv);
   for(let u=0;u<r.nu;u++)for(let v=0;v<r.nv;v++) {
    const expected=[r.points[u][v],r.points[u+1][v],r.points[u+1][v+1],r.points[u][v+1]];
    actual[u*r.nv+v].points.forEach((p,i)=>point(p,expected[i]));surfaceFaces++;
   }
  }
  if(r.kind==='surface_normal') {
   const expected=r.key.includes('cut')||r.key.includes('annulus')?[0,0,-1]:r.key.includes('gaussian')?[1,0,0]:[0,0,1];
   assert.deepEqual(r.normal,expected);
   const start=mul(r.positionM,r.positionGain),end=add(start,mul(expected,.45));
   const shafts=scene.primitives.filter(p=>p.kind==='line'&&p.fidelity_kind===r.key);
   assert.equal(shafts.length,12);point(shafts[0].points[0],start);point(shafts.at(-1).points[1],end);
  }
 }
 if(s.mode==='capacitor') {
  const surfaces=new Map(scene.maxwell.surfaces.map(r=>[r.key,r]));
  const gap=surfaces.get('gap_spanning_disk'),annulus=surfaces.get('wire_surface_opposite_annulus'),cylinder=surfaces.get('wire_surface_outer_cylinder'),lower=surfaces.get('wire_surface_lower_disk');
  gap.sourceSI.at(-1).forEach((p,i)=>point(p,annulus.sourceSI[0][i]));
  annulus.sourceSI.at(-1).forEach((p,i)=>point(p,cylinder.sourceSI[0][i]));
  cylinder.sourceSI.at(-1).forEach((p,i)=>point(p,lower.sourceSI.at(-1)[i]));
  const correction=-s.chargingCurrentA*(Math.max(0,Math.min(d.plateRadiusM,Math.hypot(...annulus.sourceSI.at(-1)[0]))**2-d.loopRadiusM**2)/d.plateRadiusM**2);
  near(d.wireSurfaceDisplacementA,correction,Math.abs(s.chargingCurrentA));
  const normals=scene.maxwell.primitives.filter(p=>p.kind==='surface_normal');
  assert.deepEqual(normals.find(p=>p.key==='gap_surface_normal').normal,[0,0,1]);
  assert.deepEqual(normals.find(p=>p.key==='wire_lower_disk_normal').normal,[0,0,1]);
  if(annulus.sourceSI.at(-1)[0][0]>d.loopRadiusM)assert.deepEqual(normals.find(p=>p.key==='wire_annulus_normal').normal,[0,0,-1]);
 }
 assert.ok(scene.primitives.length<=3000);maxwellStates++;
}

const cosmosCases=cosmos.stations.flatMap(([mode])=>[{mode},...cosmos.controls.filter(c=>c.modes.includes(mode)).flatMap(c=>[{mode,[c.key]:c.min},{mode,[c.key]:c.max}])]);
cosmosCases.push(...cosmos.choices[0].options.map(([bhView])=>({mode:'blackhole',bhView})),
 ...cosmos.presets.map(p=>p[2]), {mode:'expansion',omegaM:1,omegaR:0,omegaLambda:0},
 {mode:'expansion',omegaM:1,omegaR:0,omegaLambda:1e-16},
 {mode:'horizons',omegaM:0,omegaR:0,omegaLambda:1},
 {mode:'horizons',omegaM:0,omegaR:0,omegaLambda:0},
 {mode:'expansion',omegaM:1.5,omegaR:0,omegaLambda:0,scaleFactor:3},
 {mode:'blackhole',bhView:'infall',radiusRs:.8});
for(const raw of cosmosCases) {
 const scene=spatial.build('review-cosmology',raw),s=scene.state,core=cosmos.build(raw);
 assert.deepEqual(s,core.state);
 scene.cosmology.panels.forEach((p,index)=> {
  const actual=scene.primitives.filter(x=>x.kind==='line'&&x.fidelity_kind==='cosmology_calibrated_curve'&&x.panel===index);
  assert.equal(actual.length,core.panels[index].curves.filter(c=>c.points.length>1).length);
  for(const curve of p.curves) {
   const original=core.panels[index].curves.find(c=>c.key===curve.key);
   if(original.points.length<=1)continue;
   const primitive=actual.find(x=>x.key===curve.key); assert.ok(primitive);
   assert.equal(primitive.points.length,original.points.length);
   original.points.forEach((q,j)=> {point(primitive.points[j],add([q.x*p.xGain,(q.y-p.yOffset)*p.yGain,0],p.origin));chartPoints++;});
  }
  const dots=scene.primitives.filter(x=>x.fidelity_kind==='cosmology_calibrated_marker'&&x.panel===index);
  assert.equal(dots.length,core.panels[index].markers.length);
  for(const marker of core.panels[index].markers) {
   const actual=dots.find(x=>x.key===marker.key); assert.ok(actual);
   point(actual.points[0],add([marker.x*p.xGain,(marker.y-p.yOffset)*p.yGain,0],p.origin));markers++;
  }
 });
 for(const t of scene.cosmology.primitives.filter(p=>p.kind==='tensor_component')) {
  const actual=scene.primitives.find(p=>p.fidelity_kind==='orthonormal_tensor_component'&&p.tensor===t.tensor&&p.row===t.row&&p.col===t.col);
  assert.ok(actual);point(actual.points[0],add([t.row,t.col,t.value*t.gain],t.origin));
 }
 if(s.mode==='expansion') {
  const galaxies=scene.primitives.filter(p=>p.fidelity_kind==='flat_flrw_comoving_galaxy');
  assert.equal(galaxies.length,core.current.omegaK===0&&core.current.E!==null?27:0);
  for(const g of galaxies)g.properMpc.forEach((x,i)=>near(x,g.comovingMpc[i]*s.scaleFactor));
 }
 if(s.mode==='horizons') {
  const rings=scene.primitives.filter(p=>p.fidelity_kind==='radial_horizon_radius_angular_diagram');
  const values=[['particle',core.current.particleProperMpc],['event',core.current.eventProperMpc],['Hubble',core.current.hubbleProperMpc]];
  for(const [key,radius]of values) {
   const matched=rings.filter(p=>p.key===key);assert.equal(matched.length,radius===null?0:3);
   for(const r of matched)assert.equal(r.radiusMpc,radius);
   const record=scene.cosmology.primitives.find(p=>p.kind==='horizon_radius'&&p.key===key);
   for(const r of matched)for(const p of r.points)near(norm(add(p,mul(record.origin,-1))),radius*record.gainScenePerMpc,1);
  }
 }
 if(s.mode==='causality') {
  const cone=scene.cosmology.primitives.find(p=>p.kind==='causal_cone');
  for(const p of scene.primitives.filter(p=>p.fidelity_kind==='weak_field_null_front_section').flatMap(p=>p.points)) {
   const q=add(p,mul(cone.origin,-1));near(Math.hypot(q[0],q[1]),q[2],1);
   near(q[2]/cone.gainScenePerAU,C*s.elapsedMinutes*60/149597870700,1);
  }
  for(const p of scene.primitives.filter(p=>p.fidelity_kind==='weak_field_future_null_generator')) {
   point(p.points[0],cone.origin);const q=add(p.points[1],mul(cone.origin,-1));near(Math.hypot(q[0],q[1]),q[2],1);
  }
  const receiver=scene.primitives.find(p=>p.fidelity_kind==='weak_field_fixed_receiver_worldline');
  receiver.points.forEach(p=>near((p[0]-cone.origin[0])/cone.gainScenePerAU,s.distanceAU,1));
  const arrival=scene.primitives.find(p=>p.fidelity_kind==='weak_field_first_arrival').points[0];
  point(arrival,add(mul([s.distanceAU,0,s.distanceAU],cone.gainScenePerAU),cone.origin));
 }
 if(s.mode==='blackhole'&&s.bhView==='radius') {
  const spheres=scene.cosmology.primitives.filter(p=>p.kind==='areal_sphere');
  assert.equal(spheres.length,2);
  for(const sphere of spheres) {
   assert.equal(sphere.radialSpatialEmbeddingClaim,false);
   near(sphere.areaM2,4*Math.PI*sphere.radiusM**2);
   const rings=scene.primitives.filter(p=>p.fidelity_kind==='schwarzschild_areal_two_sphere'&&p.key===sphere.key);
   assert.equal(rings.length,3);
   for(const p of rings.flatMap(r=>r.points))near(norm(add(p,mul(sphere.origin,-1))),sphere.radiusRs*sphere.gainScenePerRs,1);
  }
 }
 if(s.mode==='blackhole'&&s.bhView==='infall'&&s.radiusRs<=1) {
  assert.equal(core.current.event.schwarzschildTimeRsC,null);
  assert.equal(core.current.event.arrivalDelayRsC,null);
  assert.ok(!scene.cosmology.panels.flatMap(p=>p.markers).some(m=>['chosen-t','chosen-arrival'].includes(m.key)));
 }
 assert.ok(scene.primitives.length<=3000);cosmologyStates++;
}
// A real bus with nine simultaneously connected views: fields never cross keys.
const bus=require('../web/lesson-state.js'),keys=['math.5.complex-analysis','phys.4.quantum','math.5.topology','phys.4.relativity','math.5.abstract','phys.5.quantum-info','math.5.logic','phys.4.em-maxwell','phys.5.gr-cosmo'];
const received=keys.map(()=>[]),roots=keys.map(()=>({isConnected:true}));
keys.forEach((k,i)=>bus.join(k,roots[i],v=>received[i].push(v)));
const sender={isConnected:true};
keys.forEach((k,i)=>{const before=received.map(v=>v.length);bus.publish(k,sender,{reviewValue:i,inactiveValue:123.456789123});received.forEach((v,j)=>assert.equal(v.length,before[j]+(i===j?1:0)));assert.deepEqual(received[i].at(-1),{reviewValue:i,inactiveValue:123.456789123});});
const before=received.map(v=>v.length);bus.publish('unknown',sender,{bad:true});assert.deepEqual(received.map(v=>v.length),before);
console.log(JSON.stringify({passed:true,maxwellStates,cosmologyStates,fieldVectors,engineArrowShafts,surfaceFaces,chartPoints,markers,stateKeys:keys.length,wholeGoalComplete:false}));

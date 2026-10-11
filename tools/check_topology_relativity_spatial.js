#!/usr/bin/env node
'use strict';

// Fixed CommonJS observation path. Neither core's formula helpers nor its
// reported pass flags are numerical or combinatorial reference values.
const assert = require('node:assert/strict');
global.window = {
  PrimerMathTopologyLab: require('../web/math-topology-lab.js'),
  PrimerPhysicsRelativityLab: require('../web/physics-relativity-lab.js'),
};
window.PrimerFidelitySpatialFamilies = require('../web/spatial-fidelity.js');
require('../web/spatial-models.js');
require('../web/spatial-module-objects.js');
const bindings = require('../data/module-models.json').models;
const pi = Math.PI, tau = 2*pi, c = 299792458, year = 31557600,
  day = 86400, gm = 3.986004418e14, radius = 6378137,
  omega = 7.292115e-5, g0 = 9.80665;

function near(a,b,label,tolerance=2e-10) {
  if(Object.is(a,b))return;
  assert.ok(Number.isFinite(a)&&Number.isFinite(b)&&
    Math.abs(a-b)<=tolerance*Math.max(1,Math.abs(a),Math.abs(b)),`${label}: ${a} != ${b}`);
}
function vector(a,b,label,tolerance){assert.equal(a.length,b.length,label);a.forEach((v,i)=>near(v,b[i],label+'['+i+']',tolerance));}
function lineNear(a,b,label){assert.equal(a.length,b.length,label);a.forEach((p,i)=>vector(p,b[i],label+' '+i));}
const kinds=(scene,kind)=>scene.primitives.filter(p=>p.fidelity_kind===kind);
function unique(scene,kind){const p=kinds(scene,kind);assert.equal(p.length,1,kind+' unique');return p[0];}
function attach(node,family){
  const binding=bindings.find(b=>b.node_id===node);
  assert.equal(binding?.family,family,'Exact current lesson binding');assert.equal(binding.mode,'model');
  const props={scenario:'module.'+node,family,mode:'model',context:binding.context,lesson:node};
  assert.equal(window.PrimerModuleObjects.ensure({props}),true);
  return raw=>window.PrimerSpatial.build(props.scenario,raw);
}
const top=attach('math.5.topology','topology-open-set-geometry'),rel=attach('phys.4.relativity','relativistic-event-geometry');
function finite(scene){assert.ok(scene.primitives.length>0&&scene.primitives.length<3000);for(const p of scene.primitives)for(const q of p.points){assert.equal(q.length,3);assert.ok(q.every(Number.isFinite));}}
const family=code=>Array.from({length:8},(_,i)=>i).filter(i=>code&(1<<i));
const topologyCode={discrete:255,indiscrete:129,chain:139,fork:143};
function validFamily(opens){return opens.includes(0)&&opens.includes(7)&&opens.every(a=>opens.every(b=>opens.includes(a|b)&&opens.includes(a&b)));}
function transform(p,s){return [s.stretch*p[0]+s.bend*p[1],p[2],-p[1]];}
function meshReference(vertices,faces,genus){
  const edges=new Map(),adj=Array.from({length:vertices.length},()=>new Set()),links=Array.from({length:vertices.length},()=>new Map());
  for(const f of faces){
    assert.equal(new Set(f).size,3,'Distinct triangle vertices');
    const a=vertices[f[0]],b=vertices[f[1]],d=vertices[f[2]],u=b.map((v,i)=>v-a[i]),v=d.map((x,i)=>x-a[i]);
    assert.ok(Math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])>1e-12,'Nondegenerate actual facet');
    f.forEach((a,i)=>{
      assert.ok(Number.isInteger(a)&&a>=0&&a<vertices.length);
      const b=f[(i+1)%3],d=f[(i+2)%3],key=[Math.min(a,b),Math.max(a,b)].join(':');
      if(!edges.has(key))edges.set(key,[]);edges.get(key).push(a<b?1:-1);adj[a].add(b);adj[b].add(a);
      if(!links[a].has(b))links[a].set(b,new Set());if(!links[a].has(d))links[a].set(d,new Set());links[a].get(b).add(d);links[a].get(d).add(b);
    });
  }
  assert.ok([...edges.values()].every(v=>v.length===2&&v[0]+v[1]===0),'Closed coherent oriented edge incidence');
  function reached(map,start){const seen=new Set([start]),todo=[start];while(todo.length)for(const n of map.get?map.get(todo.pop()):map[todo.pop()])if(!seen.has(n)){seen.add(n);todo.push(n);}return seen;}
  assert.equal(reached(adj,0).size,vertices.length,'One connected surface');
  for(const link of links){assert.ok([...link.values()].every(n=>n.size===2),'Each vertex link has degree two');assert.equal(reached(link,link.keys().next().value).size,link.size,'Each vertex link is a single circle');}
  assert.equal(vertices.length-edges.size+faces.length,2-2*genus,'Euler characteristic of actual facets');
  return {V:vertices.length,E:edges.size,F:faces.length,chi:2-2*genus};
}
function topologyScene(scene){
  finite(scene);const s=scene.state,d=scene.topology.active;
  assert.deepEqual(scene.topology.state,s,'Full topology state retained');
  assert.match(scene.note,/finite display is not that proof/);
  if(s.station==='T1'){
    const opens=family(s.familyMask);assert.deepEqual(d.opens,opens);assert.equal(d.valid,validFamily(opens));
    const points=kinds(scene,'subset');assert.equal(points.length,8);
    points.forEach(p=>{assert.equal(p.included,opens.includes(p.mask));vector(p.points[0],[p.mask&1?1:-1,p.mask&2?1:-1,p.mask&4?1:-1],'Boolean subset vertex');});
    assert.equal(kinds(scene,'subset_inclusion').length,12,'All Boolean inclusion edges');
  }else if(s.station==='T2'){
    const mapping=[s.mapCode%3,Math.floor(s.mapCode/3)%3,Math.floor(s.mapCode/9)];
    assert.deepEqual(d.mapping,mapping);
    const opens=family(topologyCode[s.targetTopology]),domain=family(topologyCode[s.domainTopology]);
    const preimages=opens.map(open=>mapping.reduce((p,y,x)=>open&(1<<y)?p|(1<<x):p,0));
    assert.deepEqual(d.preimages.map(p=>p.preimage),preimages);assert.equal(d.continuous,preimages.every(p=>domain.includes(p)));
    const lines=kinds(scene,'map');assert.equal(lines.length,3);lines.forEach(p=>lineNear(p.points,[[-2,1.2-1.2*p.source,0],[2,1.2-1.2*mapping[p.source],0]],'Exact finite map link'));
  }else if(s.station==='T3'){
    const cover=kinds(scene,'open_cover_interval');assert.equal(cover.length,s.coverN-1);
    cover.forEach((p,i)=>lineNear(p.points,[[5/(i+2),.03*i,0],[5,.03*i,0]],'Selected open interval'));
    near(d.omittedBoundary,1/s.coverN,'Missing boundary');near(d.witness,1/(2*s.coverN),'Finite-cover witness');
    vector(unique(scene,'uncovered_witness').points[0],[5/(2*s.coverN),-.3,0],'Uncovered witness coordinate');
    assert.ok(d.selected.every(u=>u.start>d.witness&&u.startIncluded===false&&u.endIncluded===false));
    assert.ok(d.radius>.5/s.coverMesh,'Independent sufficient radius for closed interval cover');
    const closed=kinds(scene,'closed_interval_cover');assert.equal(closed.length,s.coverMesh+1);
    closed.forEach((p,i)=>lineNear(p.points,[[5*(i/s.coverMesh-.75/s.coverMesh),0,1+.03*i],[5*(i/s.coverMesh+.75/s.coverMesh),0,1+.03*i]],'Separate closed interval open cover'));
    const labels=scene.primitives.filter(p=>p.kind==='label').map(p=>p.text);assert.ok(labels.includes('x; gain 5'));assert.ok(labels.includes('Selected index n: y=.03(n−2)'));
    assert.match(d.theorem,/ANY nonempty finite selection/);
  }else if(s.station==='T4'){
    const a=Array.from({length:s.cofiniteA},(_,i)=>i),b=Array.from({length:s.cofiniteB},(_,i)=>i+2),union=[...new Set([...a,...b])];
    assert.deepEqual(d.excludedA,a);assert.deepEqual(d.excludedB,b);
    const witness=Math.max(...union)+1;near(d.witness,witness,'Cofinite intersection witness');assert.ok(!union.includes(witness));
    const gain=4/Math.max(witness,...union.map(Math.abs),1);
    const marker=scene.primitives.filter(p=>p.kind==='sphere'&&p.color==='#b98a2f');assert.equal(marker.length,1);
    vector(marker[0].points[0],[gain*witness,.15,.5],'Witness display gain');
    assert.equal(kinds(scene,'excluded_point').length,a.length+b.length);assert.match(d.theorem,/cannot exhaust ℝ/);
  }else if(s.station==='T5'){
    const graph=unique(scene,'finite_sine_graph'),segment=unique(scene,'limiting_segment');
    graph.points.forEach(p=>{assert.ok(p[0]>0,'No sampled graph vertex on limit segment');near(p[1],Math.sin(4/p[0]),'Independent sine graph coordinate');near(p[2],0,'Planar graph');});
    lineNear(segment.points,[[0,-1,0],[0,1,0]],'Actual limiting vertical segment');
    assert.equal(kinds(scene,'finite_sine_graph').length,1);assert.equal(kinds(scene,'limiting_segment').length,1);
    assert.ok(!scene.primitives.filter(p=>p.kind==='line'&&p.fidelity_kind!=='axis').some(p=>p.points.some(q=>q[0]===0)&&p.points.some(q=>q[0]>0)),'No false path/oscillation bridge');
    const seq=kinds(scene,'closure_sequence');assert.equal(seq.length,20);seq.forEach(p=>{near(p.points[0][0],4/(Math.asin(s.sineTarget)+tau*p.n),'Closure sequence x');near(p.points[0][1],s.sineTarget,'Closure sequence y');});
    const labels=scene.primitives.filter(p=>p.kind==='label').map(p=>p.text);assert.ok(labels.includes('x; gain 4'));assert.ok(labels.includes('sin(1/x); gain 1'));
    assert.match(d.theorem,/intermediate value theorem/);
  }else if(s.station==='T6'){
    const observation=scene.topology.primitives.find(p=>p.kind==='surface'),actual=kinds(scene,'surface_triangle');
    const reference=meshReference(observation.vertices,observation.faces,s.genus);assert.deepEqual(observation.counts,reference);
    assert.equal(actual.length,observation.faces.length);actual.forEach(p=>lineNear(p.points,observation.faces[p.face].map(i=>observation.vertices[i]),'Actual source triangle'));
    observation.vertices.forEach((p,i)=>vector(p,transform(d.mesh.vertices[i],s),'Invertible deformed source vertex'));
    near(observation.determinant,s.stretch,'Affine determinant positive');assert.ok(s.stretch>0);
    const eight=unique(scene,'separate_figure_eight'),offset=Math.max(...observation.vertices.map(p=>p[0]))+3;
    eight.points.forEach((p,i)=>{const theta=tau*i/128,base=[0,64,128].includes(i)?[0,0,0]:[Math.sin(theta),Math.sin(2*theta),0];const expected=transform(base,s);expected[0]+=offset;vector(p,expected,'Actual figure-eight deformation');});
    assert.ok(Math.min(...eight.points.map(p=>p[0]))>Math.max(...observation.vertices.map(p=>p[0])),'Separate figure-eight sheet does not meet surface');
    assert.deepEqual(eight.points[0],eight.points[64]);assert.deepEqual(eight.points[64],eight.points[128]);
  }else{
    const circle=unique(scene,'circle');circle.points.forEach(p=>{near(p[0]**2+p[1]**2,1,'Unit circle');near(p[2],0,'Planar circle');});
    assert.deepEqual(circle.points[0],circle.points.at(-1),'Exact seam closure');
    const maps=kinds(scene,'circle_map');assert.equal(maps.length,2);maps.forEach(p=>{
      const angle=p.key==='upper'?10**s.logEpsilon:tau-10**s.logEpsilon;
      lineNear(p.points,[[3,-1+angle/pi,0],[Math.cos(angle),Math.sin(angle),0]],'Circle quotient map near seam');
    });
    const selected=tau*s.angleFraction;lineNear(unique(scene,'selected_circle_map').points,[[3,-1+selected/pi,0],[Math.cos(selected),Math.sin(selected),0]],'Selected angle actual source and image');
    assert.equal(kinds(scene,'included_endpoint').length,s.circleDomain==='halfopen'?1:2,'Actual source domain endpoints');
    const excluded=kinds(scene,'excluded_endpoint');assert.equal(excluded.length,s.circleDomain==='halfopen'?1:0,'Excluded half-open endpoint');
    if(excluded.length)excluded[0].points.forEach(p=>{near(Math.hypot(p[0]-3,p[1]-1),.08,'Hollow excluded endpoint ring');near(p[2],0,'Domain marker plane');});
    const domain=scene.topology.primitives.find(p=>p.kind==='source_domain');assert.equal(domain.endpointEquivalence,s.circleDomain==='quotient');
    assert.equal(d.homeomorphism,s.circleDomain==='quotient');assert.equal(d.bijective,s.circleDomain!=='closed');
    assert.equal(d.domainCompact,s.circleDomain!=='halfopen');near(d.inverseDistance,tau-10**s.logEpsilon,'Half-open inverse jump');
  }
}
const boost=(x,ct,b)=>{const g=1/Math.sqrt(1-b*b);return {x:g*(x-b*ct),y:g*(ct-b*x)};};
const gg=b=>1/Math.sqrt(1-b*b);
function tower(h,lat){const rs=2*gm/c**2,a=Math.sqrt(1-rs/radius),b=Math.sqrt(1-rs/(radius+h));return {grav:(rs*h/(radius*(radius+h)))/(a*(a+b)),rot:-(omega**2)*(2*radius*h+h*h)*Math.cos(lat*pi/180)**2/(2*c*c)};}
function gps(h,lat){const r=radius+1000*h,ground=omega*radius*Math.cos(lat*pi/180),grav=gm*(1/radius-1/r)/c**2,sr=-(gm/r-ground**2)/(2*c*c);return {r,grav,sr,net:grav+sr};}
function actualCurveReference(scene,panel,curve,p){
  const s=scene.state,d=scene.relativity.current,x=p.x,key=curve.key,i=panel.index;
  if(s.mode==='events'){
    if(key==='light+')return x;if(key==='light-')return -x;
    if(key==='ct-axis'){near(x,s.beta*p.y,'Moving origin worldline');return p.y;}
    if(key==='x-axis')return s.beta*x;
  }else if(s.mode==='clocks'){
    if(i===0)return key==='light'?x:(s.beta===0?(near(x,0,'Rest muon x'),p.y):x/s.beta);
    if(key==='lab-slice')return 0;
    if(key==='rest-slice')return s.beta*x;
    const intercept=key==='front'?s.properLengthM/gg(s.beta):0;
    near(x,s.beta*p.y+intercept,'Rod worldline simultaneity');return p.y;
  }else if(s.mode==='barn'){
    const original=i===0?{x:p.x,y:p.y}:boost(p.x,p.y,-s.barnBeta);
    const rear=key==='rear',front=key==='front';
    near(original.x,rear?s.barnBeta*original.y:front?s.barnBeta*original.y+s.poleLengthM/gg(s.barnBeta):key==='entrance'?0:s.barnLengthM,'Independent barn worldline');return p.y;
  }else if(s.mode==='momentum'){
    if(i===0)return key==='addition'?(x-s.shipABeta)/(1-x*s.shipABeta):x-s.shipABeta;
    return key==='energy'?gg(x):x*gg(x);
  }else if(s.mode==='acceleration'){
    if(i===0){if(key==='light')return x;const length=c/(s.accelerationG*g0*year);return Math.sqrt(x*x+2*length*x);}
    return key==='light-speed'?1:Math.tanh(s.accelerationG*g0*x*year/c);
  }else if(s.mode==='gravity'){
    if(s.gravitySystem==='tower'){
      const t=tower(i===0?s.heightM:x,s.latitudeDeg),duration=i===0?x:s.elapsedDays;
      return (t.grav+(key==='gravity'?0:t.rot))*duration*day*1e6;
    }
    const orbit=gps(i===0?x:s.orbitAltitudeKm,s.latitudeDeg);
    return i===0?(key==='GR'?orbit.grav:key==='SR'?orbit.sr:orbit.net)*day*1e6:key==='corrected'?0:orbit.net*x*day*1e6;
  }else if(s.mode==='equivalence'){
    return key==='flat'?0:(i===0?gm*s.capsuleHeightM:-.5*gm*s.capsuleWidthM)*x*x/radius**3*1e6;
  }else{
    const speed=key==='plus'?c/s.ringRadiusM:key==='minus'?-c/s.ringRadiusM:s.ringBeta*c/s.ringRadiusM;
    return (speed-(i===1?s.ringBeta*c/s.ringRadiusM:0))*x*1e-6;
  }
  throw new Error('Unrecognized independently assessed curve '+s.mode+'/'+key);
}
function markerReference(s,i,key){
  if(s.mode==='events')return key==='A'?[0,0]:i===0?[s.eventXM,s.eventCtM]:Object.values(boost(s.eventXM,s.eventCtM,s.beta));
  if(s.mode==='clocks')return i===0?[s.beta*c*gg(s.beta)*s.properTimeUs*1e-6,c*gg(s.beta)*s.properTimeUs*1e-6]:[key==='0'?0:s.properLengthM/gg(s.beta),0];
  if(s.mode==='barn'){const x=key==='entrance'?0:s.barnLengthM;return i===0?[x,0]:Object.values(boost(x,0,s.barnBeta));}
  if(s.mode==='momentum')return i===0?[s.shipBBeta,(s.shipBBeta-s.shipABeta)/(1-s.shipBBeta*s.shipABeta)]:[Math.sqrt(s.particleGamma**2-1)/s.particleGamma,s.particleGamma];
  if(s.mode==='acceleration'){const eta=s.accelerationG*g0*s.crewYears*year/c,length=c/(s.accelerationG*g0*year);return i===0?[length*2*Math.sinh(eta/2)**2,length*Math.sinh(eta)]:[s.crewYears,Math.tanh(eta)];}
  if(s.mode==='gravity'){
    if(s.gravitySystem==='tower'){const t=tower(s.heightM,s.latitudeDeg);return [i===0?s.elapsedDays:s.heightM,(t.grav+t.rot)*s.elapsedDays*day*1e6];}
    const q=gps(s.orbitAltitudeKm,s.latitudeDeg);return i===0?[s.orbitAltitudeKm,q.net*day*1e6]:[s.elapsedDays,s.clockCorrection==='corrected'?0:q.net*s.elapsedDays*day*1e6];
  }
  if(s.mode==='equivalence')return [s.fallTimeS,(i===0?gm*s.capsuleHeightM:-.5*gm*s.capsuleWidthM)*s.fallTimeS**2/radius**3*1e6];
  const sign=key.startsWith('positive')||key.startsWith('plus')?1:-1,arrival=tau*s.ringRadiusM/(c*(1-sign*s.ringBeta)),time=i===0?arrival:Math.min(s.flightFraction*tau*s.ringRadiusM/(c*(1-Math.abs(s.ringBeta))),arrival);
  return [time*1e6,(sign-(i===1?s.ringBeta:0))*c*time/s.ringRadiusM];
}
function unitReference(s,i){
  if(['events','clocks','barn'].includes(s.mode))return ['x (m)','ct (m)'];
  if(s.mode==='momentum')return i===0?['u/c in station','u′/c']:['v/c','normalized energy / pc'];
  if(s.mode==='acceleration')return i===0?['x (light-years)','ct (light-years)']:['τ (Julian years)','v/c'];
  if(s.mode==='gravity')return s.gravitySystem==='tower'?[i===0?'days':'height (m)','clock gain (µs)']:i===0?['altitude (km)','µs per day']:['days','satellite clock gain (µs)'];
  if(s.mode==='equivalence')return ['time (s)','separation change (µm)'];
  return ['t (µs)',i===0?'unwrapped angle (rad)':'rotating angle (rad)'];
}
function shortUnitReference(s,i){
  if(['events','clocks','barn'].includes(s.mode))return ['m','m'];
  if(s.mode==='momentum')return i===0?['u/c in station','u′/c']:['v/c','normalized energy / pc'];
  if(s.mode==='acceleration')return i===0?['light-years','light-years']:['Julian years','v/c'];
  if(s.mode==='gravity')return s.gravitySystem==='tower'?[i===0?'days':'m','µs']:i===0?['km','µs per day']:['days','µs'];
  if(s.mode==='equivalence')return ['s','µm'];
  return ['µs','rad'];
}
function titleReference(s,i){
  const titles={events:['S: calibrated Minkowski events','S′: same two physical events'],clocks:['Muon creation and decay in S','Length requires simultaneous endpoints'],barn:['Barn frame: doors at the same t','Pole frame: different door times'],momentum:['Ship B seen from moving ship A','Massive particle energy and momentum'],acceleration:['Worldline in initial inertial frame','Velocity versus crew proper time'],equivalence:['Radial freely falling separation','Transverse freely falling separation'],sagnac:['Unwrapped inertial angle and arrival events','Rotating-coordinate light trajectories']};
  if(s.mode==='gravity')return s.gravitySystem==='tower'?['Higher clock accumulates extra proper time','Height dependence for the selected duration'][i]:['Circular-orbit clock-rate contributions','Clock correction for selected orbit'][i];
  return titles[s.mode][i];
}
function calibrationText(scene,panel,labels,xs,ys){
  const fullUnits=unitReference(scene.state,panel.index),shortUnits=shortUnitReference(scene.state,panel.index);
  assert.ok(labels.includes('Chart '+(panel.index+1)),'Compact chart label identifies full readout');
  const title='Chart '+(panel.index+1)+': '+titleReference(scene.state,panel.index)+'. ';
  const titlePosition=scene.readout.indexOf(title);assert.ok(titlePosition>=0,'Full physical chart title retained in readout');
  let calibration=scene.readout.slice(titlePosition+title.length);
  for(const [axis,unit,shortUnit,scale] of [['X',fullUnits[0],shortUnits[0],xs],['Y',fullUnits[1],shortUnits[1],ys]]){
    const prefix=axis+' / '+shortUnit+' ×',label=labels.find(text=>text.startsWith(prefix));assert.ok(label,'Compact physical/chart unit and gain');
    const displayed=Number(label.slice(prefix.length)),expected=2/scale;
    // A nearest rounding to three significant digits has a half-unit error in
    // its third decimal place. This bound is independent of toPrecision().
    const shortQuantum=10**(Math.floor(Math.log10(expected))-2);
    assert.ok(Number.isFinite(displayed)&&Math.abs(displayed-expected)<=.5001*shortQuantum,'Three-significant-digit printed gain');
    const sourcePrefix='Source '+axis+': '+unit+', gain ';assert.ok(calibration.startsWith(sourcePrefix),'Full source axis unit retained in readout');
    const remainder=calibration.slice(sourcePrefix.length),token=/^([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\.(?: |$)/.exec(remainder);
    assert.ok(token,'Readout gain is a complete numeric token');
    const mantissa=token[1].split(/e/i)[0].replace(/[+.-]/g,'').replace(/^0+/,'');assert.equal(mantissa.length,16,'Full sixteen-significant-digit readout');
    const observed=Number(token[1]),fullQuantum=10**(Math.floor(Math.log10(expected))-15);
    assert.ok(Number.isFinite(observed)&&Math.abs(observed-expected)<=.5001*fullQuantum+2*Number.EPSILON*expected,'Full readout gain recovers original source coordinates');
    calibration=remainder.slice(token[0].length);
  }
}
function relativityScene(scene){
  finite(scene);const s=scene.state,d=scene.relativity.current,panels=scene.relativity.panels;
  assert.deepEqual(scene.relativity.state,s,'Full relativity state retained');assert.equal(panels.length,2);
  assert.match(scene.note,/depth offsets are not physical distances/);assert.match(scene.note,/not a Lorentz transformation/);
  for(const panel of panels){
    assert.equal(panel.z,-4*panel.index,'Separated mathematical chart plane');
    const all=panel.curves.flatMap(v=>v.points).concat(panel.markers),maxX=Math.max(1e-12,...all.map(p=>Math.abs(p.x))),maxY=Math.max(1e-12,...all.map(p=>Math.abs(p.y))),xs=panel.equalScale?Math.max(maxX,maxY):maxX,ys=panel.equalScale?xs:maxY;
    near(panel.xScale,xs,'Independent horizontal normalization');near(panel.yScale,ys,'Independent vertical normalization');
    if(panel.equalScale)near(panel.xScale,panel.yScale,'Equal null/worldline x and ct calibration');
    const project=p=>[2*p.x/xs,2*p.y/ys,panel.z];
    for(const curve of panel.curves){
      assert.deepEqual([curve.xUnit,curve.yUnit],unitReference(s,panel.index),'Independent physical/chart units');
      curve.points.forEach(p=>near(p.y,actualCurveReference(scene,panel,curve,p),'Independent '+s.mode+'/'+curve.key+' ordinate'));
      const emitted=kinds(scene,'calibrated_curve').filter(p=>p.panel===panel.index&&p.key===curve.key);assert.equal(emitted.length,1);lineNear(emitted[0].points,curve.points.map(project),'Calibrated emitted curve');
    }
    panel.markers.forEach(marker=>{vector([marker.x,marker.y],markerReference(s,panel.index,marker.key),'Independent marked event');const emitted=kinds(scene,'calibrated_marker').filter(p=>p.panel===panel.index&&p.key===marker.key);assert.equal(emitted.length,1);vector(emitted[0].points[0],project(marker),'Calibrated emitted marker');});
    const labels=scene.primitives.filter(p=>p.kind==='label'&&p.points[0][2]===panel.z).map(p=>p.text);
    calibrationText(scene,panel,labels,xs,ys);
    assert.ok(labels.every(label=>!label.includes('undefined')),'No undefined chart units');
  }
  if(s.mode==='events'){
    const b=boost(s.eventXM,s.eventCtM,s.beta);near(d.boosted.xM,b.x,'Lorentz x');near(d.boosted.ctM,b.y,'Lorentz ct');near(d.invariant.squareM2,s.eventCtM**2-s.eventXM**2,'Signed interval');
    near(d.boostedInvariant.squareM2,s.eventCtM**2-s.eventXM**2,'Invariant after boost',2e-8);
  }else if(s.mode==='clocks'){
    near(d.labLifetimeUs,gg(s.beta)*s.properTimeUs,'Time dilation');near(d.lengthLabM,s.properLengthM/gg(s.beta),'Simultaneous rod length');near(d.restEventTimeDifferenceS,-s.beta*s.properLengthM/c,'Nonsimultaneous transformed endpoints',1e-18);
    vector(panels[0].markers[0].x===undefined?[]:[panels[0].markers[0].x,panels[0].markers[0].y],[s.beta*c*gg(s.beta)*s.properTimeUs*1e-6,c*gg(s.beta)*s.properTimeUs*1e-6],'Mean muon decay event');
  }else if(s.mode==='barn'){
    near(d.contractedPoleM,s.poleLengthM/gg(s.barnBeta),'Pole contracted length');near(d.contractedBarnM,s.barnLengthM/gg(s.barnBeta),'Barn contracted length');
    near(d.doorTimeDifferencePoleS,-gg(s.barnBeta)*s.barnBeta*s.barnLengthM/c,'Spacelike door time difference',1e-18);
    panels[1].markers.forEach(p=>{const expected=boost(p.key==='entrance'?0:s.barnLengthM,0,s.barnBeta);vector([p.x,p.y],[expected.x,expected.y],'Door event boost');});
  }else if(s.mode==='momentum'){
    near(d.shipBInABeta,Math.tanh(Math.atanh(s.shipBBeta)-Math.atanh(s.shipABeta)),'Velocity rapidity difference');
    near(d.totalEnergyMeV,s.restEnergyMeV*s.particleGamma,'Total energy');near(d.kineticEnergyMeV,s.restEnergyMeV*(s.particleGamma-1),'Kinetic energy');near(d.pcMeV,s.restEnergyMeV*Math.sqrt(s.particleGamma**2-1),'Relativistic momentum');near(d.invariantMeV2,s.restEnergyMeV**2,'Energy momentum invariant',2e-8);
    assert.ok(Math.abs(d.shipBInABeta)<1,'Subluminal transformed material velocity');
  }else if(s.mode==='acceleration'){
    const eta=s.accelerationG*g0*s.crewYears*year/c;near(d.rapidity,eta,'Integrated proper acceleration rapidity');near(d.beta,Math.tanh(eta),'Speed from rapidity');
    near(d.oneMinusBeta,2/(Math.exp(2*eta)+1),'Resolved remaining light-speed gap',1e-14);assert.ok(d.oneMinusBeta>0);
    near(d.tS,c/(s.accelerationG*g0)*Math.sinh(eta),'Inertial elapsed time');near(d.xM,c*c/(s.accelerationG*g0)*2*Math.sinh(eta/2)**2,'Integrated position');
    near(d.coordinateAccelerationMS2,s.accelerationG*g0/Math.cosh(eta)**3,'Coordinate versus proper acceleration');
  }else if(s.mode==='gravity'){
    const t=tower(s.heightM,s.latitudeDeg),q=gps(s.orbitAltitudeKm,s.latitudeDeg);
    near(d.tower.gravFraction,t.grav,'Rationalized Schwarzschild clock ratio',1e-20);near(d.tower.rotFraction,t.rot,'Differential rotation',1e-20);
    near(d.gps.netUsDay,q.net*day*1e6,'Weak circular orbit rate');near(d.gps.preoffsetFraction,-q.net/(1+q.net),'Modeled rate preoffset',1e-20);
    if(s.gravitySystem==='gps')near(d.displayGainUs,s.clockCorrection==='corrected'?0:q.net*s.elapsedDays*day*1e6,'GPS selected correction marker');
  }else if(s.mode==='equivalence'){
    near(d.radialGradient,2*gm/radius**3,'Radial geodesic deviation');near(d.transverseGradient,-gm/radius**3,'Transverse geodesic deviation');
    near(d.radialInitialRelativeAccelerationMS2,gm*s.capsuleHeightM*(2*radius+s.capsuleHeightM)/(radius**2*(radius+s.capsuleHeightM)**2),'Finite radial differential acceleration',1e-18);
    near(d.transverseInitialRelativeAccelerationMS2,-gm*s.capsuleWidthM/(radius**2+s.capsuleWidthM**2/4)**1.5,'Finite transverse differential acceleration',1e-18);
    assert.match(scene.note,/second order/);
  }else{
    const R=s.ringRadiusM,b=s.ringBeta,tPlus=tau*R/(c*(1-b)),tMinus=tau*R/(c*(1+b));
    near(d.tPlusS,tPlus,'Positive light reception',1e-18);near(d.tMinusS,tMinus,'Negative light reception',1e-18);near(d.deltaProperS,(tPlus-tMinus)*Math.sqrt(1-b*b),'Detector proper arrival difference',1e-18);
    const circular=scene.relativity.circular,ctScale=Math.max(1e-12,...Object.values(d.worldlines).flatMap(v=>v.map(p=>p.ctM)));near(circular.ctScale,ctScale,'Temporal gain');
    const circularLabels=scene.primitives.filter(p=>p.kind==='label'&&p.points[0][2]===-8).map(p=>p.text);
    assert.ok(circularLabels.includes('x/R; gain 2'),'Dimensionless circular x ordinate');
    assert.ok(circularLabels.some(label=>label.startsWith('ct (m); gain ')),'Circular temporal coordinate is metres');
    for(const [key,points] of Object.entries(d.worldlines)){
      const emitted=kinds(scene,'circular_worldline').filter(p=>p.key===key);assert.equal(emitted.length,1);
      points.forEach((p,i)=>{
        const rate=key==='plus'?c/R:key==='minus'?-c/R:b*c/R;near(p.ctM,c*p.tS,'Circular temporal coordinate');near(p.xM,R*Math.cos(rate*p.tS),'Circular x');near(p.yM,R*Math.sin(rate*p.tS),'Circular y');
        vector(emitted[0].points[i],[2*Math.cos(rate*p.tS),2*c*p.tS/ctScale,-8-2*Math.sin(rate*p.tS)],'Two spatial directions plus ct');
      });
    }
    vector([d.plusArrival.xM,d.plusArrival.yM],[d.detectorPlus.xM,d.detectorPlus.yM],'Positive reception same place');vector([d.minusArrival.xM,d.minusArrival.yM],[d.detectorMinus.xM,d.detectorMinus.yM],'Negative reception same place');
  }
}

const topologyStates=[],relativityStates=[];
for(let familyMask=0;familyMask<256;familyMask++)topologyStates.push({station:'T1',familyMask});
for(const domainTopology of Object.keys(topologyCode))for(const targetTopology of Object.keys(topologyCode))for(let mapCode=0;mapCode<27;mapCode++)topologyStates.push({station:'T2',domainTopology,targetTopology,mapCode});
for(const coverN of [2,3,8,80])for(const coverMesh of [2,6,16])topologyStates.push({station:'T3',coverN,coverMesh});
for(const cofiniteA of [1,4,12])for(const cofiniteB of [1,4,12])topologyStates.push({station:'T4',cofiniteA,cofiniteB});
for(const sineCycles of [2,8,24])for(const sineTarget of [-1,-.5,0,.5,1])for(const sequenceN of [1,20])topologyStates.push({station:'T5',sineCycles,sineTarget,sequenceN});
for(let genus=0;genus<=3;genus++)for(const refinement of [1,2])for(const [stretch,bend] of [[.5,-.75],[1,0],[2,.75]])topologyStates.push({station:'T6',genus,refinement,stretch,bend});
for(const circleDomain of ['halfopen','closed','quotient'])for(const logEpsilon of [-5,-2,-.5])for(const angleFraction of [0,.25,.875])topologyStates.push({station:'T7',circleDomain,logEpsilon,angleFraction});
for(const beta of [-.995,-.6,0,.6,.995])for(const [eventXM,eventCtM] of [[20,30],[30,10],[30,30],[0,0],[-40,-40]])relativityStates.push({mode:'events',beta,eventXM,eventCtM});
for(const beta of [-.995,0,.6,Math.sqrt(24)/5])for(const [properTimeUs,properLengthM] of [[.1,1],[2,10],[10,40]])relativityStates.push({mode:'clocks',beta,properTimeUs,properLengthM});
for(const barnBeta of [.01,Math.sqrt(3)/2,.995])for(const [poleLengthM,barnLengthM] of [[1,30],[20,10],[40,1]])relativityStates.push({mode:'barn',barnBeta,poleLengthM,barnLengthM});
for(const [shipABeta,shipBBeta] of [[.5,-.5],[-.995,.995],[.995,.995]])for(const particleGamma of [1,5,10])relativityStates.push({mode:'momentum',shipABeta,shipBBeta,particleGamma,restEnergyMeV:500});
for(const accelerationG of [.1,1,2])for(const crewYears of [0,.05,2,5])relativityStates.push({mode:'acceleration',accelerationG,crewYears});
for(const gravitySystem of ['tower','gps'])for(const latitudeDeg of [0,45,90])for(const clockCorrection of ['uncorrected','corrected'])relativityStates.push({mode:'gravity',gravitySystem,latitudeDeg,clockCorrection,heightM:100,orbitAltitudeKm:20200,elapsedDays:365.25});
for(const [capsuleHeightM,capsuleWidthM] of [[0,0],[2,2],[1000,1000]])for(const fallTimeS of [0,1,10])relativityStates.push({mode:'equivalence',capsuleHeightM,capsuleWidthM,fallTimeS});
for(const ringBeta of [-.6,-10/c,0,10/c,.6])for(const ringRadiusM of [.1,10,10000])for(const flightFraction of [0,.5,1])relativityStates.push({mode:'sagnac',ringBeta,ringRadiusM,flightFraction});
function observations(){const fixtures=[
  top({station:'T6',genus:3,refinement:2,stretch:1.5,bend:.625}),
  rel({mode:'events',beta:.8,eventXM:30,eventCtM:10}),
  rel({mode:'clocks',beta:Math.sqrt(24)/5,properTimeUs:2,properLengthM:10}),
  rel({mode:'barn',barnBeta:Math.sqrt(3)/2,poleLengthM:20,barnLengthM:10}),
  rel({mode:'momentum',shipABeta:.5,shipBBeta:-.5,restEnergyMeV:500,particleGamma:5}),
  rel({mode:'acceleration',accelerationG:1,crewYears:5}),
  rel({mode:'gravity',gravitySystem:'tower',heightM:100,elapsedDays:365.25}),
  rel({mode:'gravity',gravitySystem:'gps',orbitAltitudeKm:20200,elapsedDays:1}),
  rel({mode:'equivalence',capsuleHeightM:2,capsuleWidthM:2,fallTimeS:1}),
  rel({mode:'sagnac',ringRadiusM:10,ringBeta:10/c,flightFraction:.6}),
];return fixtures.map(scene=>({...scene,ledger:(scene.topology?window.PrimerMathTopologyLab:window.PrimerPhysicsRelativityLab).build(scene.state).ledger}));}
if(process.argv.includes('--fixtures')){require('node:fs').writeFileSync(1,JSON.stringify(observations()));process.exit(0);}
topologyStates.forEach(raw=>topologyScene(top(raw)));relativityStates.forEach(raw=>relativityScene(rel(raw)));

// A corrupted projection/gain and a pinched/nonmanifold triangle must be
// rejected by the same independent check, not accepted because metadata says OK.
const wrongChart=structuredClone(rel({mode:'events'}));unique({...wrongChart,primitives:kinds(wrongChart,'calibrated_marker').filter(p=>p.panel===1&&p.key==='B')},'calibrated_marker').points[0][0]+=.02;
assert.throws(()=>relativityScene(wrongChart),/Calibrated emitted marker/);
const wrongSurface=structuredClone(top({station:'T6'}));wrongSurface.topology.primitives.find(p=>p.kind==='surface').faces.pop();assert.throws(()=>topologyScene(wrongSurface),/Closed coherent oriented edge incidence/);
const bridgedSine=structuredClone(top({station:'T5'}));bridgedSine.primitives.push({kind:'line',points:[[0,0,0],[.1,0,0]],fidelity_kind:'false_bridge'});assert.throws(()=>topologyScene(bridgedSine),/No false path/);
const falseEndpoint=structuredClone(top({station:'T7',circleDomain:'halfopen'}));falseEndpoint.primitives= falseEndpoint.primitives.filter(p=>p.fidelity_kind!=='excluded_endpoint');assert.throws(()=>topologyScene(falseEndpoint),/Excluded half-open endpoint/);
const wrongUnits=structuredClone(rel({mode:'acceleration'}));wrongUnits.relativity.panels[0].curves[0].xUnit='x (seconds)';assert.throws(()=>relativityScene(wrongUnits),/Independent physical\/chart units/);
const wrongShortGain=structuredClone(rel({mode:'events'}));wrongShortGain.primitives.find(p=>p.kind==='label'&&p.points[0][2]===0&&p.text.startsWith('X / ')).text='X / m ×0.999';assert.throws(()=>relativityScene(wrongShortGain),/Three-significant-digit printed gain/);
const wrongFullGain=structuredClone(rel({mode:'events'}));wrongFullGain.readout=wrongFullGain.readout.replace(/Source X: x \(m\), gain [^ ]+/, 'Source X: x (m), gain 0.9990000000000000.');assert.throws(()=>relativityScene(wrongFullGain),/Full readout gain recovers/);
const exact=rel({mode:'barn',barnBeta:Math.sqrt(3)/2});assert.equal(exact.state.barnBeta,Math.sqrt(3)/2,'Exact assessed fixture not snapped to a range tick');
for(const invalid of [null,true,false,[],{},'', '   ',Infinity,NaN]){assert.equal(rel({beta:invalid}).state.beta,window.PrimerPhysicsRelativityLab.initial.beta);assert.equal(top({genus:invalid}).state.genus,window.PrimerMathTopologyLab.initial.genus);}
for(const mode of window.PrimerPhysicsRelativityLab.stations.map(v=>v[0]))assert.deepEqual(Object.keys(rel({mode}).state).sort(),Object.keys(window.PrimerPhysicsRelativityLab.initial).sort());
for(const station of window.PrimerMathTopologyLab.controls[0].options.map(v=>v.value))assert.deepEqual(Object.keys(top({station}).state).sort(),Object.keys(window.PrimerMathTopologyLab.initial).sort());
for(const theoremStep of [1,2,3,4]){
  const scene=top({station:'T7',circleDomain:'quotient',theoremStep});topologyScene(scene);
  assert.equal(scene.state.theoremStep,theoremStep,'Complete selected theorem state');assert.equal(scene.topology.active.steps.length,theoremStep,'Selected compact-Hausdorff proof prefix');
  assert.ok(scene.readout.includes('Compact–Hausdorff proof steps '+theoremStep),'Selected proof step remains in spatial readout');
  [/closed A/,/image f\(A\) is compact/,/compact subset of a Hausdorff space is closed/,/closed bijection/].slice(0,theoremStep).forEach((statement,i)=>assert.match(scene.topology.active.steps[i],statement));
}
const bus=require('../web/lesson-state.js'),source={isConnected:true},peer={isConnected:true},other={isConnected:true},detached={isConnected:false};
let delivered=0,crossed=0,echoed=0,discarded=0;
bus.join('phys.4.relativity',source,()=>echoed++);bus.join('phys.4.relativity',peer,state=>{delivered++;assert.deepEqual(state,exact.state,'Full state bus payload including exact barn fixture');});
bus.join('math.5.topology',other,()=>crossed++);bus.join('phys.4.relativity',detached,()=>discarded++);
bus.publish('phys.4.relativity',source,exact.state);assert.equal(delivered,1);assert.equal(crossed,0);assert.equal(echoed,0);assert.equal(discarded,0);
process.stdout.write(JSON.stringify({status:'passed',topologyStations:7,relativityStations:8,topologyStates:topologyStates.length,relativityStates:relativityStates.length,
  independentOracles:['finite topology/preimage enumeration','every actual triangle, edge orientation and vertex link','invertible affine deformation and exact figure-eight incidence','quantified covers and separate sine closure','Lorentz boosts, intervals and simultaneous endpoints','rapidity, energy-momentum and proper acceleration','Schwarzschild/weak Earth clocks and finite tidal vectors','circular null paths and one rotating receiver'],
  regressionChecks:['calibration mutation rejection','three-digit short gain mutation rejection','sixteen-digit readout gain mutation rejection','nonmanifold mutation rejection','false sine bridge rejection','half-open endpoint omission rejection','wrong physical units rejection','complete normalized state','selected compact-Hausdorff proof prefix retained','exact assessed barn speed','invalid input rejection','full-state bus with source/cross-lesson/disconnected exclusions']})+'\n');

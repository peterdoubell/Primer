#!/usr/bin/env node
'use strict';

// Reproduction entry point: fixed CommonJS modules only. Expected numbers below
// are independently derived; no source-string execution, expression evaluator,
// core build/evaluate calls, or environment-selected executable is an oracle.
// Core build is used only as observed input for separate semantic-ledger checks.
const assert = require('node:assert/strict');
global.window = {
  PrimerMathComplexLab: require('../web/math-complex-lab.js'),
  PrimerPhysicsQuantumLab: require('../web/physics-quantum-lab.js'),
};
require('../web/spatial-models.js');
require('../web/spatial-module-objects.js');
const bindings = require('../data/module-models.json').models;
const pi = Math.PI, tau = 2 * pi;
const h = 6.62607015e-34, mass = 9.1093837139e-31, eV = 1.602176634e-19;
const hbar = h / tau, light = 299792458;
const Z = (re = 0, im = 0) => [re, im];
const plus = (a, b) => Z(a[0] + b[0], a[1] + b[1]);
const minus = (a, b) => Z(a[0] - b[0], a[1] - b[1]);
const times = (a, b) => Z(a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]);
const gain = (a, x) => a.map(v => v * x);
const mod = a => Math.hypot(...a);
const conjugate = a => Z(a[0], -a[1]);
const divide = (a, b) => mod(b) === 0 ? null : gain(times(a, conjugate(b)), 1 / mod(b) ** 2);
const polar = (r, t) => Z(r * Math.cos(t), r * Math.sin(t));
const exp = a => polar(Math.exp(a[0]), a[1]);
const power = (a, n) => Array.from({length: n}).reduce(v => times(v, a), Z(1));
const pair = a => a && Z(a.re, a.im);
function near(a, b, label, tolerance = 3e-10) {
  if (Object.is(a, b)) return;
  assert.ok(Number.isFinite(a) && Number.isFinite(b) &&
    Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(a), Math.abs(b)), `${label}: ${a} != ${b}`);
}
function vector(a, b, label, tolerance) {
  assert.equal(a.length, b.length, label + ': dimension');
  a.forEach((v, i) => near(v, b[i], `${label}[${i}]`, tolerance));
}
function complexNear(a, b, label, tolerance) {
  if (b === null) return assert.equal(a, null, label);
  assert.ok(a, label + ': finite value is present');
  vector(pair(a), b, label, tolerance);
}
function primitive(scene, kind) {
  const values = scene.primitives.filter(p => p.cq_kind === kind);
  assert.equal(values.length, 1, 'Unique ' + kind);
  return values[0];
}
function primitives(scene, kind) { return scene.primitives.filter(p => p.cq_kind === kind); }
function lineNear(actual, expected, label, tolerance) {
  assert.equal(actual.length, expected.length, label + ': sample count');
  actual.forEach((p, i) => vector(p, expected[i], `${label} point ${i}`, tolerance));
}
function finiteScene(scene) {
  assert.ok(scene.primitives.length > 0 && scene.primitives.length < 3000);
  for (const p of scene.primitives) for (const q of p.points) {
    assert.equal(q.length, 3); assert.ok(q.every(Number.isFinite), 'All emitted coordinates finite');
  }
}
function labelsInclude(scene, expected) {
  const labels=scene.primitives.filter(p=>p.kind==='label').map(p=>p.text);
  expected.forEach(text=>assert.ok(labels.includes(text),'Authored axis/ordinate unit label: '+text));
}
function attach(node, family) {
  const binding = bindings.find(v => v.node_id === node);
  assert.equal(binding.family, family, 'Actual lesson binding'); assert.equal(binding.mode, 'model');
  const scenario = 'module.' + node;
  assert.equal(window.PrimerModuleObjects.ensure({props: {scenario, family, mode: 'model',
    context: binding.context, lesson: node}}), true);
  return state => window.PrimerSpatial.build(scenario, state);
}
const buildComplex = attach('math.5.complex-analysis', 'complex-function-domain');
const buildQuantum = attach('phys.4.quantum', 'quantum-state-geometry');

// Named values, natural logarithms, and wrapped arguments. The essential
// singularity retains its logarithm even when exponentiation is unavailable.
function named(s, z) {
  let value, logAbs, phase;
  const name = ({C1: s.directionalFn, C2: s.contourFn, C3: s.taylorFn,
    C4: s.growthFn, C5: s.meanFn, C6: s.arcFn})[s.station];
  const r2 = z[0] ** 2 + z[1] ** 2;
  if (s.station === 'C6') {
    const factor = name === 'one' ? Z(1) : name === 'linear' ? divide(Z(1), plus(z, Z(0, s.poleA)))
      : divide(Z(1), plus(times(z, z), Z(s.poleA ** 2)));
    if (!factor) return {value: null, logAbs: Infinity, phase: null};
    logAbs = Math.log(mod(factor)) - s.k * z[1];
    phase = Math.atan2(factor[1], factor[0]) + s.k * z[0];
  } else if (name === 'pathology') {
    if (!r2) return {value: Z(), logAbs: -Infinity, phase: null};
    const exponent = gain(divide(Z(1), power(z, 4)), -1);
    logAbs = exponent[0]; phase = exponent[1];
  } else if (name === 'exp') { logAbs = z[0]; phase = z[1]; }
  else {
    if (name === 'z2') value = times(z, z);
    if (name === 'conjugate') value = conjugate(z);
    if (name === 'abs2') value = Z(r2);
    if (name === 'peak') value = Z(1 - r2);
    if (name === 'one' || name === 'constant') value = Z(1);
    if (name === 'linear' || name === 'annulus-z') value = z;
    if (name === 'geometric') value = divide(Z(1), minus(Z(1), z));
    if (name === 'poles') value = divide(Z(1), plus(times(z, z), Z(1)));
    if (name === 'annulus-inverse') value = divide(Z(1), z);
    if (name === 'rational') {
      const a = s.residueA === 0 ? Z() : divide(Z(s.residueA), z);
      const b = s.residueB === 0 ? Z() : divide(Z(s.residueB), minus(z, Z(2)));
      value = a && b ? plus(a, b) : null;
    }
    if (name === 'laurent') value = r2 ? plus(plus(divide(Z(3), times(z, z)), divide(Z(5), z)),
      plus(plus(Z(7), gain(z, 2)), times(z, z))) : null;
    if (!value) return {value: null, logAbs: Infinity, phase: null};
    const length = mod(value);
    return {value, logAbs: length ? Math.log(length) : -Infinity,
      phase: length ? Math.atan2(value[1], value[0]) : null};
  }
  phase = Math.atan2(Math.sin(phase), Math.cos(phase));
  value = logAbs < -740 ? Z() : logAbs > 700 ? null : polar(Math.exp(logAbs), phase);
  return {value, logAbs, phase};
}
function genuinePoles(s) {
  if (s.station === 'C1') return s.directionalFn === 'pathology' ? [Z()] : [];
  if (s.station === 'C2') return s.contourFn === 'rational' ?
    [s.residueA ? Z() : null, s.residueB ? Z(2) : null].filter(Boolean) :
    s.contourFn === 'poles' ? [Z(0, 1), Z(0, -1)] :
    ['laurent', 'annulus-inverse'].includes(s.contourFn) ? [Z()] : [];
  if (s.station === 'C3') return s.taylorFn === 'exp' ? [] :
    s.taylorFn === 'geometric' ? [Z(1)] : [Z(0, 1), Z(0, -1)];
  if (s.station === 'C5') return s.meanFn === 'geometric' ? [Z(1)] : [];
  if (s.station === 'C6') return s.arcFn === 'one' ? [] : s.arcFn === 'linear' ?
    [Z(0, -s.poleA)] : [Z(0, s.poleA), Z(0, -s.poleA)];
  return [];
}
function sampled(actual, expected, label) {
  near(actual.logAbs, expected.logAbs, label + ' log');
  if (expected.phase === null) assert.equal(actual.phase, null, label + ' undefined zero/pole phase');
  else near(Math.atan2(Math.sin(actual.phase - expected.phase), Math.cos(actual.phase - expected.phase)), 0, label + ' phase');
  complexNear(actual.value, expected.value, label + ' value');
}
function phaseColor(phase) {
  if (phase == null) return '#83949a';
  const angle = ((phase / tau % 1) + 1) % 1 * 6;
  const secondary = 1 - Math.abs(angle % 2 - 1);
  const rgb = [[1,secondary,0],[secondary,1,0],[0,1,secondary],[0,secondary,1],[secondary,0,1],[1,0,secondary]][Math.floor(angle) % 6];
  return 'rgb(' + rgb.map(v => Math.round(45 + 145 * v)).join(',') + ')';
}
function zeroMayCross(s, bounds, radialMin, radialMax) {
  // Exact zeros or a sufficient nonzero certificate, derived from the named
  // numerators rather than from production zeroCertificate metadata.
  if(s.station==='C6')return false; // exp(ikz) times 1 or a reciprocal has no zeros.
  const name=({C1:s.directionalFn,C2:s.contourFn,C3:s.taylorFn,C4:s.growthFn,C5:s.meanFn})[s.station];
  const contains=(x,y)=>bounds.x0<=x&&x<=bounds.x1&&bounds.y0<=y&&y<=bounds.y1;
  if(name==='peak')return radialMin<=1&&radialMax>=1;
  if(['z2','linear','annulus-z','conjugate','abs2','pathology'].includes(name))return contains(0,0);
  if(name==='rational'){
    if(!s.residueA&&!s.residueB)return true;
    if(!s.residueA||!s.residueB||s.residueA+s.residueB===0)return false;
    return contains(2*s.residueA/(s.residueA+s.residueB),0);
  }
  if(name==='laurent'){
    // P(z)=sum a_j z^j; the mean-value integral along a line in a convex
    // rectangle gives |P(z)-P(c)| <= |z-c| sum j|a_j|R^(j-1).
    const coefficients=[3,5,7,2,1],center=Z((bounds.x0+bounds.x1)/2,(bounds.y0+bounds.y1)/2);
    const value=coefficients.toReversed().reduce((v,a)=>plus(times(v,center),Z(a)),Z());
    const derivativeBound=coefficients.slice(1).reduce((sum,a,i)=>sum+(i+1)*Math.abs(a)*radialMax**i,0);
    const distance=Math.hypot(bounds.x1-bounds.x0,bounds.y1-bounds.y0)/2;
    const variation=distance*derivativeBound,magnitude=mod(value);
    return !(magnitude-variation>64*Number.EPSILON*(magnitude+variation+1));
  }
  return false;
}
function complexScene(scene) {
  finiteScene(scene);
  const s = scene.state, data = scene.complex, poles = genuinePoles(s);
  labelsInclude(scene,['Re z',s.heightMode==='magnitude'?'|f|':'ln |f|','Im z','Re f / scale','Output plane','Im f / scale']);
  const expectedExtent = Math.max(s.domainExtent,
    ['C2', 'C5'].includes(s.station) ? Math.abs(s.circleRe) + s.radius : 0,
    ['C2', 'C5'].includes(s.station) ? Math.abs(s.circleIm) + s.radius : 0,
    s.station === 'C4' ? s.growthRadius : s.station === 'C6' ? s.arcRadius : 0);
  near(data.extent, expectedExtent, 'Input span');
  assert.equal(data.fields.length, 576, 'Bounded 24 by 24 mesh');
  const cells = primitives(scene, 'function_cell');
  const height = a => s.heightMode === 'magnitude' ? Math.exp(a.logAbs) : a.logAbs;
  let count = 0;
  for (let i = 0; i < 24; i++) for (let j = 0; j < 24; j++) {
    const x0 = -expectedExtent + expectedExtent * i / 12, x1 = -expectedExtent + expectedExtent * (i + 1) / 12;
    const y0 = -expectedExtent + expectedExtent * j / 12, y1 = -expectedExtent + expectedExtent * (j + 1) / 12;
    const corners = [Z(x0,y0), Z(x1,y0), Z(x1,y1), Z(x0,y1)];
    const values = corners.map(p => named(s, p));
    const critical = poles.some(p => p[0] >= x0 && p[0] <= x1 && p[1] >= y0 && p[1] <= y1);
    const radialMin=Math.hypot(x0>0?x0:x1<0?x1:0,y0>0?y0:y1<0?y1:0),radialMax=Math.max(...corners.map(mod));
    const annulus=s.station==='C2'&&s.contourFn.startsWith('annulus');
    const domainContained=!annulus||radialMin>.25&&radialMax<4.5;
    const zeroPossible=zeroMayCross(s,{x0,x1,y0,y1},radialMin,radialMax);
    const visible = !critical && domainContained && (s.heightMode!=='log'||!zeroPossible) && values.every(v => Number.isFinite(height(v)) && Math.abs(height(v)) <= s.heightCrop);
    const field = data.fields[i * 24 + j];
    assert.equal(field.critical, critical, 'Independent pole/discontinuity cell classification');
    assert.equal(field.zeroCertificate.possible,zeroPossible,'Independent exact-zero or polynomial nonzero certificate');
    assert.equal(field.visible, visible, 'Independent finite/crop cell classification');
    values.forEach((v, k) => sampled(field.samples[k], v, 'Vertex'));
    const actual = cells.filter(v => v.i === i && v.j === j);
    assert.equal(actual.length, Number(visible), 'Omitted cells cannot be capped or bridged');
    if (!visible) continue;
    count++;
    lineNear(actual[0].points, corners.map((z, k) => [z[0],height(values[k]),-z[1]]), 'Emitted facet transform');
    assert.equal(actual[0].color, phaseColor(named(s, Z((x0+x1)/2,(y0+y1)/2)).phase), 'Cyclic phase colour');
  }
  assert.equal(cells.length, count);
  assert.equal(data.cells.length, count);
  lineNear(primitives(scene, 'critical_input').map(p => p.points[0]), poles.map(p => [p[0],0,-p[1]]), 'Genuine pole markers');
  const probe = ['C1', 'C3'].includes(s.station) ? Z(s.pointRe,s.pointIm) : s.station === 'C4' ?
    Z(s.growthRadius) : s.station==='C2'?Z(s.circleRe+s.radius,s.circleIm):s.station==='C5'?Z(s.circleRe,s.circleIm):Z(0,(s.halfPlane==='upper'?1:-1)*s.arcRadius);
  const probeSample = named(s, probe);
  vector(primitive(scene, 'input_probe').points[0], [probe[0],0,-probe[1]], 'Input probe transform');
  sampled(data.sample, probeSample, 'Uncropped probe');
  const probeHeight = primitives(scene, 'probe_height');
  const probeInDomain=s.station!=='C2'||!s.contourFn.startsWith('annulus')||mod(probe)>.25&&mod(probe)<4.5;
  const showProbe = probeInDomain && Number.isFinite(height(probeSample)) && Math.abs(height(probeSample)) <= s.heightCrop;
  assert.equal(probeHeight.length, Number(showProbe));
  if (showProbe) lineNear(probeHeight[0].points, [[probe[0],0,-probe[1]],[probe[0],height(probeSample),-probe[1]]], 'Probe height');

  const active = data.active;
  let inputCurve = [], outputValues = [];
  const center = Z(s.circleRe,s.circleIm), winding = Number(s.winding);
  if (['C2','C5'].includes(s.station)) inputCurve = Array.from({length:129}, (_, i) =>
    plus(center, polar(s.radius, tau * (s.station === 'C2' ? winding : 1) * i / 128)));
  if (s.station === 'C3' && s.taylorFn !== 'exp') inputCurve = Array.from({length:97}, (_, i) => polar(1,tau*i/96));
  if (s.station === 'C4') inputCurve = Array.from({length:97}, (_, i) => polar(s.growthRadius,tau*i/96));
  if (s.station === 'C6') inputCurve = Array.from({length:97}, (_, i) => polar(s.arcRadius,(s.halfPlane==='upper'?1:-1)*pi*i/96));
  const actualInput = primitives(scene, 'input_curve');
  assert.equal(actualInput.length, Number(inputCurve.length > 0));
  if (inputCurve.length) lineNear(actualInput[0].points, inputCurve.map(z => [z[0],0,-z[1]]), 'Oriented input contour');
  const contourInDomain=s.station!=='C2'||!s.contourFn.startsWith('annulus')||Math.abs(mod(center)-s.radius)>.25&&mod(center)+s.radius<4.5;
  if (['C2','C5'].includes(s.station) && !active.pathPole && contourInDomain) outputValues = inputCurve.map(p => named(s,p).value);
  const extras = [];
  if (s.station === 'C1') {
    const step = polar(10 ** s.logStep, s.angle*pi/180), a = named(s,plus(probe,step)), b = probeSample;
    const quotient = a.value && b.value ? divide(minus(a.value,b.value),step) : null;
    const pathologyOrigin=s.directionalFn==='pathology'&&mod(probe)===0;
    const quotientLog=pathologyOrigin?-Math.cos(4*s.angle*pi/180)/(10**s.logStep)**4-Math.log(10**s.logStep):quotient?Math.log(mod(quotient)):Infinity;
    if (quotient&&!(pathologyOrigin&&(quotientLog<-740||quotientLog>700))) extras.push(quotient);
    lineNear(primitive(scene,'approach_step').points, [[probe[0],0,-probe[1]],
      [probe[0]+step[0],0,-probe[1]-step[1]]], 'Directional step length and angle');
    assert.equal(active.cr, ['z2','exp','pathology'].includes(s.directionalFn) || s.directionalFn==='abs2' && mod(probe)===0);
    assert.equal(active.pointwise, ['z2','exp'].includes(s.directionalFn) || s.directionalFn==='abs2' && mod(probe)===0 || s.directionalFn==='pathology' && mod(probe)!==0);
    if(s.directionalFn==='pathology'&&mod(probe)===0){
      const theta=s.angle*pi/180,h=10**s.logStep,log=-Math.cos(4*theta)/h**4-Math.log(h);
      near(active.selected.logAbs,log,'Pathological quotient logarithm');
      if(log<-740)assert.equal(active.selected.status,'underflow-log-only');
      if(log>700)assert.equal(active.selected.status,'overflow-log-only');
    } else if(quotient)complexNear(active.selected.value,quotient,'Independent directional quotient');
  }
  if (s.station === 'C2') {
    let residues = s.contourFn === 'rational' ? [Z(s.residueA),Z(s.residueB)].filter((_,i)=>i===0?s.residueA:s.residueB) :
      s.contourFn === 'laurent' ? [Z(5)] : s.contourFn === 'poles' ? [Z(0,-.5),Z(0,.5)] : s.contourFn==='annulus-inverse' ? [Z(1)] : [];
    const pathPole = poles.some(p=>Math.abs(mod(minus(p,center))-s.radius)<=1e-12);
    assert.equal(active.pathPole,pathPole);
    let sum=Z(); poles.forEach((p,i)=>{if(mod(minus(p,center))<s.radius)sum=plus(sum,gain(residues[i],winding));});
    complexNear(active.integral,pathPole?null:times(Z(0,tau),sum),'Signed residue integral');
    if (s.contourFn.startsWith('annulus')) assert.equal(active.contourInDomain,
      Math.abs(mod(center)-s.radius)>.25 && mod(center)+s.radius<4.5,'Annulus hypotheses');
  }
  if (s.station === 'C3') {
    let factorial=1, partial=Z();
    for(let degree=0;degree<=s.terms;degree++) {
      if(degree)factorial*=degree;
      const coefficient=s.taylorFn==='geometric'?1:s.taylorFn==='poles'?degree%2?0:(-1)**(degree/2):1/factorial;
      near(active.coefficients[degree],coefficient,'Taylor coefficient');
      partial=plus(partial,gain(power(probe,degree),coefficient));
    }
    complexNear(active.partial,partial,'Independent finite Taylor polynomial');extras.push(partial);
    near(active.radius,s.taylorFn==='exp'?Infinity:1,'Nearest singularity radius');
    assert.equal(active.valid,s.taylorFn==='exp'||mod(probe)<1,'Open convergence disk');
    complexNear(active.error,probeSample.value?minus(probeSample.value,partial):null,'Actual finite Taylor error');
    if(active.valid){const radius=mod(probe),bound=s.taylorFn==='geometric'?radius**(s.terms+1)/(1-radius):
      s.taylorFn==='poles'?radius**(2*Math.floor(s.terms/2)+2)/(1-radius*radius):Math.exp(radius)*radius**(s.terms+1)/(factorial*(s.terms+1));
      near(active.remainderBound,bound,'Valid open-disk remainder bound');}
    else assert.equal(active.remainderBound,null,'No bound promised at or beyond convergence boundary');
    assert.equal(active.inference.selected,Number(s.inferenceRadius));assert.equal(active.inference.endpointsAllowed,true);
    assert.equal(active.inference.boundaryDetermined,false);
  }
  if (s.station === 'C4') {
    const disk=s.growthFn==='constant'?1:s.growthFn==='linear'?s.growthRadius:Math.exp(s.growthRadius);
    near(active.diskMaximum,disk,'Exact compact-disk maximum');near(active.hypotheticalCauchyBound,s.globalM/s.growthRadius,'Hypothetical M/R');
    assert.equal(active.globalBounded,s.growthFn==='constant');assert.equal(active.steps.length,Number(s.proofStep));
    const points=Array.from({length:45},(_,i)=>{const r=.5+11.5*i/44;return [3.5*expectedExtent+r/6,.1*s.globalM/r,-expectedExtent/2];});
    lineNear(primitive(scene,'hypothetical_cauchy_bound').points,points,'Uniform hypothetical theorem strip');
  }
  if (s.station === 'C5') {
    const distance=mod(minus(Z(1),center)),holomorphic=!['abs2','peak'].includes(s.meanFn),contained=s.meanFn!=='geometric'||distance>s.radius;
    let mean=active.pathPole?null:s.meanFn==='abs2'?Z(mod(center)**2+s.radius**2):s.meanFn==='peak'?Z(1-mod(center)**2-s.radius**2):
      s.meanFn==='geometric'&&distance<s.radius?Z():probeSample.value;
    complexNear(active.mean,mean,'Complex circle mean');if(mean)extras.push(mean);
    assert.equal(active.meanEquality,holomorphic&&contained);assert.equal(active.constantEquality,s.meanFn==='constant');
    if(!active.pathPole){
      const maxRadius=mod(center)+s.radius,minRadius=Math.abs(mod(center)-s.radius);
      const maximum=s.meanFn==='constant'?1:['z2','abs2'].includes(s.meanFn)?maxRadius**2:
        s.meanFn==='exp'?Math.exp(center[0]+s.radius):s.meanFn==='geometric'?1/Math.abs(distance-s.radius):
        Math.max(Math.abs(1-minRadius**2),Math.abs(1-maxRadius**2));
      near(active.maxModulus,maximum,'Exact boundary modulus maximum');
      const modulusMean=simpson(theta=>Z(mod(named(s,plus(center,polar(s.radius,theta))).value)),0,tau,8192)[0]/tau;
      near(active.modulusMean,modulusMean,'Independent modulus circle quadrature',2e-7);
    }
  }
  if (s.station === 'C6') {
    const sign=s.halfPlane==='upper'?1:-1;
    lineNear(primitive(scene,'real_segment').points,[[-s.arcRadius,0,0],[s.arcRadius,0,0]],'Real-axis forward orientation');
    assert.equal(active.orientation,sign);assert.equal(active.matching,s.k*sign>0);
    assert.equal(active.certificate,s.k*sign>0&&s.arcFn!=='one');
    const residue=s.arcFn==='one'?Z():s.arcFn==='linear'?sign<0?Z(Math.exp(s.k*s.poleA)):Z():
      sign>0?Z(0,-Math.exp(-s.k*s.poleA)/(2*s.poleA)):Z(0,Math.exp(s.k*s.poleA)/(2*s.poleA));
    complexNear(active.closedIntegral,times(Z(0,sign*tau),residue),'Oriented Jordan residue integral');
    if(s.arcFn==='one')complexNear(active.arcIntegral,Z(s.k===0?-2*s.arcRadius:-2*Math.sin(s.k*s.arcRadius)/s.k),'Nondecaying arc counterexample');
    const real=simpson(x=>named(s,Z(x)).value,-s.arcRadius,s.arcRadius,4096);
    const arc=simpson(theta=>{const z=polar(s.arcRadius,sign*theta);return times(named(s,z).value,times(Z(0,sign),z));},0,pi,4096);
    complexNear(active.realIntegral,real,'Independent finite real integral',3e-7);
    complexNear(active.arcIntegral,arc,'Independent finite arc integral',3e-7);
    const factorSup=s.arcFn==='one'?1:s.arcFn==='linear'?sign<0?1/(s.arcRadius-s.poleA):1/Math.hypot(s.arcRadius,s.poleA):1/(s.arcRadius**2-s.poleA**2);
    near(active.factorSupremum,factorSup,'Analytic arc supremum');
    near(active.jordanBound,s.k*sign>0?pi*factorSup/Math.abs(s.k):null,'Conditional Jordan bound');
  }
  const finiteValues=outputValues.filter(Boolean), finiteExtras=extras.filter(Boolean);
  const representableProbe=!!probeSample.value&&(probeSample.logAbs===-Infinity||probeSample.logAbs>=-740&&probeSample.logAbs<=700);
  const scale=Math.max(1,...finiteValues.map(mod),...finiteExtras.map(mod),representableProbe?mod(probeSample.value):0);
  near(data.outputScale,scale,'Uniform output-plane scale');
  const output=p=>[3.5*expectedExtent+expectedExtent*p[0]/scale,0,-expectedExtent*p[1]/scale];
  const out=primitives(scene,'output_curve');
  assert.equal(out.length,Number(outputValues.length>1&&finiteValues.length===outputValues.length));
  if(out.length)lineNear(out[0].points,outputValues.map(output),'Closed complex output transform');
  const marker=primitives(scene,'output_probe');assert.equal(marker.length,Number(probeInDomain&&representableProbe));
  if(marker.length)vector(marker[0].points[0],output(probeSample.value),'Output probe independent transform');
  lineNear(primitives(scene,'auxiliary_output').map(p=>p.points[0]),finiteExtras.map(output),'Auxiliary values in same output scale');
  return scene;
}

// Independent stationary-well coefficients and Born CDF, using exact SI energy.
function energy(n,L) { return h*h*n*n/(8*mass*(L*1e-9)**2*eV); }
function wellCoefficients(s) {
  const choices=s.projection!=='none'?[[Number(s.projection),1,0]]:s.wellState==='eigen'?[[s.n,1,0]]:
    [[1,Math.sqrt(1-s.mix),0],[2,Math.sqrt(s.mix),s.phaseDeg*pi/180]];
  return choices.map(([n,a,relative])=>({n,value:polar(a,s.globalPhaseDeg*pi/180+relative-energy(n,s.lengthNm)*s.timeFs/(hbar/eV*1e15)),p:a*a}));
}
function wellValue(s,x) {
  if(x<=0||x>=s.lengthNm)return Z();
  return wellCoefficients(s).reduce((v,c)=>plus(v,gain(c.value,Math.sqrt(2/s.lengthNm)*Math.sin(c.n*pi*x/s.lengthNm))),Z());
}
function wellCDF(s,u) {
  u=Math.max(0,Math.min(1,u));const cc=wellCoefficients(s);
  let p=cc.reduce((v,c)=>v+c.p*(u-Math.sin(2*c.n*pi*u)/(2*c.n*pi)),0);
  if(cc.length===2)p+=2*times(cc[0].value,conjugate(cc[1].value))[0]*(Math.sin(pi*u)/pi-Math.sin(3*pi*u)/(3*pi));
  return p;
}
function randomSequence(s,salt=0) {
  let state=(s.seed+((s.batch+1)*2654435761)+salt)%4294967296;
  return ()=>{state=(1664525*state+1013904223)%4294967296;return state/4294967296;};
}
function expectedHistogram(s) {
  const rng=randomSequence(s),bins=Array(20).fill(0),positions=[];
  for(let i=0;i<s.detections;i++){
    const uniform=rng();let low=0,high=1;
    for(let j=0;j<45;j++){const mid=(low+high)/2;if(wellCDF(s,mid)<uniform)low=mid;else high=mid;}
    const u=(low+high)/2;bins[Math.min(19,Math.floor(u*20))]++;positions.push(u*s.lengthNm);
  }
  return {bins,positions};
}
function gaussianPosition(s,x) {
  const u=(x-s.centerNm)/s.sigmaNm;
  return polar(Math.exp(-u*u/4)/Math.pow(tau*s.sigmaNm*s.sigmaNm,.25),s.chirp*u*u/4+s.kCenter*x);
}
function gaussianMomentum(s,k) {
  // Gaussian integral: sqrt(1-ib) has its principal square root.
  const q=k-s.kCenter,A=Z(1,-s.chirp),sqrt=polar(Math.sqrt(mod(A)),Math.atan2(A[1],A[0])/2);
  const prefactor=divide(Z(Math.pow(2*s.sigmaNm*s.sigmaNm/pi,.25)),sqrt);
  return times(prefactor,exp(plus(divide(Z(-s.sigmaNm*s.sigmaNm*q*q),A),Z(0,-q*s.centerNm))));
}
function simpson(fn,a,b,n=2048) {
  let value=Z();for(let i=0;i<=n;i++)value=plus(value,gain(fn(a+(b-a)*i/n),i===0||i===n?1:i%2?4:2));
  return gain(value,(b-a)/(3*n));
}
function solveComplex(matrix,rhs) {
  const rows=matrix.map((r,i)=>[...r.map(v=>[...v]),[...rhs[i]]]);
  for(let column=0;column<rows.length;column++) {
    let pivot=column;for(let i=column+1;i<rows.length;i++)if(mod(rows[i][column])>mod(rows[pivot][column]))pivot=i;
    [rows[pivot],rows[column]]=[rows[column],rows[pivot]];
    assert.ok(mod(rows[column][column])>0,'Nonzero matching-system pivot');
    const divisor=rows[column][column];rows[column]=rows[column].map(v=>divide(v,divisor));
    for(let i=0;i<rows.length;i++)if(i!==column){const factor=rows[i][column];rows[i]=rows[i].map((v,j)=>minus(v,times(factor,rows[column][j])));}
  }
  return rows.map(r=>r.at(-1));
}
function barrierSolve(s) {
  const k=Math.sqrt(2*mass*s.energyEV*eV)/hbar*1e-9,kappa=Math.sqrt(2*mass*(s.heightEV-s.energyEV)*eV)/hbar*1e-9;
  const grow=Math.exp(kappa*s.widthNm),decay=1/grow,travel=polar(1,k*s.widthNm),ik=Z(0,k);
  // Unknowns [r,A,B,t]; match both psi and its derivative at x=0 and x=a.
  const [r,A,B,t]=solveComplex([
    [Z(1),Z(-1),Z(-1),Z()], [gain(ik,-1),Z(-kappa),Z(kappa),Z()],
    [Z(),Z(grow),Z(decay),gain(travel,-1)],
    [Z(),Z(kappa*grow),Z(-kappa*decay),gain(times(ik,travel),-1)],
  ],[Z(-1),gain(ik,-1),Z(),Z()]);
  return {k,kappa,r,A,B,t};
}
function scatteringAt(s,c,x) {
  let value,derivative;
  if(x<0){const incident=polar(1,c.k*x),reflected=times(c.r,polar(1,-c.k*x));value=plus(incident,reflected);derivative=times(Z(0,c.k),minus(incident,reflected));}
  else if(x>s.widthNm){value=times(c.t,polar(1,c.k*x));derivative=times(Z(0,c.k),value);}
  else{const growing=gain(c.A,Math.exp(c.kappa*x)),decaying=gain(c.B,Math.exp(-c.kappa*x));value=plus(growing,decaying);derivative=gain(minus(growing,decaying),c.kappa);}
  return {value,derivative,current:hbar/mass*1e9*times(conjugate(value),derivative)[1]};
}
function quantumScene(scene) {
  finiteScene(scene);const s=scene.state,d=scene.quantum.current;
  if(s.mode==='well') {
    labelsInclude(scene,['x / nm','Re ψ / nm⁻¹/²','Im ψ / nm⁻¹/²','Bin count / N']);
    const cc=wellCoefficients(s),expected=Array.from({length:161},(_,i)=>{const x=s.lengthNm*i/160,v=wellValue(s,x);return [x,...v];});
    lineNear(primitive(scene,'well_amplitude').points,expected,'Analytic normalized well amplitude');
    lineNear(primitive(scene,'well_density').points,expected.map(p=>[p[0],p[1]*p[1]+p[2]*p[2],-2.5]),'Born density strip');
    vector(primitive(scene,'well_probe').points[0],[s.probe*s.lengthNm,...wellValue(s,s.probe*s.lengthNm)],'Well probe');
    lineNear(primitive(scene,'well_region').points,[[s.regionStart*s.lengthNm,0,-2.5],[s.regionEnd*s.lengthNm,0,-2.5]],'Selected interval coordinates');
    for(const sample of scene.quantum.samples){
      const hPsi=cc.reduce((v,c)=>plus(v,gain(c.value,energy(c.n,s.lengthNm)*Math.sqrt(2/s.lengthNm)*Math.sin(c.n*pi*sample.input/s.lengthNm))),Z());
      if(sample.input>0&&sample.input<s.lengthNm){complexNear(sample.value.hPsiEV,hPsi,'Independently applied Hamiltonian');complexNear(sample.value.iHbarDtEV,hPsi,'Time evolution equation');}
    }
    near(d.regionalProbability,wellCDF(s,s.regionEnd)-wellCDF(s,s.regionStart),'Exact Born interval');
    near(d.meanEnergyEV,cc.reduce((v,c)=>v+c.p*energy(c.n,s.lengthNm),0),'Energy expectation');
    cc.forEach((c,i)=>{complexNear(d.coefficients[i],c.value,'Schrödinger coefficient');near(d.energies[i].probability,c.p,'Energy Born probability');});
    const scale=Math.max(1,...cc.map(c=>energy(c.n,s.lengthNm)));
    const energies=primitives(scene,'well_energy');assert.equal(energies.length,cc.length);
    cc.forEach((c,i)=>lineNear(energies[i].points,[[s.lengthNm+.4,2*energy(c.n,s.lengthNm)/scale,-1.8],[s.lengthNm+.7,2*energy(c.n,s.lengthNm)/scale,-1.8]],'Calibrated eV strip'));
    const bins=expectedHistogram(s),bars=primitives(scene,'well_count');assert.equal(bars.length,20);
    for(let i=0;i<20;i++){
      assert.equal(d.counts.histogram[i].count,bins.bins[i],'Independent inverse-CDF detections');
      near(d.counts.histogram[i].probability,wellCDF(s,(i+1)/20)-wellCDF(s,i/20),'Exact finite-bin Born mass');
      const a=i/20*s.lengthNm,b=(i+1)/20*s.lengthNm,y=bins.bins[i]/s.detections;
      lineNear(bars[i].points,[[a,0,-3.2],[b,0,-3.2],[b,y,-3.2],[a,y,-3.2]],'Finite count fraction geometry');
    }
    near(d.counts.histogram.reduce((v,b)=>v+b.probability,0),1,'Histogram full mass');
    assert.equal(d.counts.histogram.reduce((v,b)=>v+b.count,0),s.detections,'Count conservation');
    assert.equal(d.energyMeasurement.projectedN,s.projection==='none'?null:Number(s.projection));
    assert.equal(d.energyMeasurement.immediateRepeatProbability,1);
    assert.equal(primitives(scene,'hard_wall').length,2);
    for(const wall of primitives(scene,'hard_wall'))lineNear(wall.points,[[wall.xNm,-2,-2],[wall.xNm,2,-2],[wall.xNm,2,2],[wall.xNm,-2,2],[wall.xNm,-2,-2]],'Hard wall plane');
  } else if(s.mode==='spin') {
    labelsInclude(scene,['⟨σx⟩','⟨σz⟩','⟨σy⟩','Original input','Selected z+','Final z+','Final z−']);
    const axis=a=>a==='x'?[1,0,0]:a==='y'?[0,1,0]:[0,0,1];
    const bloch=s.prep==='unpolarized'?[0,0,0]:axis(s.prep[0]).map(v=>v*(s.prep[1]==='+'?1:-1));
    const a=axis(s.axis),dot=bloch.reduce((v,x,i)=>v+x*a[i],0),p=(1+dot)/2;
    near(d.measurement.plus,p,'Pauli projector probability');near(d.measurement.minus,1-p,'Complement projector');
    const display=v=>[v[0],v[2],-v[1]];
    lineNear(primitive(scene,'prepared_bloch').points,[[0,0,0],display(bloch)],'Bloch expectation transform');
    lineNear(primitive(scene,'measurement_axis').points,[display(a).map(v=>-v),display(a)],'Measurement-axis transform');
    const first=(1+bloch[2])/2,middle=s.middle==='bypass'?1:s.middle==='z'?(s.middleSign==='+'?1:0):.5;
    const selected=s.middle==='bypass'?[0,0,1]:axis(s.middle).map(v=>v*(s.middleSign==='+'?1:-1));
    const final=(1+selected[2])/2,survival=first*middle;
    const probabilities=[first,survival,survival*final,survival*(1-final)];
    const branches=primitives(scene,'spin_branch');assert.equal(branches.length,4);
    const branchCoordinates=[[[2,0,0],[3,.6,0]],[[3,.6,0],[4,.6,0]],[[4,.6,0],[5,1.2,0]],[[4,.6,0],[5,0,0]]];
    probabilities.forEach((v,i)=>{near(branches[i].probabilityOriginal,v,'Original-input branch denominator');near(branches[i].width,1+5*v,'Probability-to-width gain');lineNear(branches[i].points,branchCoordinates[i],'Schematic branch connections');});
    const circles=primitives(scene,'bloch_unit_circle');assert.equal(circles.length,3);
    circles.forEach((circle,index)=>lineNear(circle.points,Array.from({length:65},(_,i)=>{const p=[0,0,0];p[(index+1)%3]=Math.cos(tau*i/64);p[(index+2)%3]=Math.sin(tau*i/64);return display(p);}), 'Unit Bloch calibration circle'));
    near(d.tree.middleConditional,middle,'Per first survivor');near(d.tree.finalConditionalPlus,final,'Per middle survivor');
    assert.equal(d.tree.conditionalDefined,survival>0,'Zero survivors have no empirical conditional frequency');
    near(d.tree.blockedOriginal+probabilities[2]+probabilities[3],1,'Probability branch conservation');
    assert.equal(d.counts.finalPlus+d.counts.finalMinus,d.counts.middleSelected);assert.equal(d.counts.blockedAtFirst+d.counts.blockedAtMiddle+d.counts.middleSelected,s.detections);
  } else if(s.mode==='gaussian') {
    labelsInclude(scene,['x / nm','Re ψ / nm⁻¹/²','Im ψ / nm⁻¹/²','k / (10 nm⁻¹)','5 Re φ / nm¹/²','5 Im φ / nm¹/²']);
    const sigmaK=Math.sqrt(1+s.chirp*s.chirp)/(2*s.sigmaNm);
    near(d.sigmaKNmInverse,sigmaK,'Fourier spread');near(d.uncertaintyInHbar,s.sigmaNm*sigmaK,'Dimensionless uncertainty');
    near(d.sigmaPSI,hbar*sigmaK*1e9,'SI momentum units',1e-36);
    const tail=simpson(x=>Z(Math.exp(-x*x/2)/Math.sqrt(tau)),s.cropSigma,12,1024)[0];
    for(const key of ['positionCrop','momentumCrop']){near(d[key].leftTail,tail,'Unrenormalized omitted tail',2e-11);near(d[key].insideMass,1-2*tail,'Finite crop mass');}
    const x=Array.from({length:161},(_,i)=>s.centerNm+s.sigmaNm*s.cropSigma*(-1+i/80));
    const k=Array.from({length:161},(_,i)=>s.kCenter+sigmaK*s.cropSigma*(-1+i/80));
    const xp=x.map(v=>[v,...gaussianPosition(s,v)]),kp=k.map(v=>{const a=gaussianMomentum(s,v);return [4+v/10,5*a[0],5*a[1]];});
    lineNear(primitive(scene,'gaussian_position_amplitude').points,xp,'Position complex phase');
    lineNear(primitive(scene,'gaussian_momentum_amplitude').points,kp,'Fourier phase and amplitude gain');
    lineNear(primitive(scene,'gaussian_position_density').points,x.map(v=>[v,mod(gaussianPosition(s,v))**2,-2.5]),'Position density units');
    lineNear(primitive(scene,'gaussian_momentum_density').points,k.map(v=>[4+v/10,5*mod(gaussianMomentum(s,v))**2,-2.5]),'Momentum density per k and gain');
    for(const selected of [s.kCenter,s.kCenter+.7*sigmaK]){
      const integral=simpson(v=>times(gaussianPosition(s,v),polar(1,-selected*v)),s.centerNm-12*s.sigmaNm,s.centerNm+12*s.sigmaNm);
      vector(gain(integral,1/Math.sqrt(tau)),gaussianMomentum(s,selected),'Direct Fourier quadrature',2e-9);
    }
  } else if(s.mode==='barrier') {
    labelsInclude(scene,['x / nm','Re ψ; incident amplitude 1','Im ψ; incident amplitude 1']);
    const coefficients=barrierSolve(s),span=Math.max(.35,2/coefficients.k);
    for(const key of ['r','A','B','t'])complexNear(d[key],coefficients[key],'Independently solved matching coefficient '+key);
    for(const error of Object.values(d.matching))assert.ok(error<2e-9,'Both interfaces match amplitudes and derivatives');
    const expected=Array.from({length:241},(_,i)=>{const x=-span+(s.widthNm+2*span)*i/240;return [x,...scatteringAt(s,coefficients,x).value];});
    lineNear(primitive(scene,'barrier_amplitude').points,expected,'Matched three-region amplitude');
    const T=1/(1+s.heightEV*s.heightEV*Math.sinh(coefficients.kappa*s.widthNm)**2/(4*s.energyEV*(s.heightEV-s.energyEV)));
    near(d.T,T,'Analytic finite-barrier transmission');near(d.R,1-T,'Reflection and current conservation');
    const current=hbar/mass*coefficients.k*1e9*T;
    near(d.currents.transmitted,current,'Transmitted SI current');near(d.currents.internal,current,'Evanescent net current',3e-9);
    for(const x of [-.1,0,s.widthNm/2,s.widthNm,s.widthNm+.1])near(scatteringAt(s,coefficients,x).current,current,'Independently conserved current',3e-9);
    assert.equal(d.outgoingEnergyEV,s.energyEV,'No energy loss or borrowing');
    lineNear(primitive(scene,'barrier_potential').points,[[-span,0,-2],[0,0,-2],[0,.25*s.heightEV,-2],[s.widthNm,.25*s.heightEV,-2],[s.widthNm,0,-2],[s.widthNm+span,0,-2]],'Potential eV coordinate gain');
    lineNear(primitive(scene,'barrier_energy').points,[[-span,.25*s.energyEV,-2],[s.widthNm+span,.25*s.energyEV,-2]],'Energy eV coordinate gain');
    const flux=primitives(scene,'flux_fraction');lineNear(flux[0].points,[[s.widthNm+span+.5,0,-1],[s.widthNm+span+.5,1-T,-1]],'Reflection flux height');
    lineNear(flux[1].points,[[s.widthNm+span+.5,0,1],[s.widthNm+span+.5,T,1]],'Transmission flux height');
    assert.equal(d.counts.reflected+d.counts.transmitted,s.detections);
  } else {
    labelsInclude(scene,['λ / (100 nm)','E / eV','Separate phase reference','One wavelength; phase reference only']);
    const hc=h*light/eV*1e9,E=hc/s.wavelengthNm;
    near(d.energyEV,E,'Exact SI photon energy');near(d.energyJ,E*eV,'Photon joule conversion',1e-30);
    near(d.roundedConventionEV,1240/s.wavelengthNm,'Distinct rounded assessment convention');
    lineNear(primitive(scene,'photon_energy_curve').points,Array.from({length:161},(_,i)=>{const wavelength=200+5*i;return [wavelength/100,hc/wavelength,0];}),'Photon dispersion units');
    vector(primitive(scene,'photon_energy_probe').points[0],[s.wavelengthNm/100,E,0],'Photon wavelength marker');
    lineNear(primitive(scene,'photon_phase_reference').points,Array.from({length:65},(_,i)=>[s.wavelengthNm*i/6400,0,-2+.5*Math.sin(tau*i/64)]),'One wavelength with fixed display amplitude');
  }
  return scene;
}

function run() {
  let complexCount=0,quantumCount=0;
  const C=s=>{complexCount++;return complexScene(buildComplex(s));};
  const Q=s=>{quantumCount++;return quantumScene(buildQuantum(s));};
  for(const directionalFn of ['z2','exp','conjugate','abs2','pathology']) {
    C({station:'C1',directionalFn,pointRe:.5,pointIm:.25,angle:30});
    C({station:'C1',directionalFn,pointRe:0,pointIm:0,heightMode:'magnitude'});
  }
  C({station:'C1',directionalFn:'pathology',angle:0,logStep:-4,heightMode:'magnitude'});
  C({station:'C1',directionalFn:'exp',angle:180,logStep:-4,pointRe:-.75,pointIm:.5,heightCrop:1});
  for(const contourFn of ['rational','laurent','poles','annulus-inverse','annulus-z'])for(const winding of ['1','-2'])
    C({station:'C2',contourFn,circleRe:.25,circleIm:.5,radius:1.25,winding,residueA:-2,residueB:0});
  C({station:'C2',contourFn:'poles',radius:1});
  C({station:'C2',contourFn:'rational',residueA:0,residueB:0,radius:2});
  for(const taylorFn of ['geometric','poles','exp'])for(const pointRe of [.5,1,1.5])C({station:'C3',taylorFn,pointRe,pointIm:.25,terms:9});
  C({station:'C3',taylorFn:'geometric',pointRe:1,pointIm:0,terms:24});
  for(const growthFn of ['constant','linear','exp'])C({station:'C4',growthFn,growthRadius:4,globalM:3});
  for(const meanFn of ['z2','exp','constant','abs2','peak','geometric'])C({station:'C5',meanFn,circleRe:.5,circleIm:.25,radius:1.25});
  C({station:'C5',meanFn:'geometric',circleRe:0,radius:1});
  const peakLog=C({station:'C5',meanFn:'peak'}),peakMagnitude=C({station:'C5',meanFn:'peak',heightMode:'magnitude'});
  const peakIndex=15*24+16;
  assert.equal(peakLog.complex.fields[peakIndex].visible,false,'Interior zero circle cannot be bridged in a logarithmic facet');
  assert.ok(peakLog.complex.fields[peakIndex].samples.every(sample=>Number.isFinite(sample.logAbs)&&Math.abs(sample.logAbs)<5),'Zero-ring regression has finite uncropped corners');
  assert.equal(peakMagnitude.complex.fields[peakIndex].visible,true,'Magnitude projection crosses a true zero continuously');
  const rationalZero=C({station:'C2',contourFn:'rational',residueA:1,residueB:2,domainExtent:1.7});
  const rationalZeroCells=rationalZero.complex.fields.filter(field=>field.bounds.x0<=2/3&&field.bounds.x1>=2/3&&field.bounds.y0<=0&&field.bounds.y1>=0);
  assert.ok(rationalZeroCells.length>0);rationalZeroCells.forEach(field=>assert.equal(field.visible,false,'Off-grid rational zero cannot be bridged'));
  const laurentZero=C({station:'C2',contourFn:'laurent',domainExtent:3,heightCrop:12});
  const polynomialRoots=[Z(-.60543020266388159,2.2654696095052369),Z(-.60543020266388159,-2.2654696095052369),
    Z(-.39456979733611752,.62440251735213004),Z(-.39456979733611752,-.62440251735213004)];
  for(const root of polynomialRoots){
    const residual=[1,2,7,5,3].reduce((v,a)=>plus(times(v,root),Z(a)),Z());
    assert.ok(mod(residual)<2e-12,'Independent fixed Laurent root calibration');
    const containing=laurentZero.complex.fields.filter(field=>field.bounds.x0<=root[0]&&field.bounds.x1>=root[0]&&field.bounds.y0<=root[1]&&field.bounds.y1>=root[1]);
    assert.equal(containing.length,1);assert.equal(containing[0].visible,false,'Uncertified Laurent root cell is omitted');
  }
  for(const arcFn of ['one','linear','quadratic'])for(const halfPlane of ['upper','lower'])for(const k of [-1,0,1])
    C({station:'C6',arcFn,halfPlane,k,arcRadius:3,poleA:1});
  // True zero vs. log underflow and overflow must remain distinct semantically.
  const pathology=C({station:'C1',directionalFn:'pathology',pointRe:0,pointIm:0,angle:45,logStep:-1});
  assert.equal(pathology.complex.sample.phase,null);assert.ok(pathology.complex.active.selected.logAbs>9000);
  assert.equal(pathology.complex.active.pointwise,false);assert.equal(pathology.complex.active.cr,true);

  for(const E1 of [1.5,2]) {
    const L=h/Math.sqrt(8*mass*E1*eV)*1e9;
    for(const n of [1,3,4]){const scene=Q({mode:'well',wellState:'eigen',n,lengthNm:L,detections:64});assert.equal(scene.state.lengthNm,L);near(scene.quantum.current.energy1EV,E1,'Exact assessed well width');near(scene.quantum.current.meanEnergyEV,E1*n*n,'Assessed n squared energy');}
  }
  for(const phaseDeg of [0,90,180])for(const globalPhaseDeg of [0,73])Q({mode:'well',mix:.37,phaseDeg,globalPhaseDeg,timeFs:.271,detections:96,batch:2});
  for(const projection of ['none','1','2','5','6']){
    const scene=Q({mode:'well',wellState:'eigen',n:5,projection,lengthNm:.8,detections:64,probe:.71});
    assert.equal(scene.state.projection,['none','5'].includes(projection)?projection:'none','Only the prepared eigenenergy can be observed');
    assert.equal(scene.quantum.current.energies[0].n,5,'Impossible eigenenergy request retains the prepared eigenstate');
  }
  for(const [raw,expected] of [
    [{wellState:'eigen',n:1,projection:'6'},'none'],
    [{wellState:'superposition',mix:0,projection:'2'},'none'],
    [{wellState:'superposition',mix:1,projection:'1'},'none'],
    [{wellState:'superposition',mix:0,projection:'1'},'1'],
    [{wellState:'superposition',mix:1,projection:'2'},'2'],
    [{wellState:'superposition',mix:.37,projection:'1'},'1'],
    [{wellState:'superposition',mix:.37,projection:'2'},'2'],
    [{wellState:'eigen',n:3,projection:'3'},'3'],
    [{wellState:'eigen',n:4,projection:'4'},'4'],
  ]){
    const scene=Q({mode:'well',...raw,detections:32});
    assert.equal(scene.state.projection,expected,'Observed energy requires positive prepared Born probability');
    if(expected==='none'){
      const unmeasured=buildQuantum({mode:'well',...raw,projection:'none',detections:32});
      assert.deepEqual(scene.quantum.current,unmeasured.quantum.current,'Impossible alternative outcome leaves complete unmeasured state/data intact');
      assert.deepEqual(scene.primitives,unmeasured.primitives,'Impossible alternative outcome cannot draw a false collapsed state');
    }else assert.equal(scene.quantum.current.energyMeasurement.immediateRepeatProbability,1,'Supported observed energy repeats with certainty');
  }
  Q({mode:'well',mix:1,detections:32});
  for(const prep of ['z+','z-','x+','x-','y+','y-','unpolarized'])for(const axis of ['x','y','z'])Q({mode:'spin',prep,axis,detections:32});
  for(const middle of ['x','y','z','bypass'])for(const middleSign of ['+','-'])Q({mode:'spin',prep:'unpolarized',middle,middleSign,detections:32});
  for(const chirp of [-3,0,2.25])for(const cropSigma of [2,4,6])Q({mode:'gaussian',sigmaNm:.173,centerNm:.71,kCenter:-1.3,chirp,cropSigma});
  for(const widthNm of [0,.013,.2,.73,2])Q({mode:'barrier',energyEV:1.25,heightEV:2.4,widthNm,detections:64});
  Q({mode:'barrier',energyEV:4,heightEV:.2,widthNm:.001,detections:32});
  for(const wavelengthNm of [200,500,543.21,1000])Q({mode:'photon',wavelengthNm});

  // Full state survives mode switches, including inactive controls and batches.
  const fullComplex={...buildComplex({}).state,directionalFn:'conjugate',pointRe:.75,pointIm:-.5,angle:120,
    logStep:-3,contourFn:'rational',residueA:-2,residueB:0,circleRe:1,circleIm:-.75,radius:.75,winding:'-2',
    taylorFn:'exp',terms:13,inferenceRadius:'3',growthFn:'exp',growthRadius:5,globalM:4,proofStep:'2',
    meanFn:'peak',arcFn:'linear',k:-.75,halfPlane:'lower',arcRadius:4,poleA:1.25,domainExtent:1.37,heightCrop:3.17,heightMode:'magnitude'};
  for(const station of ['C1','C2','C3','C4','C5','C6'])assert.deepEqual(C({...fullComplex,station}).state,{...fullComplex,station});
  const fullQuantum={...buildQuantum({}).state,wellState:'eigen',n:4,lengthNm:.4123456789,mix:.37,phaseDeg:71.3,
    globalPhaseDeg:-42.7,timeFs:.371,projection:'4',regionStart:.12,regionEnd:.81,probe:.61,prep:'y-',axis:'y',middle:'z',middleSign:'-',
    sigmaNm:.176,centerNm:-.231,kCenter:2.13,chirp:-2.17,cropSigma:3.8,energyEV:1.31,heightEV:3.72,widthNm:.291,
    wavelengthNm:543.21,detections:73,seed:127,batch:42};
  for(const mode of ['well','spin','gaussian','barrier','photon'])assert.deepEqual(Q({...fullQuantum,mode}).state,{...fullQuantum,mode});
  const complexControls=window.PrimerSpatial.controls('module.math.5.complex-analysis');
  const quantumControls=window.PrimerSpatial.controls('module.phys.4.quantum');
  for(const c of complexControls.filter(v=>!v.options))assert.equal(c.numericInput,true,'Complex numeric field retains authored bounds');
  for(const c of quantumControls.filter(v=>!v.options))assert.equal(c.preserveExact,true,'Quantum exact numeric controls');
  assert.equal(quantumControls.find(v=>v.key==='batch').max,1000000);
  for(const [key,min,max,expected] of [['domainExtent',.5,5,2],['heightCrop',1,12,5]]) {
    for(const value of [null,true,false,'',' ',[],{},NaN,Infinity,-Infinity])assert.equal(buildComplex({[key]:value}).state[key],expected,'Malformed optional display control uses its default');
    assert.equal(buildComplex({[key]:-100}).state[key],min);assert.equal(buildComplex({[key]:100}).state[key],max);
    assert.equal(buildComplex({[key]:'2.1234567'}).state[key],2.1234567);
  }
  for(const value of [null,true,' ',NaN,Infinity])assert.equal(buildQuantum({lengthNm:value}).state.lengthNm,1);
  assert.equal(buildQuantum({wellState:'superposition',projection:'6'}).state.projection,'none');
  assert.equal(buildQuantum({batch:1e9,seed:1e9,detections:-100}).state.batch,1000000);
  assert.equal(buildQuantum({regionStart:.9,regionEnd:.1}).state.regionStart,.1);

  // Changes that legitimately preserve geometry still update their semantic ledger.
  const theoremA=buildComplex({station:'C3',inferenceRadius:'2'}),theoremB=buildComplex({station:'C3',inferenceRadius:'3'});
  assert.deepEqual(theoremA.primitives,theoremB.primitives);assert.equal(theoremB.complex.active.inference.selected,3);assert.notEqual(theoremA.readout,theoremB.readout);
  const theoremLedgerA=window.PrimerMathComplexLab.build({station:'C3',inferenceRadius:'2'}),theoremLedgerB=window.PrimerMathComplexLab.build({station:'C3',inferenceRadius:'3'});
  assert.deepEqual(theoremLedgerA.rows.slice(0,-1),theoremLedgerB.rows.slice(0,-1),'All numerical Taylor ledger rows preserved by assessed inference selection');
  assert.equal(theoremLedgerB.rows.at(-1)[1],'2 ≤ R ≤ 3');assert.ok(theoremLedgerB.rows.at(-1)[2].includes('Selected 3; endpoints allowed; boundary undetermined'));
  assert.deepEqual(theoremLedgerA.proof,theoremLedgerB.proof);
  const proofA=buildComplex({station:'C4',proofStep:'1'}),proofB=buildComplex({station:'C4',proofStep:'6'});
  assert.deepEqual(proofA.primitives,proofB.primitives);assert.equal(proofB.complex.active.steps.length,6);assert.notEqual(proofA.readout,proofB.readout);
  const proofLedgerA=window.PrimerMathComplexLab.build({station:'C4',proofStep:'1'}),proofLedgerB=window.PrimerMathComplexLab.build({station:'C4',proofStep:'6'});
  assert.deepEqual(proofLedgerA.rows.slice(0,-1),proofLedgerB.rows.slice(0,-1),'All analytic bound ledger rows preserved by proof reveal');
  assert.deepEqual(proofLedgerB.active.steps.map(step=>step.id),['root-free','reciprocal','exterior','interior','liouville','contradiction']);
  assert.equal(proofLedgerB.rows.at(-1)[1],'6/6');
  const invariantA=buildQuantum({mode:'well',globalPhaseDeg:0,detections:64}),invariantB=buildQuantum({mode:'well',globalPhaseDeg:90,detections:64});
  lineNear(primitive(invariantA,'well_density').points,primitive(invariantB,'well_density').points,'Common phase leaves Born geometry invariant');
  assert.notDeepEqual(primitive(invariantA,'well_amplitude').points,primitive(invariantB,'well_amplitude').points);
  const phaseLedgerA=window.PrimerPhysicsQuantumLab.build(invariantA.state),phaseLedgerB=window.PrimerPhysicsQuantumLab.build(invariantB.state);
  for(let i=0;i<phaseLedgerA.ledger.length;i++){
    const a=phaseLedgerA.ledger[i],b=phaseLedgerB.ledger[i];assert.equal(a[0],b[0]);assert.equal(a[2],b[2]);
    if(['Probe Re ψ','Probe Im ψ'].includes(a[0]))continue;
    if(typeof a[1]==='number')near(a[1],b[1],'Full common-phase semantic ledger invariance');else assert.equal(a[1],b[1]);
  }
  const probePhase=wellValue(invariantB.state,invariantB.state.probe*invariantB.state.lengthNm);
  near(phaseLedgerB.ledger.find(row=>row[0]==='Probe Re ψ')[1],probePhase[0],'Rotated real amplitude ledger');
  near(phaseLedgerB.ledger.find(row=>row[0]==='Probe Im ψ')[1],probePhase[1],'Rotated imaginary amplitude ledger');
  const batchA=buildQuantum({mode:'well',batch:0,detections:64}),batchB=buildQuantum({mode:'well',batch:1,detections:64});
  assert.deepEqual(primitive(batchA,'well_amplitude'),primitive(batchB,'well_amplitude'));assert.notDeepEqual(batchA.quantum.current.counts.positions,batchB.quantum.current.counts.positions);
  const gaussA=buildQuantum({mode:'gaussian',chirp:0}),gaussB=buildQuantum({mode:'gaussian',chirp:2});
  lineNear(primitive(gaussA,'gaussian_position_density').points,primitive(gaussB,'gaussian_position_density').points,'Chirp preserves position density');
  assert.ok(gaussB.quantum.current.sigmaKNmInverse>gaussA.quantum.current.sigmaKNmInverse);
  const inactiveA=buildQuantum({mode:'photon',mix:.1}),inactiveB=buildQuantum({mode:'photon',mix:.9});
  assert.deepEqual(inactiveA.primitives,inactiveB.primitives);assert.equal(inactiveB.quantum.state.mix,.9);
  const inactiveLedgerA=window.PrimerPhysicsQuantumLab.build(inactiveA.state),inactiveLedgerB=window.PrimerPhysicsQuantumLab.build(inactiveB.state);
  assert.equal(inactiveLedgerB.state.mix,.9);delete inactiveLedgerA.state;delete inactiveLedgerB.state;
  assert.deepEqual(inactiveLedgerA,inactiveLedgerB,'Full active semantic model preserved for an inactive preparation control');
  // Calibration negatives prove that the validators inspect emitted geometry.
  const shifted=structuredClone(buildQuantum({mode:'photon'}));primitive(shifted,'photon_energy_probe').points[0][0]+=.01;
  assert.throws(()=>quantumScene(shifted),/Photon wavelength marker/);
  const badBranch=structuredClone(buildQuantum({mode:'spin',prep:'unpolarized'}));primitives(badBranch,'spin_branch')[2].width+=.1;
  assert.throws(()=>quantumScene(badBranch),/Probability-to-width gain/);
  const bridge=structuredClone(buildComplex({station:'C2',contourFn:'poles'}));
  primitives(bridge,'function_cell')[0].points[0][2]+=.01;
  assert.throws(()=>complexScene(bridge),/Emitted facet transform/);
  return {status:'passed',complexStates:complexCount,quantumStates:quantumCount,complexStations:6,quantumModes:5,
    independentOracles:['named complex values/logs/phases/poles','primitive input/output/probe/cell transforms',
      'oriented contours and residue/mean/Taylor/theorem semantics','analytic well coefficients/Born CDF/seeded bins',
      'Pauli expectations and original/survivor probabilities','complex Gaussian integral/direct Fourier quadrature/tails',
      'four-equation barrier matching/current/energy/potential','exact SI photon dispersion/phase-reference gain'],
    regressionChecks:['C5 closed output loop','malformed optional control defaults','calibration mutation rejection',
      'full inactive state retention','exact assessed well widths','batch/projection retention','legitimate geometry invariances',
      'full semantic ledger checks for invariant/theorem controls','zero-locus log-facet omission',
      'impossible alternative energy outcomes retain preparation']};
}
function fixtures() {
  // A bounded, fixed observation packet for the second-language oracles. This
  // exports actual primitives/data, never computed expected numbers.
  const states=[
    {mode:'well',wellState:'superposition',lengthNm:.4336070583942774,mix:.37,phaseDeg:61,
      globalPhaseDeg:-42,timeFs:.213,probe:.71,regionStart:.12,regionEnd:.81,detections:73,seed:127,batch:42},
    {mode:'spin',prep:'unpolarized',axis:'y',middle:'x',middleSign:'-',detections:32},
    {mode:'gaussian',sigmaNm:.173,centerNm:.71,kCenter:-1.3,chirp:2.25,cropSigma:3.8},
    {mode:'barrier',energyEV:1.31,heightEV:3.72,widthNm:.291,detections:32},
    {mode:'photon',wavelengthNm:543.21},
  ];
  return states.map(raw=>{
    const scene=buildQuantum(raw),model=window.PrimerPhysicsQuantumLab.build(raw);
    return {state:scene.state,current:scene.quantum.current,primitives:scene.primitives,
      samples:scene.quantum.samples,curves:scene.quantum.curves,ledger:model.ledger,
      equation:model.equation,note:model.note};
  });
}
if(require.main===module){
  assert.ok(process.argv.length===2||process.argv.length===3&&process.argv[2]==='--fixtures','Only the fixed --fixtures observation mode is supported');
  console.log(JSON.stringify(process.argv[2]==='--fixtures'?fixtures():run()));
}
module.exports={run,complexScene,quantumScene,buildComplex,buildQuantum,barrierSolve,gaussianMomentum,fixtures};

#!/usr/bin/env node
'use strict';
// Independent oracles: matrix operators, Jacobi eigenvalues, quadrature,
// numerical derivatives and on-shell four-vector identities.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const runtimePath = path.join(root, 'web/physics-qft-lab.js');
const qft = require(runtimePath);
const counts = {};
let comparisons = 0;
function close(actual, expected, context, rel = 2e-11, abs = 2e-12) {
  assert.ok(Number.isFinite(actual) && Number.isFinite(expected), context + ': non-finite');
  assert.ok(Math.abs(actual - expected) <= abs + rel * Math.abs(expected),
    context + ': ' + actual + ' vs ' + expected);
  comparisons++;
}
function bump(group) { counts[group] = (counts[group] || 0) + 1; }
const C = 299792458, H = 6.62607015e-34, EV = 1.602176634e-19;
const HB = H / (2 * Math.PI), HC = HB * C / EV * 1e9;
const ME = 0.51099895069;
const mat = (r, c) => Array.from({length:r}, () => Array(c).fill(0));
function product(a,b) { return a.map(row => b[0].map((_,j) => row.reduce((s,x,k) => s+x*b[k][j],0))); }
function mv(a,v) { return a.map(row => row.reduce((s,x,i) => s+x*v[i],0)); }
const dot = (a,b) => a.reduce((s,x,i) => s+x*b[i],0);
function transpose(a) { return a[0].map((_,j) => a.map(row => row[j])); }
function jacobiEigenvalues(input) {
  const a = input.map(row => [...row]);
  for (let iteration=0; iteration<80; iteration++) {
    let p=0,q=1,big=0;
    for (let i=0;i<a.length;i++) for(let j=i+1;j<a.length;j++) if(Math.abs(a[i][j])>big) { p=i; q=j; big=Math.abs(a[i][j]); }
    if(big<1e-14) break;
    const theta=.5*Math.atan2(2*a[p][q], a[q][q]-a[p][p]);
    const c=Math.cos(theta),s=Math.sin(theta),rot=mat(a.length,a.length);
    for(let i=0;i<a.length;i++) rot[i][i]=1;
    rot[p][p]=rot[q][q]=c; rot[p][q]=s; rot[q][p]=-s;
    const changed=product(transpose(rot),product(a,rot));
    for(let i=0;i<a.length;i++) for(let j=0;j<a.length;j++) a[i][j]=changed[i][j];
  }
  return a.map((row,i)=>row[i]).sort((a,b)=>a-b);
}
function simpson(fn,a,b,n=16384) {
  assert.equal(n%2,0);
  let sum=fn(a)+fn(b),h=(b-a)/n;
  for(let i=1;i<n;i++) sum+=(i%2?4:2)*fn(a+i*h);
  return sum*h/3;
}
function radialNumerical(cutoff, A, B=null) {
  // k=exp(t)-1 resolves the low k region even at Lambda=10^8.
  return simpson(t => {
    const k=Math.expm1(t),z=k*k;
    const body=B===null?1/(z+A)**2:(B-A)*(2*z+A+B)/((z+A)**2*(z+B)**2);
    return k*k*k*body*Math.exp(t);
  },0,Math.log1p(cutoff));
}

// Canonical oscillator operators in a larger finite basis; tested levels are
// well below the artificial top edge. Neither coefficient nor q variance
// oracle calls the implementation's formula helpers.
const a=mat(12,12);
for(let n=1;n<12;n++) a[n-1][n]=Math.sqrt(n);
const ad=transpose(a), number=product(ad,a), canonical=mat(12,12);
for(let i=0;i<12;i++) for(let j=0;j<12;j++) canonical[i][j]=(a[i][j]+ad[i][j])/Math.sqrt(2);
const q2=product(canonical,canonical);
for(const boxFm of [100,1200,10000]) for(const massMeV of [.01,.511,10]) for(let j=-4;j<=4;j++) for(let n=0;n<=8;n++) {
  const d=qft.freeModes({boxFm,massMeV,modeIndex:j,occupation:n,fieldKind:'boson'});
  const f=n===0?0:Math.sqrt(dot(mv(ad,Array.from({length:12},(_,i)=>i===n?1:0)),mv(ad,Array.from({length:12},(_,i)=>i===n?1:0))));
  close(d.creationCoefficient,n===0?1:f,'creation matrix norm');
  close(d.annihilationCoefficient,Math.sqrt(number[n][n]),'annihilation matrix norm');
  close(d.varianceCanonicalQ,q2[n][n],'number-state q variance');
  close(d.meanCanonicalQ,canonical[n][n],'number-state mean q');
  const pc=H*C/EV*1e9*j/boxFm,energy=Math.sqrt(pc*pc+massMeV*massMeV);
  close(d.selected.energy,energy,'periodic relativistic energy',2e-10);
  close(d.excitationEnergy,number[n][n]*energy,'Hamiltonian excitation',2e-10);
  for(const row of d.rows) close(row.energy**2-row.pc**2,massMeV**2,'common field rest parameter',2e-9);
  bump('bosonic_operator_states');
}
const b=[[0,1],[0,0]],bd=transpose(b),fermionN=product(bd,b),anti=product(b,bd).map((row,i)=>row.map((x,j)=>x+fermionN[i][j]));
for(const n of [0,1,2,8]) {
  const d=qft.freeModes({fieldKind:'fermion',occupation:n});
  assert.equal(d.selected.occupation,Math.min(n,1));
  const v=[n===0?1:0,n===0?0:1];
  close(d.creationCoefficient,Math.sqrt(dot(mv(bd,v),mv(bd,v))),'Pauli creation');
  close(d.annihilationCoefficient,Math.sqrt(dot(mv(b,v),mv(b,v))),'Pauli annihilation');
  assert.equal(d.occupationLimit,1);
  for(let i=0;i<2;i++) for(let j=0;j<2;j++) close(anti[i][j],i===j?1:0,'fermion anticommutator');
  bump('fermionic_operator_states');
}

const minkowski=p=>p[0]*p[0]-dot(p.slice(1),p.slice(1));
for(const massMeV of [.01,.511,10]) for(const momentumMeV of [0,.001,1,10]) for(const angleDeg of [0,.00001,30,90,179.99999,180]) {
  const d=qft.scattering({massMeV,momentumMeV,angleDeg});
  for(const v of [d.p1,d.p2,d.p3,d.p4]) close(minkowski(v),massMeV**2,'external mass shell',2e-9);
  for(let i=0;i<4;i++) close(d.p1[i]+d.p2[i],d.p3[i]+d.p4[i],'momentum conservation');
  close(d.t,minkowski(d.p1.map((x,i)=>x-d.p3[i])),'t invariant');
  close(d.u,minkowski(d.p1.map((x,i)=>x-d.p4[i])),'u invariant');
  close(d.sInvariant,minkowski(d.p1.map((x,i)=>x+d.p2[i])),'s invariant');
  close(d.sInvariant+d.t+d.u,4*massMeV**2,'Mandelstam identity',2e-9);
  assert.ok(d.t<=2e-12);
  if(momentumMeV>0 && angleDeg>0) assert.ok(d.t<0);
  else assert.ok(d.t===0);
  bump('elastic_com_states');
}

const beta=[[1,0,0,0],[0,1,0,0],[0,0,-1,0],[0,0,0,-1]];
const alphaZ=[[0,0,1,0],[0,0,0,-1],[1,0,0,0],[0,-1,0,0]];
for(const massMeV of [.01,.511,10]) for(const momentumMeV of [0,.0001,.1,1,10]) for(const chargeUnits of [-3,-1,0,1,3]) {
  const d=qft.antiparticles({massMeV,momentumMeV,chargeUnits});
  const matrix=beta.map((row,i)=>row.map((x,j)=>massMeV*x+momentumMeV*alphaZ[i][j]));
  const square=product(matrix,matrix),sorted=jacobiEigenvalues(matrix);
  const expected=[...d.eigenvalues].sort((x,y)=>x-y);
  sorted.forEach((x,i)=>close(x,expected[i],'Jacobi Dirac eigenvalue'));
  for(let i=0;i<4;i++) for(let j=0;j<4;j++) {
    close(d.H[i][j],matrix[i][j],'Dirac basis Hamiltonian');
    close(square[i][j],i===j?massMeV**2+momentumMeV**2:0,'Dirac Clifford square');
  }
  for(const [v,e] of [[d.positive,d.physicalParticleEnergy],[d.negative,-d.physicalAntiparticleEnergy]]) {
    close(dot(v,v),1,'Dirac vector norm');
    mv(matrix,v).forEach((x,i)=>close(x,e*v[i],'Dirac eigenvector residual'));
  }
  close(dot(d.positive,d.negative),0,'Dirac branch orthogonality');
  assert.ok(d.physicalParticleEnergy>0 && d.physicalAntiparticleEnergy>0);
  close(d.particleCharge+d.antiparticleCharge,0,'conjugate electric charges');
  bump('dirac_states');
}

for(const massMultiple of [.1,1,100,1000]) {
  const d=qft.compton({massMultiple}),mass=9.1093837139e-31*massMultiple;
  close(d.ordinaryM,H/(mass*C),'NIST ordinary Compton',1e-10,1e-26);
  close(d.reducedM,HB/(mass*C),'NIST reduced Compton',1e-10,1e-26);
  close(d.ordinaryM/d.reducedM,2*Math.PI,'Compton convention');
  close(d.pairThresholdMeV,2*ME*massMultiple,'COM threshold rest energy');
  close(d.quizUnits,243/massMultiple,'rounded quiz convention');
  bump('compton_states');
}
close(qft.compton({massMultiple:100}).quizUnits,2.43,'quiz ordinary 100m');

for(const cutoff of [1,10,1000,1e8]) for(const probeScale of [.1,1,3,10]) for(const referenceScale of [.1,1,10]) {
  const d=qft.renormalization({cutoff,probeScale,referenceScale});
  close(d.Iq,radialNumerical(cutoff,1+probeScale**2),'regulator quadrature',3e-10);
  close(d.Iu,radialNumerical(cutoff,1+referenceScale**2),'matching quadrature',3e-10);
  const difference=radialNumerical(cutoff,1+probeScale**2,1+referenceScale**2);
  close(d.difference,difference,'independently integrated subtraction',3e-10);
  close(d.observable,.2+.05*difference,'matched prediction',3e-10);
  close(d.finiteCutoffError,d.observable-d.continuumObservable,'retained finite cutoff remainder');
  if(probeScale===referenceScale) close(d.observable,.2,'exact matching point');
  bump('radial_quadrature_states');
}
for(const [A,B] of [[1.01,2],[2,101],[101,1.01]]) {
  const integral=radialNumerical(1e8,A,B);
  close(qft.subtraction(1e8,A,B),integral,'large-cutoff numerical convergence',3e-10);
  close(qft.subtraction(1e8,A,B),.5*Math.log(B/A),'continuum identity',3e-10);
  bump('continuum_comparisons');
}

// Lifshitz perfect-reflector Euclidean integrals, independent of runtime
// coefficients 720 and 240. The removable endpoint has its exact limit.
const energyIntegral=simpson(x=>x===0?0:x*x*Math.log(-Math.expm1(-x)),0,80,65536);
const pressureIntegral=simpson(x=>x===0?0:x*x*x/Math.expm1(x),0,80,65536);
for(const gapUm of [.1,.5,1,5]) for(const areaMm2 of [.01,1,100]) {
  const d=qft.casimir({gapUm,areaMm2}),a=gapUm*1e-6;
  const e=HB*C/(16*Math.PI**2*a**3)*energyIntegral;
  const p=-HB*C/(16*Math.PI**2*a**4)*pressureIntegral;
  close(d.energyPerArea,e,'Lifshitz energy integral',3e-9,1e-23);
  close(d.pressure,p,'Lifshitz pressure integral',3e-9,1e-15);
  close(d.force,p*areaMm2*1e-6,'pressure to total force',3e-9,1e-20);
  const step=a*1e-4,ea=qft.casimir({gapUm:(a-step)*1e6}).energyPerArea,eb=qft.casimir({gapUm:(a+step)*1e6}).energyPerArea;
  // Boundary values cannot be differentiated through normalization clamp.
  if(gapUm>.1 && gapUm<5) close(d.pressure,-(eb-ea)/(2*step),'energy derivative sign',1e-7,1e-15);
  const f=qft.casimir({gapUm,parallelK:3,normalMode:2});
  close(f.omega**2/C**2,f.kz**2+f.kparallel**2,'EM normal-mode dispersion',1e-10);
  bump('casimir_integral_states');
}
close(qft.casimir({gapUm:.5}).pressure/qft.casimir({gapUm:1}).pressure,16,'Casimir pressure scaling');

for(const alpha of [0,1/137,.03,.1]) for(const coefficient of [-3,-1,0,1,3]) for(const phaseDeg of [-180,-90,0,90,180]) {
  const d=qft.perturbation({alpha,coefficient,phaseDeg,correctionKind:'amplitude'});
  const imaginary=coefficient*alpha*Math.sin(phaseDeg*Math.PI/180);
  const real=1+coefficient*alpha*Math.cos(phaseDeg*Math.PI/180);
  close(d.ratio,dot([real,imaginary],[real,imaginary]),'complex amplitude norm');
  close(d.ratio-d.linearRatio,alpha*alpha*coefficient*coefficient,'interference quadratic term');
  const rate=qft.perturbation({alpha,coefficient,phaseDeg,correctionKind:'rate'});
  close(rate.ratio,1+coefficient*alpha,'declared rate branch');
  if(Math.abs(phaseDeg)===90) close(d.linearPercentage,0,'orthogonal phase no linear correction');
  bump('perturbative_interference_states');
}
assert.equal(qft.perturbation({alpha:1/137,coefficient:1,correctionKind:'rate'}).percentage.toFixed(1),'0.7');

for(const mediatorMeV of [0,1,197,500]) for(const radiusFm of [.01,.1,1,5,10]) {
  const d=qft.mediator({mediatorMeV,radiusFm}),mu=mediatorMeV/HC;
  close(d.attenuation,Math.exp(-mu*radiusFm),'Yukawa e-fold',2e-10,1e-14);
  if(mediatorMeV===0) assert.equal(d.rangeFm,null);
  else close(d.rangeFm,HC/mediatorMeV,'massive Green-function range',2e-10);
  if(radiusFm>.01 && radiusFm<10) {
    const h=radiusFm*1e-3,w=r=>r*qft.mediator({mediatorMeV,radiusFm:r}).potentialMeV;
    const second=(-w(radiusFm+2*h)+16*w(radiusFm+h)-30*w(radiusFm)+16*w(radiusFm-h)-w(radiusFm-2*h))/(12*h*h);
    close(second,mu*mu*w(radiusFm),'radial Helmholtz equation outside source',2e-6,3e-5);
  }
  bump('yukawa_green_function_states');
}
close(qft.mediator({mediatorMeV:197}).quizRangeFm,1,'rounded mediator quiz');

// Leading vertex form factor in its zero photon-mass limit has parameter
// integral int_0^1 2x dx=1. Full multi-loop precision is intentionally absent.
const schwingerIntegral=simpson(x=>2*x,0,1);
for(const alpha of [0,1/137,.0072973525643,.1]) for(const fieldTesla of [0,.01,1,10]) {
  const d=qft.magnetic({alpha,fieldTesla}),anomaly=alpha/(2*Math.PI)*schwingerIntegral;
  close(d.anomaly,anomaly,'zero-mass vertex parameter integral');
  close(d.muB,9.2740100657e-24,'NIST magneton',1e-10,1e-35);
  close(d.spinUpJ+d.spinDownJ,0,'Zeeman signed levels',1e-11,1e-34);
  close(d.spinUpJ-d.spinDownJ,d.g*d.muB*fieldTesla,'Zeeman splitting',1e-11,1e-34);
  assert.ok(d.spinUpJ>=0 && d.spinDownJ<=0);
  bump('magnetic_vertex_states');
}

let sampledPoints=0,markers=0;
for(const [mode] of qft.stations) {
  const state=qft.build({mode});
  assert.equal(state.panels.length,2);
  assert.ok(state.note.includes('Float64'));
  for(const p of state.panels) {
    for(const c of p.curves) for(const xy of c.points) {
      assert.ok(Number.isFinite(xy.x)&&Number.isFinite(xy.y),mode+' sampled curve finite');
      sampledPoints++;
    }
    for(const marker of p.markers||[]) { assert.ok(Number.isFinite(marker.x)&&Number.isFinite(marker.y)); markers++; }
  }
  bump('station_chart_states');
}
// Exercise the actual adapter with an independent geometry recorder. The
// recorder does not call the application's graph builder or projection code.
const spatialPath=path.join(root,'web/spatial-qft.js');
let spatialPoints=0,spatialMarkers=0,standingVertices=0,standingFaces=0;
assert.ok(fs.existsSync(spatialPath),'actual spatial adapter must be present');
{
  global.window={PrimerPhysicsQftLab:qft};
  const family=require(spatialPath);
  for(const [mode] of qft.stations) for(const preset of [{},{momentumMeV:0,modeIndex:0,occupation:0,alpha:0},{momentumMeV:10,angleDeg:180,normalMode:6,parallelK:10,coefficient:-3,phaseDeg:90,correctionKind:'amplitude'}]) {
    const geometry={lines:[],spheres:[],polygons:[],labels:[],colors:{ink:'ink',teal:'teal',blue:'blue',gold:'gold',coral:'coral'},
      line(points,color,meta){this.lines.push({points,color,meta});},
      sphere(point,radius,color,meta){this.spheres.push({point,radius,color,meta});},
      polygon(points,color,meta){this.polygons.push({points,color,meta});},
      label(point,label){this.labels.push({point,label});}};
    const actual=family.build({mode,...preset},geometry),core=qft.build({mode,...preset});
    assert.deepEqual(actual.qft.state,core.state);
    if(mode==='scattering') assert.equal(core.panels[0].equalScale,true,'momentum component diagram preserves physical scattering angles');
    if(mode==='perturbation'&&core.state.correctionKind==='amplitude') assert.equal(core.panels[1].equalScale,true,'complex amplitude circle preserves phase angles');
    if(['compton','casimir','mediator'].includes(mode)) {
      const first=core.panels[0];
      for(const curve of first.curves) {
        assert.ok(curve.xUnit.includes('log') && curve.yUnit.includes('log'),'broad-domain logarithmic coordinates are labelled');
        for(const point of curve.points) {
          const physicalX=10**point.x,physicalY=10**point.y;
          let expected;
          if(mode==='compton') {
            expected=H*C/(ME*1e6*EV*physicalX);
            if(curve.key==='reduced') expected/=2*Math.PI;
          } else if(mode==='casimir') {
            expected=HB*C/(16*Math.PI**2*(physicalX*1e-6)**4)*pressureIntegral;
          } else {
            const mu=curve.key==='massless'?0:core.state.mediatorMeV/HC;
            expected=HC/physicalX*Math.exp(-mu*physicalX);
          }
          close(physicalY,expected,'inverse logarithmic '+mode+' physical curve '+curve.key,4e-9,1e-26);
        }
      }
      const selected=first.markers[0],current=core.current;
      close(10**selected.x,mode==='compton'?core.state.massMultiple:mode==='casimir'?core.state.gapUm:core.state.radiusFm,'inverse log selected abscissa');
      close(10**selected.y,mode==='compton'?current.ordinaryM:mode==='casimir'?-current.pressure:-current.potentialMeV,'inverse log selected signed magnitude',2e-10,1e-26);
      if(mode!=='compton') assert.ok(mode==='casimir'?current.pressure<0:current.potentialMeV<0,'attractive sign retained separately from log magnitude');
      bump('inverse_log_physical_chart_states');
    }
    for(const chart of actual.qft.charts) {
      const panel=core.panels[chart.index];
      if(panel.equalScale) close(chart.xGain,chart.yGain,'3D equal-unit isotropic chart');
      chart.graphs.forEach((graph,i)=>{
        assert.deepEqual(graph.source,panel.curves[i].points);
        assert.equal(graph.points.length,graph.source.length);
        graph.points.forEach((point,j)=>{
          const source=graph.source[j];
          close((point[0]-chart.origin[0])/chart.xGain+chart.xmin,source.x,'3D inverse x calibration',2e-9);
          close((point[1]-chart.origin[1])/chart.yGain+chart.ymin,source.y,'3D inverse y calibration',2e-9);
          close(point[2],chart.origin[2],'3D separate chart depth');
          spatialPoints++;
        });
      });
      chart.markers.forEach(marker=>{
        close((marker.point[0]-chart.origin[0])/chart.xGain+chart.xmin,marker.x,'3D marker inverse x');
        close((marker.point[1]-chart.origin[1])/chart.yGain+chart.ymin,marker.y,'3D marker inverse y');
        spatialMarkers++;
      });
    }
    for(const extra of actual.qft.extra) {
      if(extra.kind==='momentum') {
        const expected=core.current[extra.key].slice(1);
        extra.point.forEach((x,i)=>close((x-extra.origin[i])/extra.gain,expected[i],'physical 3D momentum components'));
      } else if(extra.kind==='diagram') {
        assert.ok(extra.points.length===2);
        [extra.from,extra.to].forEach((v,j)=>v.forEach((x,i)=>close(extra.points[j][i]-extra.offset[i],x,'categorical topology coordinate')));
        assert.ok(actual.note.includes('categorical'));
      } else if(extra.kind==='mode') {
        close((extra.point[0]-extra.origin[0])/extra.pGain,extra.source.pc,'mode momentum axis');
        close((extra.point[1]-extra.origin[1])/extra.nGain,extra.source.occupation,'mode occupation axis');
        close((extra.point[2]-extra.origin[2])/extra.eGain,extra.source.excitation,'mode excitation axis');
      } else if(extra.kind==='standing-factor') {
        assert.equal(extra.notVectorEM,true);
        for(const vertex of extra.points) {
          const expected=Math.sin(core.state.normalMode*Math.PI*vertex.zA)*Math.cos(core.current.kparallel*core.current.a*vertex.xA);
          close(vertex.factor,expected,'3D scalar standing factor');
          close((vertex.point[0]-extra.origin[0])/extra.xGain,vertex.xA,'standing factor x/a');
          close((vertex.point[1]-extra.origin[1])/extra.factorGain,expected,'standing factor field ordinate');
          close((vertex.point[2]-extra.origin[2])/extra.zGain,vertex.zA,'standing factor z/a');
          standingVertices++;
        }
        const faces=geometry.polygons.filter(p=>p.meta.fidelity_kind==='qft_standing_factor');
        assert.equal(faces.length,2*extra.nx*extra.nz);
        assert.ok(extra.interpolationErrorBound<=extra.errorBudget&&extra.errorBudget===.02);
        for(const face of faces) { assert.equal(face.points.length,3); for(const point of face.points) assert.ok(point.every(Number.isFinite)); standingFaces++; }
      }
    }
    for(const line of geometry.lines) for(const point of line.points) assert.ok(point.every(Number.isFinite));
    bump('actual_spatial_adapter_states');
  }
}
const result={review:'independent analytic/numerical QFT oracles',status:'pass',counts,comparisons,sampledPoints,markers,
  spatialPoints,spatialMarkers,standingVertices,standingFaces,
  runtime_sha256:crypto.createHash('sha256').update(fs.readFileSync(runtimePath)).digest('hex'),
  spatial_sha256:crypto.createHash('sha256').update(fs.readFileSync(spatialPath)).digest('hex'),
  check_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),
  scope:'Declared finite free modes, COM kinematics, free Dirac branches, Compton scales, scalar subtraction toy, ideal EM Casimir, illustrative amplitude/rate expansions, scalar static Green function and leading electron anomaly. No continuum QFT, clinical or full-project approval.'};
console.log(JSON.stringify(result,null,2));

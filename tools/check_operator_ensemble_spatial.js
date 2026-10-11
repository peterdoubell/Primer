#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
global.window={PrimerMathOperatorLab:require('../web/math-operator-lab.js'),
  PrimerPhysicsEnsembleLab:require('../web/physics-ensemble-lab.js')};
require('../web/spatial-models.js');
require('../web/spatial-module-objects.js');
const manifest=require('../data/module-models.json');
const bindings={};
for(const [node,family,lesson] of [['math.5.functional','operator-coordinate-graph','Functional Analysis'],['phys.4.statmech','ensemble-state-graph','Statistical Mechanics']]){
 const authored=manifest.models.find(m=>m.node_id===node);assert.equal(authored.family,family);assert.equal(authored.mode,'model');
 const item={props:{scenario:'module.'+node,family,mode:authored.mode,context:authored.context,lesson}};
 assert.ok(window.PrimerModuleObjects.ensure(item));bindings[family]=item.props.scenario;
}
const build=(family,s)=>window.PrimerSpatial.build(bindings[family],s);
const near=(a,b,label)=>assert.ok(Math.abs(a-b)<=3e-12*Math.max(1,Math.abs(a),Math.abs(b)),`${label}: ${a} != ${b}`);
const point=(a,b,label)=>{assert.equal(a.length,3);a.forEach((v,i)=>near(v,b[i],label+' axis '+i));};
// Independent reduced fractions and matrix multiplication. Expected ledgers
// never call either shipped numerical activity's build/resolve functions.
const gcd=(a,b)=>{a=a<0n?-a:a;while(b){const c=a%b;a=b;b=c;}return a||1n;};
function f(n,d=1n){n=BigInt(n);d=BigInt(d);if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return[n/g,d/g];}
const add=(a,b)=>f(a[0]*b[1]+b[0]*a[1],a[1]*b[1]);
const mul=(a,b)=>f(a[0]*b[0],a[1]*b[1]);
const neg=a=>[-a[0],a[1]],num=a=>Number(a[0])/Number(a[1]);
const squareSum=a=>a.reduce((s,v)=>add(s,mul(v,v)),f(0));
const exact=(packed,expected,label)=>assert.deepEqual([BigInt(packed.numerator),BigInt(packed.denominator)],expected,label);
let operatorStates=0,ensembleStates=0;
for(const operator of ['shift','diagonal'])for(const realization of ['infinite','matrix','finite-rank'])for(const N of [1,2,4,32])for(const position of ['first','boundary','tail'])for(const [first,second] of [[0,0],[4,0],[12,16],[-3,7],[-16,16]])for(const probe of ['zero','two-fifths','one']){
 const s={operator,realization,cutoff:N,position,first,second,probe},scene=build('operator-coordinate-graph',s),m=scene.operator;
 const k=position==='first'?1:position==='boundary'?N:N+1,lambda=probe==='zero'?f(0):probe==='one'?f(1):f(2,5);
 const length=Math.max(N+2,k+2),request=Array.from({length},()=>f(0));request[k-1]=f(first,4);request[k]=f(second,4);
 const accepted=request.map((v,j)=>realization==='matrix'&&j>=N?f(0):v),output=Array.from({length},()=>f(0));
 for(let row=0;row<length;row++)for(let col=0;col<length;col++){
  if(realization!=='infinite'&&(row>=N||col>=N))continue;
  const coefficient=operator==='shift'?f(Number(row===col+1)):row===col?f(1,row+1):f(0);
  output[row]=add(output[row],mul(coefficient,accepted[col]));
 }
 const residual=output.map((v,j)=>add(v,neg(mul(lambda,accepted[j]))));
 exact(m.lambda,lambda,'Exact spectral probe');
 for(const [key,expected] of [['input',accepted],['output',output],['residual',residual]]){
  const actual=m.selected[key],entries=new Map(actual.entries.map(e=>[e.index,e]));
  expected.forEach((v,j)=>{if(v[0])exact(entries.get(j+1),v,key+' coordinate');else assert.ok(!entries.has(j+1),key+' exact zero is omitted');});
  exact(actual.normSquared,squareSum(expected),key+' full squared norm');
  exact(actual.visibleSquared,squareSum(expected.slice(0,N)),key+' visible norm');
  exact(actual.offscreenSquared,squareSum(expected.slice(N)),key+' hidden norm');
 }
 exact(m.selected.excludedInputSquared,add(squareSum(request),neg(squareSum(accepted))),'Finite-domain excluded input');
 assert.equal(m.selected.zeroInput,squareSum(accepted)[0]===0n);
 assert.equal(m.selected.eigenvector,squareSum(accepted)[0]!==0n&&squareSum(residual)[0]===0n,'Zero cannot be an eigenvector');
 const spheres=scene.primitives.filter(p=>p.operator_kind==='coordinate_point'),stems=scene.primitives.filter(p=>p.operator_kind==='coordinate_pair');
 assert.equal(spheres.length,N);assert.equal(stems.length,N);
 for(let j=1;j<=N;j++){
  const expected=[j/N,num(accepted[j-1]),num(output[j-1])],sphere=spheres.find(p=>p.index===j),stem=stems.find(p=>p.index===j);
  point(sphere.points[0],expected,'Actual coefficient pair');near(sphere.radius,.025,'Fixed display dot');
  assert.equal(stem.points.length,3);point(stem.points[0],[j/N,0,0],'Stem origin');point(stem.points[1],[j/N,expected[1],0],'Input guide');point(stem.points[2],expected,'Output guide');
  point(m.plotted[j-1].point,expected,'Coordinate metadata');
 }
 const spec=m.selected.spectrum;
 if(operator==='shift'){
  exact(spec.distance,realization==='infinite'?f(0):probe==='zero'?f(0):lambda,'Shift spectral distance');
  assert.equal(spec.inSpectrum,realization==='infinite'||probe==='zero');assert.equal(spec.eigenvalue,realization!=='infinite'&&probe==='zero');
  assert.equal(spec.inverseNorm,null,'No reciprocal-distance resolvent for a nonnormal finite shift');
  exact(m.truncation,f(1),'All-N shift norm error');
 }else{
  const eigenpoints=Array.from({length:realization==='infinite'?100:N},(_,j)=>f(1,j+1));if(realization!=='matrix')eigenpoints.push(f(0));
  let closest;for(const e of eigenpoints){const delta=add(e,neg(lambda)),abs=f(delta[0]<0n?-delta[0]:delta[0],delta[1]);if(!closest||num(abs)<num(closest))closest=abs;}
  exact(spec.distance,closest,'Full reciprocal spectrum distance');
  if(closest[0])exact(spec.inverseNorm,f(closest[1],closest[0]),'Normal diagonal resolvent');else assert.equal(spec.inverseNorm,null);
  assert.equal(spec.inSpectrum,closest[0]===0n);assert.equal(spec.eigenvalue,closest[0]===0n&&(lambda[0]!==0n||realization==='finite-rank'));
  exact(m.truncation,f(1,N+1),'All-N diagonal norm error');
 }
 operatorStates++;
}
// Semantic changes at e_N must retain the same visible coefficient crop.
const canonical=build('operator-coordinate-graph',{});
for(const realization of ['infinite','matrix','finite-rank'])assert.deepEqual(build('operator-coordinate-graph',{realization}).primitives,canonical.primitives);
for(const probe of ['zero','two-fifths','one'])assert.deepEqual(build('operator-coordinate-graph',{probe}).primitives,canonical.primitives);
assert.equal(canonical.operator.selected.output.offscreenSquared.exact,'1');
assert.equal(build('operator-coordinate-graph',{realization:'matrix'}).operator.selected.output.normSquared.exact,'0');
const distant=build('operator-coordinate-graph',{operator:'diagonal',cutoff:2,probe:'two-fifths'});
assert.equal(distant.operator.selected.spectrum.closest.index,3);assert.equal(distant.operator.selected.spectrum.inverseNorm.exact,'15');
const matrix=build('operator-coordinate-graph',{operator:'diagonal',cutoff:2,probe:'two-fifths',realization:'matrix'});
assert.equal(matrix.operator.selected.spectrum.inverseNorm.exact,'10');
// For S_2 and λ=2/5, the inverse is [[-5/2,0],[-25/4,-5/2]].
// Its squared singular norm is the larger eigenvalue of B*B, where the
// numerator matrix is [[725,250],[250,100]] / 16. It exceeds 1/dist².
const actualNonnormalInverse=Math.sqrt((825+Math.sqrt(640625))/32);
assert.ok(actualNonnormalInverse>2.5);
assert.equal(build('operator-coordinate-graph',{cutoff:2,probe:'two-fifths',realization:'matrix'}).operator.selected.spectrum.inverseNorm,null);

// Independent Pascal rows, then normalized microstate Boltzmann weights.
function counts(N){let row=[1n];for(let n=0;n<N;n++)row=[1n,...Array.from({length:row.length-1},(_,j)=>row[j]+row[j+1]),1n];return row;}
for(const mode of ['coins','particles'])for(const N of [1,2,3,4,8,16,32])for(const x of [0,.25,1,2,10,20])for(const selected of ['zero','middle','all']){
 const scene=build('ensemble-state-graph',{mode,N,x,selected}),m=scene.ensemble,weights=counts(N),gap=mode==='coins'?0:x;
 const pUpper=1/(1+Math.exp(gap)),pLower=1-pUpper,logZ=Math.log1p(Math.exp(-gap));
 const selectedJ=selected==='zero'?0:selected==='all'?N:Math.floor(N/2);
 assert.equal(m.selected,selectedJ);near(m.x,gap,'Canonical dimensionless gap');
 const spheres=scene.primitives.filter(p=>p.ensemble_kind==='macrostate'),stems=scene.primitives.filter(p=>p.ensemble_kind==='surprisal_stem');assert.equal(spheres.length,N+1);assert.equal(stems.length,N+1);
 let sumP=0,countEntropy=0,meanMultiplicity=0;
 for(let j=0;j<=N;j++){
  const logOmega=Math.log(Number(weights[j])),logP=logOmega-j*gap-N*logZ,P=Math.exp(logP),expected=[j/N,logOmega/N,-logP/N];sumP+=P;countEntropy-=P*logP;meanMultiplicity+=P*logOmega;
  const sphere=spheres.find(p=>p.j===j),stem=stems.find(p=>p.j===j);point(sphere.points[0],expected,'Macrostate physical coordinates');
  assert.equal(sphere.omega,weights[j].toString());near(sphere.radius,j===selectedJ?.045:.025,'Selected display highlight');
  near(sphere.logOmega,logOmega,'Multiplicity metadata');near(sphere.macroLogP,logP,'Log probability metadata');
  point(stem.points[0],[j/N,logOmega/N,0],'Surprisal guide origin');point(stem.points[1],expected,'Surprisal guide endpoint');point(m.plotted[j].point,expected,'Macrostate coordinate metadata');
  near(expected[1]+expected[2],j/N*gap+logZ,'Multiplicity plus surprisal');assert.ok(sphere.points[0][2]>0,'Every finite probability has finite positive surprisal');
 }
 near(sumP,1,'Normalized macrostate law');
 const fullEntropy=-N*(pUpper*Math.log(pUpper)+pLower*Math.log(pLower));
 near(m.microGibbsOverK,fullEntropy,'Full microstate Gibbs entropy');near(m.macroGibbsOverK,countEntropy,'Count-distribution entropy');near(fullEntropy,countEntropy+meanMultiplicity,'Conditional entropy decomposition');
 ensembleStates++;
}
const fair=build('ensemble-state-graph',{mode:'coins'});
for(const x of [0,1,20])assert.deepEqual(build('ensemble-state-graph',{mode:'coins',x}).primitives,fair.primitives,'A canonical gap does not assign fair coins an energy');
console.log(`Verified ${operatorStates} independent rational operator spatial states and ${ensembleStates} independent Pascal/Boltzmann spatial states; hidden tails, semantic controls, full spectra, nonnormal resolvent exclusions and entropy coordinates passed.`);

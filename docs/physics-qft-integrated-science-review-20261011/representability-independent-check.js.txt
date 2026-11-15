'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const q=require(path.resolve('web/physics-qft-lab.js')),oldq=require('./representability-exact-prior-core.js');
assert.deepEqual(q.controls,oldq.controls);assert.deepEqual(q.choices,oldq.choices);assert.deepEqual(q.initial,oldq.initial);assert.deepEqual(q.constants,oldq.constants);
const adapter=fs.readFileSync('web/spatial-qft.js','utf8'),oldAdapter=fs.readFileSync('docs/physics-qft-integrated-reader-review-20261011/pre-ratio-gain-spatial-qft.js','utf8');
const ctx=vm.createContext({window:{PrimerPhysicsQftLab:oldq}});vm.runInContext(oldAdapter,ctx);const prior=ctx.window.PrimerQftSpatialFamily;
global.window={PrimerPhysicsQftLab:q};require(path.resolve('web/spatial-qft.js'));require(path.resolve('web/spatial-models.js'));require(path.resolve('web/spatial-module-objects.js'));
const family=window.PrimerQftSpatialFamily,binding=JSON.parse(fs.readFileSync('data/module-models.json')).models.find(m=>m.node_id==='phys.5.qft');assert(window.PrimerModuleObjects.ensure({props:{scenario:'module.phys.5.qft',family:binding.family,mode:binding.mode,context:binding.context,lesson:'Quantum Field Theory'}}));
const build=s=>window.PrimerSpatial.build('module.phys.5.qft',s);
function record(){return {colors:{ink:'ink',teal:'teal',blue:'blue',gold:'gold',coral:'coral'},p:[],line(points,color,meta){this.p.push({kind:'line',points,color,meta})},sphere(point,radius,color,meta){this.p.push({kind:'sphere',points:[point],radius,color,meta})},polygon(points,color,meta){this.p.push({kind:'polygon',points,color,meta})},label(point,text){this.p.push({kind:'label',points:[point],text})}}}
const ordinary=[];
for(const [mode] of q.stations)for(const patch of [{},{momentumMeV:.713,angleDeg:37,chargeUnits:-2,normalMode:4,parallelK:3.33,coefficient:-1.1,phaseDeg:82,correctionKind:'amplitude',mediatorMeV:37},{momentumMeV:8.888,angleDeg:179,normalMode:6,gapUm:5,parallelK:10,chargeUnits:2,alpha:.07},{momentumMeV:0,chargeUnits:0,alpha:0,fieldTesla:0,loopCoefficient:0,matchedValue:0,mediatorMeV:0,coefficient:0}]){
 const state={mode,...patch},a=record(),b=record();prior.build(state,a);family.build(state,b);assert.equal(JSON.stringify(a.p),JSON.stringify(b.p),'ordinary actual-emission parity '+mode);ordinary.push({state,primitives:b.p.length});
 if(mode!=='mediator')assert.equal(JSON.stringify(q.build(state)),JSON.stringify(oldq.build(state)),'unchanged non-mediator values');
}
const cases=[];for(const c of q.controls)for(const mode of c.modes)for(const value of [0,Number.MIN_VALUE,5e-322,1e-306,1e-162,1e-20]){
 const state={mode,[c.key]:value};if(c.key==='phaseDeg')state.correctionKind='amplitude';cases.push({sourceControl:c.key,state});
}
for(const momentumMeV of [Number.MIN_VALUE,5e-322,1e-320,1e-308,1e-200,0])for(const angleDeg of [0,90,180])cases.push({sourceControl:'coupled momentum/angle',state:{mode:'scattering',momentumMeV,angleDeg}});
cases.push({sourceControl:'all zero complex-span',state:{mode:'perturbation',correctionKind:'amplitude',alpha:0,coefficient:0}},{sourceControl:'subnormal matched observable',state:{mode:'renormalization',matchedValue:Number.MIN_VALUE,loopCoefficient:0}},{sourceControl:'subnormal rate',state:{mode:'perturbation',correctionKind:'rate',coefficient:Number.MIN_VALUE}},{sourceControl:'maximal preserved mesh',state:{mode:'casimir',gapUm:5,parallelK:10,normalMode:6}});
const tiny=[],ratio=[];let emittedPoints=0,ratioAxes=0,maxCasimirFaces=0;
for(const entry of cases){
 const scene=build(entry.state);assert.deepEqual(scene.state,oldq.normalize(entry.state),'accepted controls unchanged');
 for(const primitive of scene.primitives)for(const point of primitive.points){assert(point.every(Number.isFinite),'actual engine primitive remains finite');emittedPoints++;}
 assert(!/Infinity|NaN/.test(scene.readout));assert(!scene.qft.current.massless||scene.state.mediatorMeV===0);
 if(scene.state.mode==='scattering'){
  const d=scene.qft.current,p=scene.state.momentumMeV,a=scene.state.angleDeg,m=q.build(scene.state);
  for(const [channel,deg,zero,underflow,classification,logValue,value] of [['t',a,d.zeroTransfer,d.tUnderflow,d.transferClassification,d.log10AbsT,d.t],['u',180-a,d.uZeroTransfer,d.uUnderflow,d.uTransferClassification,d.log10AbsU,d.u]]){
   const expectedZero=p===0||deg===0;assert.equal(zero,expectedZero);assert.equal(classification,expectedZero?'zero transfer':'spacelike');
   if(!expectedZero&&value===0){assert(underflow);assert(Number.isFinite(logValue));assert(m.ledger.find(r=>r[0]===channel+' channel q²')[1].includes('Float64 underflow'));}
   if(!expectedZero&&deg<1e-150){const expected=2*(Math.log10(p)+Math.log10(deg)+Math.log10(Math.PI/180));assert(Math.abs(logValue-expected)<1.1e-12,'tiny accepted-value transfer log');}
  }
 }
 const charts=scene.qft.charts;
 for(const chart of charts){
  const corePanel=q.build(entry.state).panels[chart.index];
  if(corePanel.equalScale){assert.equal(chart.xGainLog10,chart.yGainLog10);assert.equal(JSON.stringify(chart.xMap),JSON.stringify(chart.yMap));}
  for(const axis of ['x','y']){
   assert(Number.isFinite(chart[axis+'GainLog10']));const map=chart[axis+'Map'];assert(map.mode==='affine'||map.mode==='ratio');
   if(map.mode==='affine'){assert(Number.isFinite(chart[axis+'Gain'])&&chart[axis+'Gain']>0)}else{assert(chart[axis+'Gain']===null);assert(Number.isFinite(map.divisor)&&map.divisor>0);assert(Number.isFinite(map.displayGain)&&map.displayGain>0);ratioAxes++;assert(scene.readout.includes('Ratio-normalized'))}
  }
  for(const graph of chart.graphs){
   const emitted=scene.primitives.filter(p=>p.panel===chart.index&&p.key===graph.key&&['qft_curve','qft_singleton_curve','qft_discrete_occupation'].includes(p.fidelity_kind));
   assert(emitted.length>0,'metadata curve actually emits geometry');
   const actual=graph.discrete?emitted.flatMap(p=>p.points):emitted[0].points;
   assert.equal(JSON.stringify(actual),JSON.stringify(graph.points),'actual primitive point emission equals chart source mapping');
  }
  if(chart.xMap.mode==='ratio'||chart.yMap.mode==='ratio')ratio.push({case:entry,chart,readout:scene.readout});
 }
 for(const row of q.build(entry.state).ledger)for(const v of row)assert(typeof v!=='number'||Number.isFinite(v),'finite or qualified scientific ledger');
 if(scene.state.mode==='casimir'){const meta=scene.qft.extra.find(v=>v.kind==='standing-factor'),faces=scene.primitives.filter(p=>p.fidelity_kind==='qft_standing_factor');assert.equal(meta.errorBudget,.02);assert(meta.interpolationErrorBound<=.02);assert.equal(faces.length,2*meta.nx*meta.nz);maxCasimirFaces=Math.max(maxCasimirFaces,faces.length);if(entry.sourceControl==='maximal preserved mesh')assert.equal(faces.length,47500);}
 tiny.push({sourceControl:entry.sourceControl,state:scene.state,primitiveCount:scene.primitives.length,ratioCharts:charts.filter(c=>c.xMap.mode==='ratio'||c.yMap.mode==='ratio').length});
}
const mediator=[];for(const mass of [0,Number.MIN_VALUE,5e-322,1e-320,1e-308,1e-306,1e-305,1e-200,1e-20,1e-15,1,197,500])for(const radiusFm of [.01,1,10]){
 const m=q.build({mode:'mediator',mediatorMeV:mass,radiusFm}),d=m.current;assert.equal(d.massless,mass===0);
 if(mass===0){assert(d.rangeFm===null&&d.log10RangeFm===null);assert(m.readout.includes('massless'));assert(!d.suppressionUnresolved)}else{
  assert(Number.isFinite(d.log10RangeFm)&&Number.isFinite(d.log10InverseRange));assert(Math.abs(d.log10RangeFm+d.log10InverseRange)<1e-13);
  if(d.rangeOverflow){assert(d.rangeFm===null);assert(m.readout.includes('positive finite'));assert(!m.readout.includes('an infinite'));assert(m.ledger[0][1].includes('positive'));}
  else assert(d.rangeFm>0&&Number.isFinite(d.rangeFm));
  if(d.suppressionUnresolved){assert(m.readout.includes('remains massive'));assert(m.ledger[3][1].includes('Float64 precision'));}
 }
 mediator.push({mass,radiusFm,current:d,readout:m.readout,ledger:m.ledger});
}
const zeroScenes=[{mode:'scattering',momentumMeV:0},{mode:'perturbation',coefficient:0,alpha:0,correctionKind:'amplitude'}].map(state=>{const scene=build(state);return {state,charts:scene.qft.charts.map(c=>({origin:c.origin,xmin:c.xmin,xmax:c.xmax,ymin:c.ymin,ymax:c.ymax,xMap:c.xMap,yMap:c.yMap,xGainLog10:c.xGainLog10,yGainLog10:c.yGainLog10}))}});
const result={status:'pass',ordinary,nearZeroCases:tiny,ratioCharts:ratio,zeroScenes,mediator,summary:{ordinaryEmissionParityStates:ordinary.length,acceptedControlCases:tiny.length,actualEmittedPoints:emittedPoints,ratioAxes,maxCasimirFaces,mediatorOracleCases:mediator.length},pins:Object.fromEntries(['web/physics-qft-lab.js','web/spatial-qft.js','web/spatial-models.js','web/spatial-module-objects.js','tools/check_physics_qft_representability.js'].map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')]))};
fs.mkdirSync('.research/qft-representability-audit-20261011',{recursive:true});
fs.writeFileSync('.research/qft-representability-audit-20261011/independent-representability-result.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result.summary,null,2));

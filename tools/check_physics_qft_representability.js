#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),q=require('../web/physics-qft-lab.js');
global.window={PrimerPhysicsQftLab:q};const current=require('../web/spatial-qft.js');require('../web/spatial-models.js');require('../web/spatial-module-objects.js');const b=JSON.parse(fs.readFileSync('data/module-models.json','utf8')).models.find(v=>v.node_id==='phys.5.qft');window.PrimerModuleObjects.ensure({props:{scenario:'module.phys.5.qft',family:b.family,context:b.context,mode:b.mode,lesson:'QFT'}});const prior=require('../docs/physics-qft-integrated-reader-review-20261011/pre-ratio-gain-spatial-qft.js');
const recorder=()=>({colors:{ink:'ink',teal:'teal',blue:'blue',gold:'gold',coral:'coral'},primitives:[],line(points,color,data){this.primitives.push({kind:'line',points,color,data});},sphere(point,radius,color,data){this.primitives.push({kind:'sphere',point,radius,color,data});},polygon(points,color,data){this.primitives.push({kind:'polygon',points,color,data});},label(point,text){this.primitives.push({kind:'label',point,text});}});
let ordinaryStates=0,tinyStates=0,ratioAxes=0,emittedPoints=0;
for(const [mode] of q.stations)for(const patch of [{},{momentumMeV:10,angleDeg:180,chargeUnits:3,normalMode:6,parallelK:10},{momentumMeV:0,angleDeg:0,chargeUnits:0,alpha:0,mediatorMeV:0,fieldTesla:0}]){
 const state={mode,...patch},a=recorder(),c=recorder();const old=prior.build(state,a),now=current.build(state,c);
 assert.deepEqual(c.primitives,a.primitives,'Every ordinary finite-gain emitted glyph/facet stays exact');
 for(let i=0;i<now.qft.charts.length;i++){assert.equal(now.qft.charts[i].xGain,old.qft.charts[i].xGain);assert.equal(now.qft.charts[i].yGain,old.qft.charts[i].yGain);}ordinaryStates++;
}
const cases=[...q.controls.filter(c=>c.min<=0&&c.max>0).flatMap(c=>c.modes.map(mode=>({mode,[c.key]:Number.MIN_VALUE}))),
 {mode:'scattering',momentumMeV:Number.MIN_VALUE,angleDeg:90},{mode:'scattering',momentumMeV:5e-322,angleDeg:90},
 {mode:'scattering',momentumMeV:Number.MIN_VALUE,angleDeg:0},{mode:'scattering',momentumMeV:Number.MIN_VALUE,angleDeg:180},
 {mode:'scattering',momentumMeV:0,angleDeg:0},{mode:'scattering',momentumMeV:0,angleDeg:180},
 {mode:'scattering',momentumMeV:1e-200,angleDeg:0},{mode:'scattering',momentumMeV:1e-200,angleDeg:180},
 {mode:'antiparticle',chargeUnits:0},{mode:'antiparticle',chargeUnits:5e-322}];
for(const state of cases){const scene=window.PrimerSpatial.build('module.phys.5.qft',state);assert.ok(scene.primitives.every(p=>p.points.every(x=>x.every(Number.isFinite))));assert.ok(!/NaN|Infinity/.test(scene.readout));
 for(const chart of scene.qft.charts){for(const axis of ['x','y']){const m=chart[axis+'Map'],gain=chart[axis+'Gain'];assert.ok(Number.isFinite(chart[axis+'GainLog10']));if(m.mode==='ratio'){ratioAxes++;assert.equal(gain,null);assert.ok(m.divisor>0&&Number.isFinite(m.divisor)&&m.displayGain>0&&Number.isFinite(m.displayGain));assert.ok(scene.readout.includes('Ratio-normalized'));}else assert.ok(Number.isFinite(gain)&&gain>0);}
 if(scene.qft.state.mode==='scattering'&&chart.index===0){assert.deepEqual(chart.xMap,chart.yMap,'Equal-scale momentum charts preserve isotropic normalization');assert.equal(chart.xGainLog10,chart.yGainLog10);}
 for(const graph of chart.graphs)for(let i=0;i<graph.points.length;i++){const point=graph.points[i],source=graph.source[i];for(const [axis,index] of [['x',0],['y',1]]){const m=chart[axis+'Map'],expected=chart.origin[index]+(m.mode==='ratio'?(source[axis]-chart[axis+'min'])/m.divisor*m.displayGain:(source[axis]-chart[axis+'min'])*m.gain);assert.equal(point[index],expected,'Actual emitted graph coordinate follows its stated affine/ratio calibration');}emittedPoints++;}
 }
 const m=q.build(state);assert.ok(!m.ledger.some(row=>row.some(v=>typeof v==='number'&&!Number.isFinite(v))),'No unqualified numerical infinities in accepted-value ledgers');tinyStates++;
}
for(const mass of [0,Number.MIN_VALUE,5e-322,1e-320,1e-200,197,500]){const m=q.build({mode:'mediator',mediatorMeV:mass}),d=m.current;assert.equal(d.massless,mass===0);if(mass===0){assert.equal(d.rangeFm,null);assert.equal(d.log10RangeFm,null);assert.ok(m.readout.includes('massless'));}else{assert.ok(Number.isFinite(d.log10RangeFm)&&Number.isFinite(d.log10InverseRange));if(d.rangeOverflow){assert.equal(d.rangeFm,null);assert.ok(m.readout.includes('positive finite')&&!m.readout.includes('an infinite'));}else assert.ok(d.rangeFm>0&&Number.isFinite(d.rangeFm));}}
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');console.log(JSON.stringify({status:'pass',ordinaryStates,tinyStates,ratioAxes,emittedPoints,core_sha256:sha('web/physics-qft-lab.js'),adapter_sha256:sha('web/spatial-qft.js'),check_sha256:sha(__filename)},null,2));

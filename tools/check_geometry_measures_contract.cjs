'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const core=require('../web/geometry-measures-core.js');
let comparisonCases=0,scalingCases=0,capacityCases=0;
for(let w=1;w<=12;w++)for(let h=1;h<=12;h++){
 for(let a=Math.max(1,w+h-12);a<=Math.min(12,w+h-1);a++){
  const r=core.model({kind:'compare',width:w,height:h,compareWidth:a,unit:'m'});
  assert.equal(r.first.perimeter,r.second.perimeter);assert.equal(r.second.area,a*(w+h-a));assert.equal(r.areaDifference,a*(w+h-a)-w*h);assert.equal(r.first.areaUnit,'m²');assert.equal(r.second.areaUnit,'m²');comparisonCases++;
 }
 for(let factor=1;factor<=3;factor++){
  const r=core.model({kind:'scale',width:w,height:h,factor});assert.equal(r.second.cells.length,w*h*factor**2);assert.equal(r.areaRatio,factor**2);assert.equal(r.second.perimeter,2*(w+h)*factor);scalingCases++;
 }
 for(let depth=1;depth<=12;depth++)for(const unit of ['cm','m']){
  const r=core.model({kind:'cuboid',width:w,height:h,depth,unit});const expected=unit==='cm'?w*h*depth/1000:w*h*depth*1000;assert(Math.abs(r.capacityLitres-expected)<1e-12);capacityCases++;
 }
}
const invalid=[null,[],{kind:'unknown'},{unknown:1},{width:NaN},{width:Infinity},{width:1.5},{width:'6'},{width:0},{height:13},{unit:'ft'},{factor:4},{kind:'triangle',width:2,apex:3},{kind:'cutout',width:2,cutWidth:2},{kind:'compare',width:1,height:1,compareWidth:3}];
for(const state of invalid)assert.throws(()=>core.model(state));
const m=core.model();assert(Object.isFrozen(m)&&Object.isFrozen(m.polygon)&&Object.isFrozen(m.polygon[0]));assert.throws(()=>{m.polygon[0][0]=99;});
const root=path.resolve(__dirname,'..'),out=path.join(root,'.research/geometry-fidelity-20261029');fs.mkdirSync(out,{recursive:true});const proof={allPassed:true,comparisonCases,scalingCases,capacityCases,invalidStatesRejected:invalid.length,immutableModels:true,coreSHA256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'web/geometry-measures-core.js'))).digest('hex'),lessonIntegrated:false};fs.writeFileSync(path.join(out,'contract-proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));

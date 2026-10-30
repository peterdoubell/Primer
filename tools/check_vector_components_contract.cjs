const assert=require('node:assert/strict'),fs=require('fs'),core=require('../web/vector-components-core.js');const good={a:[2,3,0],b:[4,-1,0]};let rejected=0;
for(const raw of [null,[],{}, {...good,extra:1},{...good,a:new Array(3)},{...good,a:[1,2]},{...good,a:[1,2,NaN]},{...good,a:[1,2,Infinity]},{...good,a:[1,2,'3']},{...good,a:[33,0,0]},{...good,a:[1.5,0,0]},{...good,alpha:null},{...good,alpha:9},{...good,beta:.5},{...good,dimension:null},{...good,dimension:4},{...good,a:[1,2,3],dimension:2}]){assert.throws(()=>core.model(raw));rejected++;}
let axes=0;for(let i=0;i<3;i++)for(let j=0;j<3;j++)for(const sign of [-1,1]){const a=[0,0,0],b=[0,0,0];a[i]=32;b[j]=32*sign;const r=core.model({a,b});assert.equal(r.dot,i===j?1024*sign:0);assert.equal(r.cross2,i===j?0:1048576);axes++;}

const m=core.model(good);assert(Object.isFrozen(m)&&Object.isFrozen(m.state.a)&&Object.isFrozen(m.projectionOnB));for(const example of core.presets())for(const [key,value]of Object.entries(example.expected))assert.deepEqual(core.model(example.state)[key],value);

fs.writeFileSync(require('path').resolve(__dirname,'../.research/vector-fidelity-20261029/invalid-proof.json'),JSON.stringify({allPassed:true,rejected,axisBoundaryCases:axes,integrated:false},null,2));console.log({rejected,axes});

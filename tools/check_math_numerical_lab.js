#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),lab=require('../web/math-numerical-lab.js');
const near=(a,b,t=2e-12)=>assert.ok(Math.abs(a-b)<=t*Math.max(Math.abs(a),Math.abs(b),1e-300),`${a} != ${b}`);
const same=(a,b)=>assert.equal(a.n*b.d,b.n*a.d);let states=0;
for(const precision of [32,64])for(let count=1;count<=1000;count++){
 const m=lab.build({mode:'sum',precision,count});same(lab.add(m.dataError,m.naiveRound),lab.sub(lab.fromFloat(m.naive),m.target));same(lab.add(m.dataError,m.compRound),lab.sub(lab.fromFloat(m.compensated),m.target));assert.equal(m.points.length,count);assert.ok(m.dataError.n>0n);states++;
}
assert.equal(lab.build({mode:'sum',count:10}).naive,.9999999999999999);assert.equal(lab.build({mode:'sum',count:10}).compensated,1);
for(const precision of [32,64])for(let k=1;k<=16;k++){
 const m=lab.quadratic(k,precision),{low,high}=m.certificate,B=m.Bint;
 assert.ok(low.n>0n&&low.n*low.n-B*low.n*low.d+low.d*low.d>0n);assert.ok(high.n*high.n-B*high.n*high.d+high.d*high.d<0n);
 for(const e of [m.naiveError,m.stableError])assert.ok(e.absoluteLow.n>0n&&e.absoluteHigh.n>0n&&e.relativeLow>0&&e.relativeLow<=e.relativeHigh*(1+1e-14));states++;
}
assert.equal(lab.quadratic(8,64).naive,0);assert.ok(lab.quadratic(2,64).naiveError.relativeHigh<1e-11);assert.ok(lab.quadratic(2,64).naiveError.relativeLow>1e-14);
for(let q=0;q<=16;q++)for(let p=2;p<=16;p++)for(const sign of [-1,1]){
 const m=lab.conditioning({conditionPower:q,perturbPower:p,sign});near(m.kappa,10**q);near(m.forwardRelative,10**(q-p)/Math.SQRT2);near(m.inputRelative,10**(-p)/Math.sqrt(1+10**(-2*q)));assert.ok(m.forwardRelative<=m.bound*(1+1e-14));assert.ok(m.eta>0);same(lab.mul(m.change,m.etaExact),m.deltaExact);states++;
}
for(const precision of [32,64])for(let iterations=0;iterations<=12;iterations++){
 const m=lab.build({mode:'root',precision,iterations}),p=m.at;
 near(p.radius,2**(-iterations-1));const a=lab.fromFloat(p.a),b=lab.fromFloat(p.b);assert.ok(a.n*a.n<=2n*a.d*a.d&&b.n*b.n>=2n*b.d*b.d);assert.ok(p.error.absolute>0);if(iterations===2){assert.equal(m.tests[1],1.25);assert.equal(p.midpoint,1.375);}states++;
}
for(const precision of [32,64])for(let intervals=1;intervals<=64;intervals++){
 const m=lab.build({mode:'trapezoid',precision,intervals});same(lab.add(m.truncation,m.rounding),m.total);same(m.theoretical,lab.rat(8n*BigInt(intervals)**2n+4n,3n*BigInt(intervals)**2n));if(intervals===2)assert.equal(m.value,3);states++;
}
for(let slope=-20;slope<=20;slope++)for(const startError of [-10,0,10])for(let iterations=0;iterations<=12;iterations++){
 const m=lab.build({mode:'fixed',slope,startError,iterations});same(m.at.error,lab.rat(BigInt(startError)*BigInt(slope)**BigInt(iterations),100n*10n**BigInt(iterations)));if(startError===0||(slope===0&&iterations>0))assert.equal(m.at.error.n,0n);states++;
}
class E{
 constructor(tag){this.tagName=tag;this.nodeType=1;this.attributes={};this.children=[];this.listeners={};this.value='';this.disabled=false;this.hidden=false;this.classList={toggle:(k,on)=>{const s=new Set((this.attributes.class||'').split(' '));on?s.add(k):s.delete(k);this.attributes.class=[...s].join(' ');}};}
 setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k];}append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}addEventListener(k,f){this.listeners[k]=f;}
 get textContent(){return this.children.map(x=>x.textContent).join('');}set textContent(v){this.children=[{nodeType:3,textContent:String(v)}];}
}
global.document={createElement:t=>new E(t),createElementNS:(_ns,t)=>new E(t),createTextNode:v=>({nodeType:3,textContent:String(v)})};
const root=lab.render({props:{scenario:'math.5.numerical.error-accounting'}}),all=e=>[e,...(e.children||[]).flatMap(x=>x.nodeType===1?all(x):[])],find=(k,v)=>all(root).find(e=>e.attributes?.[k]===v);let mounted=0;
function check(){const m=lab.build(JSON.parse(root.getAttribute('data-numerical-state')));assert.ok(root.textContent.includes(m.readout));for(const c of lab.controls)assert.equal(find('data-numerical-control',c.key).disabled,!c.uses.includes(m.state.mode));assert.equal(find('data-numerical-precision','').disabled,['conditioning','fixed'].includes(m.state.mode));
 for(const p of all(root).filter(e=>e.attributes?.['data-numerical-error'])){const value=Number(p.getAttribute('data-value')),low=Number(p.getAttribute('data-log-low')),high=Number(p.getAttribute('data-log-high'));assert.ok(value!==0);near(Number(p.getAttribute('cx')),76+330*(Math.log10(Math.abs(value))-low)/(high-low));}
 if(m.state.mode==='trapezoid'){const polygons=all(root).filter(e=>e.attributes?.['data-numerical-trapezoid']);assert.equal(polygons.length,m.state.intervals);for(const p of polygons){const i=+p.getAttribute('data-numerical-trapezoid'),coords=p.getAttribute('points').split(' ').map(x=>x.split(',').map(Number));for(const [j,[x,y]] of coords.entries()){const realX=2*(i+(j>=2?1:0))/m.state.intervals,realY=j===1||j===2?realX**2:0;near(x,76+330*realX/2);near(y,270-202*realY/4.4);}}}
 if(m.state.mode==='conditioning'){const path=find('data-numerical-series','conditioned-circle');assert.ok(path);assert.ok(+path.getAttribute('data-eta')>0);}
 mounted++;}
for(const [mode] of lab.modes){const select=find('data-numerical-mode','');select.value=mode;select.listeners.change();check();
 for(const precision of [32,64]){const input=find('data-numerical-precision','');if(!input.disabled){input.value=precision;input.listeners.change();check();}}
 for(const c of lab.controls.filter(c=>c.uses.includes(mode)))for(const value of [c.min,c.max]){const input=find('data-numerical-control',c.key);input.value=value;input.listeners.input();input.listeners.change();check();}
}
find('data-numerical-action','reset').listeners.click();assert.deepEqual(JSON.parse(root.getAttribute('data-numerical-state')),lab.initial);find('data-numerical-action','enlarge').listeners.click();assert.equal(find('data-numerical-action','enlarge').getAttribute('aria-pressed'),'true');assert.equal(lab.render({props:{scenario:'wrong'}}),null);
global.window={PrimerMathNumericalLab:lab};require('../web/spatial-models.js');require('../web/spatial-module-objects.js');const item={props:{scenario:'module.math.5.numerical',family:'numerical-conditioning',mode:'model',context:'Exact linear scaling.',lesson:'Numerical Analysis'}};assert.ok(window.PrimerModuleObjects.ensure(item));let spatial=0;
for(let exponent=0;exponent<=16;exponent++)for(const perturbPower of [2,16])for(const sign of [-1,1]){
 const scene=window.PrimerSpatial.build(item.props.scenario,{conditionPower:exponent,perturbPower,sign}),input=scene.primitives.filter(p=>p.conditioning_kind==='input'),output=scene.primitives.filter(p=>p.conditioning_kind==='output');assert.equal(input.length,6);assert.equal(output.length,6);const eta=10**(-exponent);for(let i=0;i<6;i++)for(let j=0;j<input[i].points.length;j++){const a=input[i].points[j],b=output[i].points[j];near(b[0]-1.5,a[0]+1.5);near(b[1],eta*a[1]);near(b[2],a[2]);assert.ok(Math.abs(b[1])>0);}
 near(scene.conditioning.eta,eta);near(scene.conditioning.kappa,10**exponent);spatial++;
}
console.log(`Verified ${states} numerical states, ${mounted} mounted error/coordinate states and ${spatial} unthickened 3D matrix maps.`);

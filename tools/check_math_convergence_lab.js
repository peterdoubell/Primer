#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),lab=require('../web/math-convergence-lab.js');
const near=(a,b,tolerance=1e-12)=>assert.ok(Math.abs(a-b)<=tolerance*Math.max(Math.abs(a),Math.abs(b),1e-300),`${a} != ${b}`);
for(let n=0;n<=1000;n++)assert.equal(lab.isqrt(BigInt(n)),BigInt(Math.floor(Math.sqrt(n))));
for(let n=1;n<=160;n++){
 const q=lab.decimalRoot(n);assert.ok(q.numerator*q.numerator<2n*q.denominator*q.denominator);
 assert.ok((q.numerator+1n)**2n>2n*q.denominator*q.denominator);
 assert.ok(q.error>0&&Number.isFinite(q.error));assert.equal(q.decimal.split('.')[1].length,n);
 if(n<160){const next=lab.decimalRoot(n+1);assert.ok(next.numerator*q.denominator>=q.numerator*next.denominator);assert.ok(next.error<=q.error*(1+1e-14));}
 const huge=10n**BigInt(n);assert.equal(lab.isqrt(huge*huge),huge);assert.equal(lab.isqrt(huge*huge-1n),huge-1n);
}
let tails=0,functions=0;
for(const f of ['reciprocal','below','above','geometric','alternating-decay','oscillating','rational-root'])for(let N=1;N<=120;N++)for(let e=1;e<=200;e++){
 const actual=lab.sequenceTail(f,N,e),eps=e/100;
 if(f==='oscillating')assert.equal(actual,eps>1);
 else if(f==='geometric'){
  const delta=-N*Math.LN2-Math.log(eps);
  if(Math.abs(delta)>1e-12)assert.equal(actual,delta<0);
 }else if(f!=='rational-root')assert.equal(actual,N>100/e);
 if(actual)for(const n of [N,Math.min(160,N+1),160])assert.ok(lab.sequencePoint(f,n).error<eps*(1+1e-13));
 tails++;
}
assert.equal(lab.sequenceTail('reciprocal',100,1),false);assert.equal(lab.sequenceTail('reciprocal',101,1),true);
assert.equal(lab.sequenceTail('geometric',2,25),false);assert.equal(lab.sequenceTail('geometric',3,25),true);
assert.equal(lab.sequenceTail('oscillating',120,100),false);assert.equal(lab.sequenceTail('oscillating',120,101),true);
assert.equal(lab.functionTail('powers',1,100),true);assert.equal(lab.functionTail('powers',120,99),false);
assert.equal(lab.functionTail('uniform-ramp',100,1),false);assert.equal(lab.functionTail('uniform-ramp',101,1),true);
for(const f of ['uniform-ramp','powers'])for(let N=1;N<=120;N++)for(const e of [1,25,50,99,100,101,200]){
 const m=lab.build({family:f,index:N,epsilon:e,sample:99});
 for(const x of [0,.01,.5,.99,1]){const q=lab.functionPoint(f,N,x);const value=f==='powers'?Math.exp(N*Math.log(x)):x/N;
  near(q.value,value);assert.equal(q.limit,f==='powers'&&x===1?1:0);near(q.error,Math.abs(value-q.limit));functions++;}
 if(f==='powers'&&e<100){assert.ok(m.witness<1&&m.witness>0);assert.ok(Math.exp(N*Math.log(m.witness))>e/100);near(Math.exp(N*Math.log(m.witness)),(1+e/100)/2);}
 assert.equal(m.works,f==='powers'?e>=100:N>100/e);
 assert.ok(m.points.some(p=>p.x===1));assert.ok(m.points.some(p=>p.x>.9999&&p.x<1));
}
class E{
 constructor(tag){this.tagName=tag;this.nodeType=1;this.attributes={};this.children=[];this.listeners={};this.value='';this.disabled=false;this.hidden=false;
  this.classList={toggle:(key,on)=>{const s=new Set((this.attributes.class||'').split(' '));on?s.add(key):s.delete(key);this.attributes.class=[...s].join(' ');}};}
 setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k];}
 append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}addEventListener(k,fn){this.listeners[k]=fn;}
 get textContent(){return this.children.map(x=>x.textContent).join('');}set textContent(v){this.children=[{nodeType:3,textContent:String(v)}];}
}
global.document={createElement:t=>new E(t),createElementNS:(_ns,t)=>new E(t),createTextNode:v=>({nodeType:3,textContent:String(v)})};
const root=lab.render({props:{scenario:'math.4.analysis.convergence'}});assert.ok(root);assert.equal(lab.render({props:{scenario:'other'}}),null);
const all=e=>[e,...(e.children||[]).flatMap(x=>x.nodeType===1?all(x):[])];const find=(k,v)=>all(root).find(e=>e.attributes?.[k]===v);
let mounted=0;
function geometry(){const m=lab.build(JSON.parse(root.getAttribute('data-convergence-state')));
 if(!m.functions){const terms=all(root).filter(e=>e.attributes?.['data-convergence-term']);assert.equal(terms.length,160);
  for(const q of terms){const n=Number(q.getAttribute('data-convergence-term'));const value=lab.sequencePoint(m.state.family,n).value;
   near(Number(q.getAttribute('cx')),72+338*(n-1)/159);near(Number(q.getAttribute('cy')),275-211*(value+2.1)/5.7);}
  for(const point of all(root).filter(e=>e.attributes?.['data-convergence-error']))assert.ok(Number(point.getAttribute('data-error'))>0);
 }else{const end=find('data-convergence-supremum',String(m.sup));assert.ok(end);assert.equal(end.getAttribute('data-attained'),String(m.state.family!=='powers'));
  assert.equal(find('data-convergence-witness',String(m.witness))!==undefined,m.witness!==null);}
 assert.equal(find('data-convergence-control','sample').disabled,!m.functions);mounted++;
}
for(const family of lab.families){const select=find('data-convergence-family','');select.value=family.value;select.listeners.change();geometry();
 for(const c of lab.controls){const input=find('data-convergence-control',c.key);if(input.disabled)continue;for(const v of [c.min,c.max]){input.value=v;input.listeners.input();input.listeners.change();geometry();}}
}
find('data-convergence-action','reset').listeners.click();assert.deepEqual(JSON.parse(root.getAttribute('data-convergence-state')),lab.initial);
find('data-convergence-action','enlarge').listeners.click();assert.equal(find('data-convergence-action','enlarge').getAttribute('aria-pressed'),'true');
global.window={PrimerMathConvergenceLab:lab};require('../web/spatial-models.js');require('../web/spatial-module-objects.js');
const item={props:{scenario:'module.math.4.analysis',family:'analysis-tail-errors',mode:'model',context:'Exact errors.',lesson:'Real Analysis'}};
assert.ok(window.PrimerModuleObjects.ensure(item));let spatial=0;
for(const family of ['powers','uniform-ramp'])for(const index of [1,20,120])for(const epsilon of [1,100,200]){
 const scene=window.PrimerSpatial.build(item.props.scenario,{family,index,epsilon});const lines=scene.primitives.filter(p=>p.convergence_kind==='data');assert.equal(lines.length,8);
 for(const line of lines)for(const [x,error,z] of line.points){near(error,family==='powers'?Math.exp(line.index*Math.log(x)):x/line.index);near(z,.2*(line.index-index));assert.ok(x>=0&&x<=1);}
 const ends=scene.primitives.filter(p=>p.convergence_kind==='endpoint');assert.equal(ends.length,8);
 ends.forEach(p=>near(p.points[0][1],family==='powers'?0:1/p.index));
 assert.equal(scene.primitives.filter(p=>p.convergence_kind==='unattained').length,family==='powers'?8:0);spatial++;
}
console.log(`Verified ${tails} exact tail decisions, ${functions} independent function values, ${mounted} mounted states and ${spatial} 3D error families; strict boundaries, endpoint exceptions, witnesses, rational brackets and geometry passed.`);

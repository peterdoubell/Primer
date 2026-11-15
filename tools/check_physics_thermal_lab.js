#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),lab=require('../web/physics-thermal-lab.js');
const near=(a,b,t=3e-11)=>assert.ok(Math.abs(a-b)<=t*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);
let states=0;
for(const left of [-20,20,80,120])for(const right of [-20,20,80,120])for(const area of [10,100,200])for(const length of [.5,5,20]) {
 for(const k of [.02,1,200]){
  const m=lab.build({mode:'conduction',left,right,area,length,conductivity:k});
  near(m.power,-k*(area/10000)*(right-left)/(length/100));near(m.flux,m.power/(area/10000));
  for(const p of m.points)near(p.t,left+(right-left)*p.x/(length/100));states++;
 }
 for(const e of [0,5,80,100]){
  const m=lab.build({mode:'radiation',left,right,area,emissivity:e});
  // Independent gross powers, using exact SI-defining constants for sigma.
  const sigma=2*Math.PI**5*(1.380649e-23)**4/(15*(6.62607015e-34)**3*(299792458)**2);
  near(m.emitted,e/100*sigma*area/10000*(left+273.15)**4,2e-10);
  near(m.absorbed,e/100*sigma*area/10000*(right+273.15)**4,2e-10);
  near(m.power,m.emitted-m.absorbed);if(left===right||e===0)assert.equal(m.power,0);states++;
 }
}
// Independently integrate the spatial fluid balance with RK4.
for(const left of [5,20,80,95])for(const right of [5,20,80,95])for(const length of [.5,5,20])for(const flow of [1,10,50])for(const h of [10,100,500]){
 const m=lab.build({mode:'stream',left,right,length,flow,coefficient:h}),steps=1000,dx=length/100/steps;
 const derivative=T=>h*.04*(left-T)/(flow*.001*4180);let T=right;
 for(let i=0;i<steps;i++){const k1=derivative(T),k2=derivative(T+dx*k1/2),k3=derivative(T+dx*k2/2),k4=derivative(T+dx*k3);T+=dx*(k1+2*k2+2*k3+k4)/6;}
 near(m.outlet,T);near(m.power,flow*.001*4180*(T-right));
 assert.ok(m.points.every(p=>p.t>=Math.min(left,right)-1e-12&&p.t<=Math.max(left,right)+1e-12));states++;
}
for(const left of [-20,20,80,120])for(const right of [-20,20,80,120])for(const a of [100,1000,5000])for(const b of [100,1000,5000])for(const G of [0,.5,5,20])for(const time of [0,10,600]){
 const m=lab.build({mode:'contact',left,right,capacityA:a,capacityB:b,conductance:G,time});
 near(a*m.a+b*m.b,a*left+b*right);near(a*(left-m.a),m.energy);near(b*(m.b-right),m.energy);
 near(m.power,G*(m.a-m.b));near(m.equilibrium,(a*left+b*right)/(a+b));
 const prev=lab.contactAt(m.state,Math.max(0,time-.001)),next=lab.contactAt(m.state,time+.001);
 if(time>0){near((next.a-prev.a)/.002,-m.power/a,1e-6);near((next.b-prev.b)/.002,m.power/b,1e-6);}
 for(const p of m.points) {near(a*p.a+b*p.b,a*left+b*right);assert.ok(p.a>=Math.min(left,right)-1e-12&&p.a<=Math.max(left,right)+1e-12);}
 if(G===0){assert.equal(m.a,left);assert.equal(m.b,right);assert.equal(m.energy,0);}states++;
}
// Known asymmetric pair: capacity ratio fixes equilibrium, not arithmetic average.
near(lab.build({mode:'contact',left:80,right:20,capacityA:1000,capacityB:4000}).equilibrium,32);
const slow=lab.build({mode:'stream',flow:1}),fast=lab.build({mode:'stream',flow:50});assert.ok(fast.outlet<slow.outlet&&fast.power>slow.power);
for(const c of lab.controls)for(const invalid of [NaN,Infinity,-Infinity,'no'])assert.equal(lab.normalize({[c.key]:invalid})[c.key],lab.initial[c.key]);
class E {
 constructor(tag){this.tagName=tag;this.nodeType=1;this.attributes={};this.children=[];this.listeners={};this.value='';this.disabled=false;this.hidden=false;this.classList={toggle:(k,on)=>{const s=new Set((this.attributes.class||'').split(' '));on?s.add(k):s.delete(k);this.attributes.class=[...s].join(' ');}};}
 setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k];}
 append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}addEventListener(k,fn){this.listeners[k]=fn;}
 get firstChild(){return this.children[0];}get textContent(){return this.children.map(x=>x.textContent).join('');}set textContent(v){this.children=[{nodeType:3,textContent:String(v)}];}
}
global.document={createElement:t=>new E(t),createElementNS:(_ns,t)=>new E(t),createTextNode:v=>({nodeType:3,textContent:String(v)})};
const all=e=>[e,...(e.children||[]).flatMap(x=>x.nodeType===1?all(x):[])];let mounted=0;
for(const scenario of ['phys.0.hot-cold.energy-balance','phys.2.heat.transport']){
 const root=lab.render({props:{scenario}}),find=(k,v)=>all(root).find(e=>e.attributes?.[k]===v);assert.ok(root);
 const check=()=>{const m=lab.build(JSON.parse(root.getAttribute('data-thermal-state')));
  for(const b of all(root).filter(e=>e.attributes?.['data-thermal-balance'])){const value=Number(b.getAttribute('data-value')),scale=Number(b.getAttribute('data-scale'));near(Number(b.getAttribute('width')),170*Math.abs(value)/scale);near(Number(b.getAttribute('x')),230+170*Math.min(0,value)/scale);}
  if(m.points){for(const path of all(root).filter(e=>e.attributes?.['data-thermal-series'])){const key=path.getAttribute('data-thermal-series'),coords=path.getAttribute('d').match(/[ML][^ML]+/g);assert.equal(coords.length,m.points.length);coords.forEach((v,i)=>{const [x,y]=v.slice(1).split(' ').map(Number),p=m.points[i];near(x,72+338*(m.state.mode==='contact'?p.x/600:p.x*100/20));near(y,275-211*((p[key]??p.t)+20)/140);});}}
  for(const c of lab.controls){const input=find('data-thermal-control',c.key);assert.equal(input.disabled,!c.modes.includes(m.state.mode));}mounted++;
 };
 const modes=scenario.includes('hot-cold')?['contact']:lab.modes.map(m=>m[0]);
 for(const mode of modes){if(mode!=='contact'){const select=find('data-thermal-mode','');select.value=mode;select.listeners.change();}check();
  for(const c of lab.controls.filter(c=>c.modes.includes(mode)))for(const value of [c.min,c.max]){const input=find('data-thermal-control',c.key);input.value=value;input.listeners.input();input.listeners.change();check();}
 }
 for(const p of all(root).filter(e=>e.attributes?.['data-thermal-preset'])){p.listeners.click();check();}
 find('data-thermal-action','reset').listeners.click();assert.deepEqual(JSON.parse(root.getAttribute('data-thermal-state')),{...lab.initial,mode:scenario.includes('hot-cold')?'contact':'conduction'});
 find('data-thermal-action','enlarge').listeners.click();assert.equal(find('data-thermal-action','enlarge').getAttribute('aria-pressed'),'true');
}
assert.equal(lab.render({props:{scenario:'wrong'}}),null);
global.window={PrimerPhysicsThermalLab:lab};require('../web/spatial-models.js');require('../web/spatial-module-objects.js');
const item={props:{scenario:'module.phys.2.heat',family:'thermal-slab',mode:'model',context:'Fourier flux.',lesson:'Heat'}};assert.ok(window.PrimerModuleObjects.ensure(item));let spatial=0;
for(const length of [.5,5,20])for(const area of [10,100,200])for(const left of [-20,50,120])for(const right of [-20,50,120]){
 const scene=window.PrimerSpatial.build(item.props.scenario,{length,area,left,right});const solids=scene.primitives.filter(p=>p.thermal_kind==='slab');assert.equal(solids.length,16*6);
 const pts=solids.flatMap(p=>p.points);const extent=axis=>Math.max(...pts.map(p=>p[axis]))-Math.min(...pts.map(p=>p[axis]));near(extent(0),length*.1);near(extent(1),Math.sqrt(area)*.1);near(extent(2),Math.sqrt(area)*.1);
 for(const p of solids)near(p.temperature,left+(right-left)*(p.slice+.5)/16);
 near(scene.thermal.area,area/10000);near(scene.thermal.power,area/10000*(left-right)/(length/100));spatial++;
}
console.log(`Verified ${states} thermal balances, ${mounted} mounted physical-coordinate states and ${spatial} dimensioned 3D slabs.`);

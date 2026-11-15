#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
globalThis.window = {};
require('../web/math-wave-lab.js');
const lab = window.PrimerMathWaveLab;
const near = (a,b,tol=1e-9) => assert.ok(Math.abs(a-b)<=tol*Math.max(1,Math.abs(b)),`${a} versus ${b}`);
function simpson(fn,length,cells=4000) {
  const dx=length/cells;let sum=fn(0)+fn(length);
  for(let i=1;i<cells;i++)sum+=(i%2?4:2)*fn(i*dx);
  return sum*dx/3;
}
let states=0;
for(const mode of ['modes','pulse'])for(const length of [1,2,5])for(const speed of [.5,1,3])
 for(const [amplitude,second,velocity] of [[1,.3,0],[-.8,-.5,.7],[0,0,1],[0,0,0]]) {
  const s={mode,length,speed,amplitude,second,velocity,diffusivity:.2};const initial=lab.quantities(s,0);
  for(const t of [0,.125,.62*length/speed,.9*length/speed,2*length/speed,8]) {
   const q=lab.quantities(s,t);near(q.wave,initial.wave,1e-12);
   const numerical=simpson(x=>{const p=lab.point(s,x,t);return .5*(p.ut**2+speed**2*p.ux**2);},length);
   near(q.wave,numerical,2e-8);
   for(const x of [0,.11*length,.3*length,.53*length,.88*length,length]) {
    const p=lab.point(s,x,t);near(p.utt,speed**2*p.uxx,1e-12);
    if(mode==='modes'){near(p.heatT,s.diffusivity*p.heatXX,1e-12);assert.ok(q.heat<=initial.heat+1e-12);}
    else assert.equal(p.heat,null);
    if(x===0||x===length){assert.equal(p.u,0);assert.equal(p.ut,0);if(mode==='modes')assert.equal(p.heat,0);}
    if(x>0&&x<length&&t>.0001&&t<23.99) {
      const h=1e-5*length,dt=1e-5*length/speed;
      near((lab.point(s,x+h,t).u-lab.point(s,x-h,t).u)/(2*h),p.ux,3e-6);
      near((lab.point(s,x,t+dt).u-lab.point(s,x,t-dt).u)/(2*dt),p.ut,3e-6);
    }
    states++;
   }
  }
 }

// Solve the PDE independently on a uniform grid by central differences.
// The renderer uses neither this stencil nor these initial-data expressions.
function referenceWave(s,t,n=512) {
 const dx=s.length/n,dtTarget=.25*dx/s.speed,steps=Math.max(1,Math.ceil(t/dtTarget)),dt=t/steps;
 const r=s.speed*dt/dx;let previous=[],velocity=[];
 for(let i=0;i<=n;i++) {
  const x=i*dx,z=(x-.3*s.length)/(.08*s.length);
  if(s.mode==='pulse') {
   previous[i]=Math.abs(z)<1?s.amplitude*(1-z*z)**3:0;
   velocity[i]=Math.abs(z)<1?6*s.speed*s.amplitude*z*(1-z*z)**2/(.08*s.length):0;
  } else {previous[i]=s.amplitude*Math.sin(Math.PI*x/s.length)+s.second*Math.sin(2*Math.PI*x/s.length);velocity[i]=s.velocity*Math.sin(Math.PI*x/s.length);}
 }
 previous[0]=previous[n]=0;let current=previous.slice();
 for(let i=1;i<n;i++)current[i]=previous[i]+dt*velocity[i]+.5*r*r*(previous[i-1]-2*previous[i]+previous[i+1]);
 for(let step=1;step<steps;step++) {
  const next=Array(n+1).fill(0);
  for(let i=1;i<n;i++)next[i]=2*current[i]-previous[i]+r*r*(current[i-1]-2*current[i]+current[i+1]);
  previous=current;current=next;
 }
 return current;
}
let solverChecks=0;
for(const mode of ['modes','pulse'])for(const phase of [.15,.7,1.2,2]) {
 const s={...lab.initial,mode,amplitude:.8,second:-.3,velocity:.4};const t=phase*s.length/s.speed;
 const reference=referenceWave(s,t);
 const errors=reference.map((u,i)=>Math.abs(u-lab.point(s,i*s.length/512,t).u));
 assert.ok(Math.max(...errors)<(mode==='pulse'?.012:.001),`${mode} PDE stencil discrepancy ${Math.max(...errors)}`);solverChecks++;
}
// A short explicit heat evolution with the same Dirichlet boundaries.
for(const diffusivity of [.05,.2,1]) {
 const s={...lab.initial,diffusivity},n=160,dx=s.length/n,t=.05*s.length*s.length/diffusivity;
 const steps=Math.ceil(t/(.4*dx*dx/diffusivity)),dt=t/steps,r=diffusivity*dt/(dx*dx);
 let u=Array.from({length:n+1},(_,i)=>s.amplitude*Math.sin(Math.PI*i/n)+s.second*Math.sin(2*Math.PI*i/n));u[0]=u[n]=0;
 for(let step=0;step<steps;step++){
  const next=Array(n+1).fill(0);for(let i=1;i<n;i++)next[i]=u[i]+r*(u[i-1]-2*u[i]+u[i+1]);u=next;
 }
 u.forEach((value,i)=>near(value,lab.point(s,i*dx,t).heat,.0001));solverChecks++;
}
// Before any reflection, the compact profile is translated rightward. After
// complete reflection it is sign-inverted and moves left, with no leakage.
const pulse={...lab.initial,mode:'pulse'};
near(lab.point(pulse,.5*pulse.length,.2*pulse.length/pulse.speed).u,1);
near(lab.point(pulse,.5*pulse.length,1.2*pulse.length/pulse.speed).u,-1);
assert.equal(lab.point(pulse,.8*pulse.length,0).u,0);
assert.equal(lab.point(pulse,.7*pulse.length,.2*pulse.length/pulse.speed).u,0);
for(const x of [.23,.3,.35].map(v=>v*pulse.length))near(lab.point(pulse,x,0).ut,-pulse.speed*lab.point(pulse,x,0).ux);
for(const bad of [-1,25,NaN,Infinity])assert.throws(()=>lab.point({},.5,bad),RangeError);

const {FakeDocument,descendants}=require('./check_remaining_models.js');
globalThis.document=new FakeDocument();
const root=lab.render({renderer:'math-wave-lab',props:{scenario:'math.5.pde.wave-field'}});
assert.equal(lab.render({props:{scenario:'math.5.pde'}}),null);
const all=()=>descendants(root,()=>true),byAttr=(k,v)=>all().find(e=>e.getAttribute(k)===v);
const input=k=>byAttr('data-wave-control',k),button=k=>byAttr('data-wave-action',k);
const readout=()=>all().find(e=>e.getAttribute('class')==='math-wave-readout').textContent;
const original=readout();let mounted=0;
function fire(e,name){e.dispatch(name);}
for(const c of lab.controls)for(const value of [c.min,(c.min+c.max)/2,c.max]) {
 input(c.key).value=String(value);fire(input(c.key),'input');
 assert.ok(input(c.key).getAttribute('aria-valuetext'));
 for(const e of all())for(const value of e.attributes.values())assert.doesNotMatch(String(value),/NaN|Infinity/);
 assert.doesNotMatch(readout(),/NaN|Infinity/);mounted++;
 fire(button('reset'),'click');assert.equal(readout(),original);
}
fire(byAttr('data-wave-preset','pulse'),'click');
assert.equal(input('second').disabled,true);assert.equal(input('velocity').disabled,true);assert.equal(input('diffusivity').disabled,true);
assert.equal(all().filter(e=>e.getAttribute('data-wave-trace')==='heat').length,0);
fire(button('enlarge'),'click');assert.equal(button('enlarge').getAttribute('aria-pressed'),'true');
fire(button('reset'),'click');assert.equal(readout(),original);
// Inspect actual profile coordinates against an independently stated initial mode.
input('time').value='0';fire(input('time'),'input');
const trace=byAttr('data-wave-trace','wave').getAttribute('points').split(' ').map(p=>p.split(',').map(Number));
const scale=Math.abs(lab.initial.amplitude)+Math.abs(lab.initial.second);
trace.forEach(([x,y],i)=>{const position=lab.initial.length*i/320;
 const expected=i===0||i===320?0:Math.sin(Math.PI*position/lab.initial.length)+.3*Math.sin(2*Math.PI*position/lab.initial.length);
 near(x,78+332*i/320);near(y,156.5-108.5*expected/scale);});
for(const key of ['amplitude','second','velocity']){input(key).value='0';fire(input(key),'input');}
assert.equal(all().filter(e=>e.getAttribute('data-wave-quantity')).length,0);
assert.match(readout(),/Wave E\(0\)=0/);assert.match(readout(),/Heat H\(0\)=0/);
assert.ok(all().some(e=>e.textContent==='Wave E(0)=0: E/E(0) is undefined.'));
assert.ok(all().some(e=>e.textContent==='Heat H(0)=0: H/H(0) is undefined.'));
input('velocity').value='1';fire(input('velocity'),'input');
assert.equal(all().filter(e=>e.getAttribute('data-wave-quantity')==='wave').length,1);
assert.equal(all().filter(e=>e.getAttribute('data-wave-quantity')==='heat').length,0);
console.log(`Verified ${states} field/derivative states, ${solverChecks} independent wave/heat PDE evolutions and ${mounted} mounted controls; energy quadrature, fixed-end reflection, causal support, coordinates and resets passed.`);

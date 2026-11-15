#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),lab=require('../web/physics-constraints-lab.js');
const near=(a,b,t=3e-10,label='quantity')=>assert.ok(Math.abs(a-b)<=t*Math.max(1,Math.abs(a),Math.abs(b)),`${label}: ${a} != ${b}`);
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),minus=(a,b)=>a.map((x,i)=>x-b[i]);
let analytic=0,hoopStates=0,doubleStates=0,mounted=0;const numerical=[];
for(const mode of ['spring','free','fall','incline','central'])for(const mass of [.2,1,3])for(const stiffness of [.5,4,20])for(const v0 of [-4,0,4])for(const time of [0,.7,4]){
 const s=lab.normalize({mode,mass,stiffness,q0:1,v0,time,rate:.8,length:1.3,incline:30,gravity:9.8}),m=lab.build(s),p=m.current;
 const kinetic=.5*mass*p.velocities.reduce((sum,v)=>sum+dot(v,v),0);near(p.T,kinetic);
 if(mode==='central'){
  const [r]=p.positions,[v]=p.velocities;near(p.V,.5*stiffness*dot(r,r));near(p.angularMomentum,mass*(r[0]*v[1]-r[1]*v[0]));near(p.angularMomentum,mass*s.length*s.length*s.rate);assert.deepEqual(m.momentumUnits,['kg·m/s','kg·m²/s']);
 }else{
  near(p.momenta[0],mass*p.rates[0]);if(mode==='spring'){near(p.V,.5*stiffness*p.q[0]**2);near(p.acceleration,-stiffness/mass*p.q[0]);}
  else{const gradient=mode==='free'?0:mode==='fall'?9.8:4.9;near(p.V,mass*gradient*p.q[0]);near(p.acceleration,-gradient);near(p.q[0],1+v0*time-.5*gradient*time*time);near(p.rates[0],v0-gradient*time);}
 }
 near(p.L,p.T-p.V);near(p.Hreduced,p.T+p.V);near(p.Elab,m.start.Elab);assert.ok(m.diagnostics.accepted);analytic++;
}
near(lab.build({mode:'free',mass:.5,v0:4}).Hreduced,4);
near(lab.build({mode:'incline',gravity:9.8,incline:30}).current.acceleration,-4.9);
near(lab.build({mode:'pendulum',length:2.45,gravity:9.8,angle:0,rate:0}).omegaSmall,2);
for(const mass of [.2,1,3])for(const radius of [.5,1,3])for(const gravity of [0,9.8,20])for(const driveOmega of [-4,0,4])for(const theta of [-Math.PI,-.8,0,.8,Math.PI])for(const thetaRate of [-3,0,3])for(const phase of [-2,0,2]){
 const h=lab.hoopSnapshot({mass,radius,gravity,driveOmega,theta,thetaRate,phase}),r=h.position,v=h.velocity,a=h.acceleration;
 near(dot(r,r),radius*radius);near(h.T,.5*mass*dot(v,v));near(h.V,mass*gravity*(r[2]+radius));
 near(h.momentumPhi,mass*(r[0]*v[1]-r[1]*v[0]));near(h.Hreduced,h.momentumTheta*thetaRate-h.L);near(h.Elab-h.Hreduced,driveOmega*h.momentumPhi);
 const reaction=a.map((value,i)=>mass*value+(i===2?mass*gravity:0));reaction.forEach((x,i)=>near(h.reactionForce[i],x));
 near(dot(reaction,h.virtualThetaTangent),0,1e-9,'Ideal allowed virtual work');near(dot(reaction,v),h.drivePower,1e-9,'Actual laboratory constraint power');near(h.drivePower,driveOmega*h.driveTorque);
 if(driveOmega===0){near(h.Elab,h.Hreduced);near(h.drivePower,0);near(h.constraintPower,0,1e-9);}
 // Independent Cartesian Taylor trajectory differentiates the embedding rather
 // than copying the implementation's component acceleration expansion.
 const dt=1e-4,position=t=>{const th=theta+thetaRate*t+.5*h.thetaAcceleration*t*t,ph=phase+driveOmega*t;return [radius*Math.sin(th)*Math.cos(ph),radius*Math.sin(th)*Math.sin(ph),-radius*Math.cos(th)];};
 const before=position(-dt),after=position(dt);for(let i=0;i<3;i++){near((after[i]-before[i])/(2*dt),v[i],2e-6,'Cartesian velocity');near((after[i]-2*r[i]+before[i])/(dt*dt),a[i],2e-5,'Cartesian acceleration');}
 hoopStates++;
}
for(const mass of [.2,1,3])for(const mass2 of [.2,1,3])for(const length of [.5,3])for(const length2 of [.5,3])for(const a of [-1.2,0,1.2])for(const b of [-.9,.9])for(const w of [-3,0,3]){
 const s=lab.normalize({mode:'double',mass,mass2,length,length2,gravity:9.8}),d=lab.doubleSnapshot(s,a,w,b,.7),[r1,r2]=d.positions,[v1,v2]=d.velocities;
 near(dot(r1,r1),length*length);near(dot(minus(r2,r1),minus(r2,r1)),length2*length2);
 near(d.T,.5*mass*dot(v1,v1)+.5*mass2*dot(v2,v2));near(d.V,mass*9.8*(r1[2]+length)+mass2*9.8*(r2[2]+length+length2));near(d.Hreduced,d.T+d.V);near(d.L,d.T-d.V);
 const F1=d.constraintForces[0],F2=d.constraintForces[1],t1=[Math.cos(a),0,Math.sin(a)],t2=[Math.cos(b),0,Math.sin(b)];
 near(dot(F2,t2),0,1e-9,'Second force is along its rod');near(dot(F1.map((x,i)=>x+F2[i]),t1),0,1e-9,'First resultant force is along its rod');
 near(dot(F1,v1)+dot(F2,v2),0,1e-9,'Total fixed-constraint power');near(dot(F2,minus(v2,v1)),0,1e-9,'Internal force-pair power');
 const eps=1e-5,cartT=(x,y)=>{const u=[length*x*Math.cos(a),0,length*x*Math.sin(a)],v=u.map((z,i)=>z+[length2*y*Math.cos(b),0,length2*y*Math.sin(b)][i]);return .5*mass*dot(u,u)+.5*mass2*dot(v,v);};
 near((cartT(w+eps,.7)-cartT(w-eps,.7))/(2*eps),d.momenta[0],2e-7,'Momentum from Cartesian kinetic energy');near((cartT(w,.7+eps)-cartT(w,.7-eps))/(2*eps),d.momenta[1],2e-7);
 assert.equal(d.dof,2);assert.equal(d.cartesianCoordinates-d.independentConstraints,2);doubleStates++;
}
const exchange=lab.doubleSnapshot(lab.normalize({mode:'double'}),.7,1.1,-.4,-.8);assert.ok(Math.abs(exchange.bobConstraintPowers[0])>.01);near(exchange.bobConstraintPowers[0]+exchange.bobConstraintPowers[1],0,1e-10);assert.ok(exchange.momentumRates.some(x=>Math.abs(x)>.01));
for(const mode of ['pendulum','hoop','double']){
 const candidates=[{mode},{mode,angle:0,rate:0,angle2:0,rate2:0},{mode,mass:.2,mass2:3,length:.5,length2:3,gravity:20,angle:150,angle2:-150,rate:3,rate2:-3,driveOmega:4},
  {mode,mass:3,mass2:.2,length:3,length2:.5,gravity:20,angle:-150,angle2:150,rate:-3,rate2:3,driveOmega:-4},{mode,gravity:0,angle:50,angle2:-30,rate:2,rate2:-1,driveOmega:0}];
 for(const control of lab.controls.filter(c=>c.modes.includes(mode)&&c.key!=='time'))for(const value of [control.min,control.max])candidates.push({mode,[control.key]:value});
 for(const raw of candidates){const s=lab.normalize({...raw,time:1.013}),m=lab.build(s);assert.ok(m.diagnostics.accepted,'Bounded refinement criteria '+JSON.stringify(s));assert.ok(m.diagnostics.angleStepDifference<=lab.TOLERANCES.angle);assert.ok(m.diagnostics.rateStepDifference<=lab.TOLERANCES.rate);const energyBudget=1e-8+2e-7*Math.max(1,Math.abs(m.start.Hreduced),Math.abs(m.start.Elab));for(const p of m.points){assert.ok(Math.abs(p.Hreduced-m.start.Hreduced)<=energyBudget,'Reduced energy conservation');assert.ok(Math.abs(p.Elab-m.start.Elab-p.driveWork)<=energyBudget,'Exterior drive work in joules, scaled to the initial energy');}numerical.push(m);}
}
// Full-window joint corners, including the stiff mass/length ratios. These are
// actual 4 s requested endpoints, not a shortened inspection horizon.
for(let i=0;i<64;i++){
 const s=lab.normalize({mode:'double',mass:i&1?.2:3,mass2:i&2?.2:3,length:i&4?.5:3,length2:i&8?.5:3,gravity:20,angle:i&16?150:-150,angle2:i&32?150:-150,rate:i&16?3:-3,rate2:i&32?-3:3,time:4}),m=lab.build(s);
 assert.ok(m.diagnostics.accepted,'Joint corner '+JSON.stringify(s));assert.equal(m.current.t,4);assert.equal(m.points[0].t,0);const energyBudget=1e-8+2e-7*Math.max(1,Math.abs(m.start.Elab));
 for(const p of m.points)assert.ok(Math.abs(p.Elab-m.start.Elab)<=energyBudget,'Joint-corner autonomous conservation');numerical.push(m);
}
for(const mode of lab.modes.map(m=>m[0]))for(const time of [0,4]){const m=lab.build({mode,time,gravity:0,driveOmega:0});assert.equal(m.current.t,time);assert.ok(m.diagnostics.accepted);assert.ok(Number.isFinite(m.Elab));}
// Actual fourth-order timestep convergence, with an independent high-resolution
// endpoint comparison. No invariant projection or analytical state snapping.
for(const mode of ['pendulum','hoop','double']){
 const s=lab.normalize({mode,angle:50,angle2:-30,rate:.7,rate2:-.4}),runs=[.0025,.00125,.000625].map(h=>lab.integrate(s,h,[0,1]).frames.at(-1).y);
 const error=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i])),ratio=error(runs[0],runs[1])/error(runs[1],runs[2]);assert.ok(ratio>14&&ratio<18,mode+' fourth-order step convergence ratio '+ratio);
}
const fixed=lab.build({mode:'hoop',driveOmega:0,time:1.37}),pend=lab.build({mode:'pendulum',time:1.37});fixed.current.q.forEach((q,i)=>near(q,pend.current.q[i]));near(fixed.Elab,pend.Elab);
const small=lab.build({mode:'pendulum',angle:.01,rate:0,length:2.45,gravity:9.8,time:1}),linear=small.state.angle*Math.PI/180*Math.cos(2);near(small.current.q[0],linear,1e-10,'Small-angle limit');
// Independent Simpson quadrature of the energy-integral period, not the AGM.
const s=lab.normalize({mode:'pendulum',angle:120,rate:0}),k=Math.sin(Math.PI/3),steps=20000,dx=(Math.PI/2)/steps;let integral=0;
for(let i=0;i<=steps;i++)integral+=(i===0||i===steps?1:i%2?4:2)/Math.sqrt(1-k*k*Math.sin(i*dx)**2);
near(lab.pendulumPeriod(s),4*Math.sqrt(s.length/s.gravity)*integral*dx/3,1e-11,'Nonlinear energy-integral period');
for(const c of lab.controls)for(const bad of [undefined,null,NaN,Infinity,-Infinity,true,'','invalid'])assert.equal(lab.normalize({[c.key]:bad})[c.key],lab.initial[c.key]);
assert.throws(()=>lab.hoopSnapshot({radius:0}),RangeError);assert.throws(()=>lab.integrate({mode:'pendulum'},1e-323,[1]),RangeError);assert.throws(()=>lab.integrate({mode:'spring'}),RangeError);

class E{constructor(tag){this.tagName=tag;this.nodeType=1;this.attributes={};this.children=[];this.listeners={};this.classList={toggle:(k,on)=>{const c=new Set((this.attributes.class||'').split(' '));on?c.add(k):c.delete(k);this.attributes.class=[...c].join(' ');}};}setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k];}append(...v){this.children.push(...v);}prepend(...v){this.children.unshift(...v);}replaceChildren(...v){this.children=v;}addEventListener(k,f){this.listeners[k]=f;}get textContent(){return this.children.map(c=>c.textContent).join('');}set textContent(v){this.children=[{nodeType:3,textContent:String(v)}];}}
global.document={createElement:t=>new E(t),createElementNS:(_n,t)=>new E(t),createTextNode:t=>({nodeType:3,textContent:String(t)})};
const root=lab.render({props:{scenario:'phys.4.classical.constraints-energy'}}),all=e=>[e,...(e.children||[]).flatMap(c=>c.nodeType===1?all(c):[])],find=(a,v)=>all(root).find(e=>e.attributes?.[a]===v);
function check(){const m=lab.build(JSON.parse(root.getAttribute('data-constraints-state')));for(const c of lab.controls){const range=find('data-constraints-control',c.key);assert.equal(range.disabled,!c.modes.includes(m.state.mode));near(Number(range.value),m.state[c.key]);}
 for(const p of all(root).filter(e=>e.attributes?.['data-constraints-energy'])){const key=p.getAttribute('data-constraints-energy'),min=Number(p.getAttribute('data-min')),max=Number(p.getAttribute('data-max')),coords=p.getAttribute('d').match(/[ML][^ML]+/g).map(v=>v.slice(1).split(' ').map(Number));assert.equal(coords.length,m.points.length);coords.forEach((v,i)=>{near(v[0],70+380*m.points[i].t/4);near(v[1],309-220*(m.points[i][key]-min)/(max-min));});}
 const s=m.state,hoop=s.mode==='hoop',central=s.mode==='central',angular=['hoop','pendulum','double'].includes(s.mode),coords=p=>hoop?[s.length*Math.sin(p.q[0]),p.positions[0][2]]:[p.positions.at(-1)[0],p.positions.at(-1)[central?1:2]],bodyPoints=m.points.flatMap(p=>hoop?[coords(p)]:p.positions.map(r=>[r[0],r[central?1:2]]));
 if(angular)bodyPoints.push([-s.length-(s.mode==='double'?s.length2:0),-s.length-(s.mode==='double'?s.length2:0)],[s.length+(s.mode==='double'?s.length2:0),s.length]);bodyPoints.push([0,0]);
 const lowX=Math.min(...bodyPoints.map(p=>p[0])),highX=Math.max(...bodyPoints.map(p=>p[0])),lowY=Math.min(...bodyPoints.map(p=>p[1])),highY=Math.max(...bodyPoints.map(p=>p[1])),metreScale=260/Math.max(.5,highX-lowX,highY-lowY),X=x=>240+(x-(lowX+highX)/2)*metreScale,Y=y=>204-(y-(lowY+highY)/2)*metreScale;
 const bodies=all(root).filter(e=>e.attributes?.['data-constraints-body']!==undefined),currentPoints=hoop?[coords(m.current)]:m.current.positions.map(r=>[r[0],r[central?1:2]]);assert.equal(bodies.length,currentPoints.length);
 bodies.forEach((e,i)=>{near(Number(e.getAttribute('data-x')),currentPoints[i][0]);near(Number(e.getAttribute('data-y')),currentPoints[i][1]);near(Number(e.getAttribute('cx')),X(currentPoints[i][0]));near(Number(e.getAttribute('cy')),Y(currentPoints[i][1]));near(Number(e.getAttribute('data-metre-scale')),metreScale);});
 for(const c of all(root).filter(e=>e.attributes?.['data-constraints-circle-radius']))near(Number(c.getAttribute('r')),s.length*metreScale);
 const plotted=find('data-constraints-path','position').getAttribute('d').match(/[ML][^ML]+/g).map(v=>v.slice(1).split(' ').map(Number));plotted.forEach((v,i)=>{const p=coords(m.points[i]);near(v[0],X(p[0]));near(v[1],Y(p[1]));});
 mounted++;} 
check();for(const mode of lab.modes.map(m=>m[0])){const select=find('data-constraints-mode','');select.value=mode;select.listeners.change();check();for(const c of lab.controls.filter(c=>c.modes.includes(mode)))for(const v of [c.min,c.max]){const number=find('data-constraints-number',c.key);number.value=v;number.listeners.change();check();}}
for(const preset of all(root).filter(e=>e.attributes?.['data-constraints-preset'])){preset.listeners.click();check();}
find('data-constraints-action','enlarge').listeners.click();find('data-constraints-action','reset').listeners.click();assert.deepEqual(JSON.parse(root.getAttribute('data-constraints-state')),lab.initial);assert.equal(find('data-constraints-action','enlarge').getAttribute('aria-pressed'),'false');
assert.equal(lab.render({props:{scenario:'wrong'}}),null);assert.equal(lab.render({props:{scenario:'phys.4.classical.constraints-energy',extra:true}}),null);
if(process.argv.includes('--json'))console.log(JSON.stringify(numerical));else console.log(`Verified ${analytic} analytic mechanics states, ${hoopStates} Cartesian hoop force/work states, ${doubleStates} Newtonian double-rod states, ${numerical.length} refined trajectories and ${mounted} mounted SI-geometry/energy states.`);

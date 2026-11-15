/* Original SI geometry. Prescribed constraints, laboratory work and reduced energy are separate. */
(function () {
  'use strict';
  const NS='http://www.w3.org/2000/svg',PI=Math.PI,HORIZON=4;
  const modes=Object.freeze([['hoop','Bead on a prescribed rotating hoop'],['spring','Mass on a spring'],
    ['free','Free particle'],['fall','Vertical free fall'],['incline','Fixed frictionless incline'],
    ['pendulum','Nonlinear rigid-rod simple pendulum'],['central','Cyclic angle in a central spring potential'],['double','Two-angle double pendulum']]);
  const initial=Object.freeze({mode:'hoop',mass:1,mass2:1,length:1,length2:1,stiffness:4,gravity:9.8,
    q0:1,v0:0,angle:30,rate:0,angle2:60,rate2:0,driveOmega:4,incline:30,time:1});
  const controls=Object.freeze([
    ['mass','Mass m / first bob mass',.2,3,.1,'kg',modes.map(m=>m[0])],
    ['mass2','Second bob mass',.2,3,.1,'kg',['double']],
    ['length','Length / hoop radius / initial central radius',.5,3,.05,'m',['pendulum','hoop','double','central']],
    ['length2','Second rod length',.5,3,.05,'m',['double']],
    ['stiffness','Spring stiffness',.5,20,.5,'N/m',['spring','central']],
    ['gravity','Gravitational acceleration',0,20,.1,'m/s²',['fall','incline','pendulum','hoop','double']],
    ['q0','Initial displacement / upward position / ramp coordinate',-3,3,.1,'m',['spring','free','fall','incline']],
    ['v0','Initial coordinate / radial velocity',-4,4,.1,'m/s',['spring','free','fall','incline','central']],
    ['angle','Initial angle from downward vertical',-150,150,1,'°',['pendulum','hoop','double']],
    ['rate','Initial angular velocity',-3,3,.1,'rad/s',['pendulum','hoop','double','central']],
    ['angle2','Second initial angle from downward vertical',-150,150,1,'°',['double']],
    ['rate2','Second initial angular velocity',-3,3,.1,'rad/s',['double']],
    ['driveOmega','Prescribed constant hoop rotation Ω',-4,4,.1,'rad/s',['hoop']],
    ['incline','Fixed ramp angle above horizontal',0,90,1,'°',['incline']],
    ['time','Inspect elapsed time; this is not playback',0,HORIZON,.01,'s',modes.map(m=>m[0])]
  ].map(([key,label,min,max,step,unit,applicable])=>Object.freeze({key,label,min,max,step,unit,modes:Object.freeze(applicable)})));
  const TOLERANCES=Object.freeze({angle:2e-6,rate:2e-5,energyAbsolute:1e-8,energyRelative:2e-7,maxRefinements:8});
  const finite=x=>(typeof x==='number'||typeof x==='string'&&x.trim()!=='')&&Number.isFinite(Number(x));
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),rad=x=>x*PI/180,fmt=x=>x==null?'not applicable':Number(x.toPrecision(6)).toString();
  const axisFmt=x=>x!==0&&(Math.abs(x)<.001||Math.abs(x)>=10000)?x.toExponential(2):Number(x.toPrecision(4)).toString();
  const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),add=(a,b)=>a.map((v,i)=>v+b[i]),scale=(a,k)=>a.map(v=>v*k);
  function normalize(raw={}){raw=raw&&typeof raw==='object'?raw:{};const s={mode:modes.some(m=>m[0]===raw.mode)?raw.mode:initial.mode};for(const c of controls)s[c.key]=finite(raw[c.key])?clamp(Number(raw[c.key]),c.min,c.max):initial[c.key];return s;}
  function hoopSnapshot({mass=1,radius=1,gravity=9.8,theta=.5,thetaRate=0,driveOmega=4,phase=0}={}){
    if(![mass,radius,gravity,theta,thetaRate,driveOmega,phase].every(x=>typeof x==='number'&&Number.isFinite(x))||mass<=0||radius<=0||gravity<0)throw new RangeError('Finite SI values, positive mass/radius and nonnegative gravity required');
    const a=Math.sin(theta),b=Math.cos(theta),c=Math.cos(phase),d=Math.sin(phase),R=radius,m=mass,w=thetaRate,O=driveOmega;
    const position=[R*a*c,R*a*d,-R*b],virtualThetaTangent=[R*b*c,R*b*d,R*a],phiTangent=[-R*a*d,R*a*c,0];
    const thetaAcceleration=a*(O*O*b-gravity/R),movingConstraintVelocity=scale(phiTangent,O),velocity=add(scale(virtualThetaTangent,w),movingConstraintVelocity);
    const mixed=[-R*b*d,R*b*c,0],phiSecond=[-R*a*c,-R*a*d,0];
    const acceleration=add(add(scale(virtualThetaTangent,thetaAcceleration),scale(position,-w*w)),add(scale(mixed,2*w*O),scale(phiSecond,O*O)));
    const gravityForce=[0,0,-m*gravity],reactionForce=add(scale(acceleration,m),scale(gravityForce,-1));
    const T=.5*m*R*R*(w*w+O*O*a*a),V=m*gravity*R*(1-b),L=T-V;
    const momentumTheta=m*R*R*w,momentumPhi=m*R*R*O*a*a,driveTorque=2*m*R*R*O*a*b*w,drivePower=O*driveTorque;
    const Hreduced=.5*m*R*R*w*w-.5*m*R*R*O*O*a*a+V,Elab=T+V;
    return {mass:m,radius:R,gravity,theta,thetaRate:w,driveOmega:O,phase,position,velocity,acceleration,gravityForce,reactionForce,
      virtualThetaTangent,phiTangent,movingConstraintVelocity,thetaAcceleration,momentumTheta,momentumPhi,driveTorque,drivePower,
      virtualWorkCoefficient:dot(reactionForce,virtualThetaTangent),constraintPower:dot(reactionForce,velocity),T,V,L,Hreduced,Elab};
  }
  function doubleAcceleration(s,a,w,b,v){
    const A=(s.mass+s.mass2)*s.length*s.length,B=s.mass2*s.length*s.length2,D=s.mass2*s.length2*s.length2,c=Math.cos(a-b),z=Math.sin(a-b);
    const rhs1=-B*z*v*v-(s.mass+s.mass2)*s.gravity*s.length*Math.sin(a),rhs2=B*z*w*w-s.mass2*s.gravity*s.length2*Math.sin(b),det=A*D-B*B*c*c;
    return [(D*rhs1-B*c*rhs2)/det,(A*rhs2-B*c*rhs1)/det];
  }
  function doubleSnapshot(s,a,w,b,v){
    const l=s.length,h=s.length2,m=s.mass,n=s.mass2,g=s.gravity,[aa,bb]=doubleAcceleration(s,a,w,b,v);
    const u=[Math.sin(a),0,-Math.cos(a)],u2=[Math.sin(b),0,-Math.cos(b)],t=[Math.cos(a),0,Math.sin(a)],t2=[Math.cos(b),0,Math.sin(b)];
    const r1=scale(u,l),r2=add(r1,scale(u2,h)),v1=scale(t,l*w),v2=add(v1,scale(t2,h*v));
    const a1=add(scale(t,l*aa),scale(u,-l*w*w)),a2=add(a1,add(scale(t2,h*bb),scale(u2,-h*v*v)));
    const F1=add(scale(a1,m),[0,0,m*g]),F2=add(scale(a2,n),[0,0,n*g]);
    const T=.5*(m+n)*l*l*w*w+.5*n*h*h*v*v+n*l*h*w*v*Math.cos(a-b),V=(m+n)*g*l*(1-Math.cos(a))+n*g*h*(1-Math.cos(b));
    const p1=(m+n)*l*l*w+n*l*h*Math.cos(a-b)*v,p2=n*h*h*v+n*l*h*Math.cos(a-b)*w;
    const coupling=n*l*h*Math.sin(a-b)*w*v,pDot1=-coupling-(m+n)*g*l*Math.sin(a),pDot2=coupling-n*g*h*Math.sin(b);
    return {q:[a,b],rates:[w,v],accelerations:[aa,bb],positions:[r1,r2],velocities:[v1,v2],cartesianAccelerations:[a1,a2],constraintForces:[F1,F2],
      rod1Force:add(F1,F2),rod2ForceOnSecond:F2,rod2PairPower:dot(F2,add(v2,scale(v1,-1))),
      constraintPower:dot(F1,v1)+dot(F2,v2),bobConstraintPowers:[dot(F1,v1),dot(F2,v2)],momenta:[p1,p2],momentumRates:[pDot1,pDot2],
      T,V,L:T-V,Hreduced:T+V,Elab:T+V,dof:2,cartesianCoordinates:4,independentConstraints:2};
  }
  function springAt(s,t){const O=Math.sqrt(s.stiffness/s.mass),q=s.q0*Math.cos(O*t)+s.v0/O*Math.sin(O*t),v=-s.q0*O*Math.sin(O*t)+s.v0*Math.cos(O*t),T=.5*s.mass*v*v,V=.5*s.stiffness*q*q;
    return {t,q:[q],rates:[v],momenta:[s.mass*v],momentumRates:[-s.stiffness*q],T,V,L:T-V,Hreduced:T+V,Elab:T+V,positions:[[q,0,0]],velocities:[[v,0,0]],acceleration:-s.stiffness/s.mass*q,drivePower:0,driveWork:0,constraintPower:0};}
  function linearAt(s,t){const gradient=s.mode==='free'?0:s.mode==='fall'?s.gravity:s.gravity*Math.sin(rad(s.incline)),a=-gradient,q=s.q0+s.v0*t+.5*a*t*t,v=s.v0+a*t,T=.5*s.mass*v*v,V=s.mass*gradient*q;
    const direction=s.mode==='fall'?[0,0,1]:s.mode==='incline'?[Math.cos(rad(s.incline)),0,Math.sin(rad(s.incline))]:[1,0,0];
    return {t,q:[q],rates:[v],momenta:[s.mass*v],momentumRates:[s.mass*a],T,V,L:T-V,Hreduced:T+V,Elab:T+V,positions:[scale(direction,q)],velocities:[scale(direction,v)],acceleration:a,drivePower:0,driveWork:0,constraintPower:0};}
  function centralAt(s,t){const O=Math.sqrt(s.stiffness/s.mass),x=s.length*Math.cos(O*t)+s.v0/O*Math.sin(O*t),y=s.length*s.rate/O*Math.sin(O*t),vx=-s.length*O*Math.sin(O*t)+s.v0*Math.cos(O*t),vy=s.length*s.rate*Math.cos(O*t),r=Math.hypot(x,y);
    const T=.5*s.mass*(vx*vx+vy*vy),V=.5*s.stiffness*r*r,ell=s.mass*(x*vy-y*vx),vr=r===0?null:(x*vx+y*vy)/r;
    return {t,q:[r,r===0?null:Math.atan2(y,x)],rates:[vr,r===0?null:ell/(s.mass*r*r)],momenta:[vr==null?null:s.mass*vr,ell],momentumRates:[null,0],T,V,L:T-V,Hreduced:T+V,Elab:T+V,positions:[[x,y,0]],velocities:[[vx,vy,0]],drivePower:0,driveWork:0,constraintPower:0,angularMomentum:ell,polarChartValid:r!==0};}
  function stateInitial(s){return s.mode==='double'?[rad(s.angle),s.rate,rad(s.angle2),s.rate2]:s.mode==='hoop'?[rad(s.angle),s.rate,0]:[rad(s.angle),s.rate];}
  function derivative(s,t,y){if(s.mode==='double'){const a=doubleAcceleration(s,y[0],y[1],y[2],y[3]);return [y[1],a[0],y[3],a[1]];}
    const z=Math.sin(y[0]),c=Math.cos(y[0]);if(s.mode==='hoop')return [y[1],z*(s.driveOmega*s.driveOmega*c-s.gravity/s.length),2*s.mass*s.length*s.length*s.driveOmega*s.driveOmega*z*c*y[1]];
    return [y[1],-s.gravity/s.length*z];}
  function rk4Step(s,t,y,h){const f=(tt,yy)=>derivative(s,tt,yy),k1=f(t,y),k2=f(t+h/2,y.map((v,i)=>v+h*k1[i]/2)),k3=f(t+h/2,y.map((v,i)=>v+h*k2[i]/2)),k4=f(t+h,y.map((v,i)=>v+h*k3[i]));return y.map((v,i)=>v+h*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6);}
  function energyOf(s,y){if(s.mode==='double'){const a=y[0],w=y[1],b=y[2],v=y[3],T=.5*(s.mass+s.mass2)*s.length*s.length*w*w+.5*s.mass2*s.length2*s.length2*v*v+s.mass2*s.length*s.length2*Math.cos(a-b)*w*v;
      const V=(s.mass+s.mass2)*s.gravity*s.length*(1-Math.cos(a))+s.mass2*s.gravity*s.length2*(1-Math.cos(b));return {H:T+V,E:T+V,work:0};}
    const T=.5*s.mass*s.length*s.length*y[1]*y[1],V=s.mass*s.gravity*s.length*(1-Math.cos(y[0])),spin=s.mode==='hoop'?.5*s.mass*s.length*s.length*s.driveOmega*s.driveOmega*Math.sin(y[0])**2:0;
    return {H:T+V-spin,E:T+V+spin,work:s.mode==='hoop'?y[2]:0};}
  function integrate(raw,maxStep=1/256,times=null){const s=normalize(raw),at=times||Array.from({length:121},(_,i)=>HORIZON*i/120);if(!['pendulum','double','hoop'].includes(s.mode))throw new RangeError('Numerical integration is only defined for nonlinear angular examples');if(!finite(maxStep)||maxStep<=0)throw new RangeError('Positive finite step required');
    if(!at.length||at.some((t,i)=>!finite(t)||t<0||t>HORIZON||i&&t<at[i-1]))throw new RangeError('Sorted times in the bounded 0…4 s window required');
    let t=0,y=stateInitial(s),steps=0,maxInvariantDrift=0,maxDriveBalanceResidual=0;const e0=energyOf(s,y),frames=[];
    for(const target of at){while(t<target){const h=Math.min(maxStep,target-t),next=t+h;if(steps>=300000||next<=t)throw new RangeError('Integration exceeded its bounded step budget or floating-point time resolution');y=rk4Step(s,t,y,h);t=next;steps++;const e=energyOf(s,y);maxInvariantDrift=Math.max(maxInvariantDrift,Math.abs(e.H-e0.H));maxDriveBalanceResidual=Math.max(maxDriveBalanceResidual,Math.abs(e.E-e0.E-e.work));}frames.push({t:target,y:[...y]});}
    return {frames,steps,maxStep,maxInvariantDrift,maxDriveBalanceResidual,initialEnergy:e0};}
  function snapshot(s,t,y){if(s.mode==='spring')return springAt(s,t);if(['free','fall','incline'].includes(s.mode))return linearAt(s,t);if(s.mode==='central')return centralAt(s,t);
    if(s.mode==='double')return {t,...doubleSnapshot(s,y[0],y[1],y[2],y[3]),drivePower:0,driveWork:0};
    if(s.mode==='hoop'){const h=hoopSnapshot({mass:s.mass,radius:s.length,gravity:s.gravity,theta:y[0],thetaRate:y[1],driveOmega:s.driveOmega,phase:s.driveOmega*t});return {t,...h,q:[y[0]],rates:[y[1]],momenta:[h.momentumTheta],momentumRates:[s.mass*s.length*s.length*h.thetaAcceleration],positions:[h.position],velocities:[h.velocity],driveWork:y[2],dof:1,cartesianCoordinates:3,independentConstraints:2};}
    const a=y[0],w=y[1],T=.5*s.mass*s.length*s.length*w*w,V=s.mass*s.gravity*s.length*(1-Math.cos(a));return {t,q:[a],rates:[w],momenta:[s.mass*s.length*s.length*w],momentumRates:[-s.mass*s.gravity*s.length*Math.sin(a)],positions:[[s.length*Math.sin(a),0,-s.length*Math.cos(a)]],velocities:[[s.length*w*Math.cos(a),0,s.length*w*Math.sin(a)]],T,V,L:T-V,Hreduced:T+V,Elab:T+V,drivePower:0,driveWork:0,constraintPower:0,dof:1,cartesianCoordinates:2,independentConstraints:1};}
  const cache=new Map();
  function solve(s){const numerical=['pendulum','double','hoop'].includes(s.mode),times=[...new Set([...Array.from({length:121},(_,i)=>HORIZON*i/120),s.time])].sort((a,b)=>a-b);
    if(!numerical){const points=times.map(t=>snapshot(s,t)),e0=points[0];return {points,diagnostics:{method:'analytic expressions',accepted:true,steps:0,maxInvariantDrift:Math.max(...points.map(p=>Math.abs(p.Hreduced-e0.Hreduced))),maxDriveBalanceResidual:Math.max(...points.map(p=>Math.abs(p.Elab-e0.Elab))),angleStepDifference:0,rateStepDifference:0}};}
    const key=JSON.stringify(s);if(cache.has(key))return cache.get(key);
    let coarse=integrate(s,1/256,times),fine,angleDifference,rateDifference,accepted=false,level=0;
    for(;level<TOLERANCES.maxRefinements;level++){fine=integrate(s,coarse.maxStep/2,times);angleDifference=0;rateDifference=0;
      fine.frames.forEach((f,i)=>{for(const j of s.mode==='double'?[0,2]:[0])angleDifference=Math.max(angleDifference,Math.abs(f.y[j]-coarse.frames[i].y[j]));for(const j of s.mode==='double'?[1,3]:[1])rateDifference=Math.max(rateDifference,Math.abs(f.y[j]-coarse.frames[i].y[j]));});
      const energyTolerance=TOLERANCES.energyAbsolute+TOLERANCES.energyRelative*Math.max(1,Math.abs(fine.initialEnergy.H),Math.abs(fine.initialEnergy.E));
      accepted=angleDifference<=TOLERANCES.angle&&rateDifference<=TOLERANCES.rate&&fine.maxInvariantDrift<=energyTolerance&&fine.maxDriveBalanceResidual<=energyTolerance;if(accepted)break;coarse=fine;}
    const out={points:fine.frames.map(f=>snapshot(s,f.t,f.y)),diagnostics:{method:'RK4 with step-halving comparison',accepted,steps:fine.steps,maxStep:fine.maxStep,coarseStep:fine.maxStep*2,
      refinements:Math.min(level+1,TOLERANCES.maxRefinements),angleStepDifference:angleDifference,rateStepDifference:rateDifference,maxInvariantDrift:fine.maxInvariantDrift,maxDriveBalanceResidual:fine.maxDriveBalanceResidual}};
    if(cache.size>=8)cache.delete(cache.keys().next().value);cache.set(key,out);return out;}
  function ellipticK(k){if(k<0||k>=1)return null;let a=1,b=Math.sqrt(1-k*k);for(let i=0;i<32;i++){const next=(a+b)/2;b=Math.sqrt(a*b);a=next;if(Math.abs(a-b)<4*Number.EPSILON*a)break;}return PI/(2*a);}
  function pendulumPeriod(s){const E=.5*s.mass*s.length*s.length*s.rate*s.rate+s.mass*s.gravity*s.length*(1-Math.cos(rad(s.angle))),limit=2*s.mass*s.gravity*s.length;
    return s.gravity>0&&E<limit?4*Math.sqrt(s.length/s.gravity)*ellipticK(Math.sqrt(E/limit)):null;}
  function build(raw={}){const state=normalize(raw),s=state,sol=solve(s),current=sol.points.find(p=>p.t===s.time),start=sol.points[0],numerical=['pendulum','double','hoop'].includes(s.mode),angular=['pendulum','double','hoop'].includes(s.mode),momentumUnit=angular?'kg·m²/s':s.mode==='central'?'radial kg·m/s; angular kg·m²/s':'kg·m/s';
    const momentumUnits=s.mode==='central'?['kg·m/s','kg·m²/s']:current.momenta.map(()=>momentumUnit),rateUnits=s.mode==='central'?['m/s','rad/s']:current.rates.map(()=>angular?'rad/s':'m/s');
    const deltaLab=current.Elab-start.Elab,deltaReduced=current.Hreduced-start.Hreduced,energyResidual=deltaLab-current.driveWork;
    const omegaSmall=s.gravity>0?Math.sqrt(s.gravity/s.length):0,period=s.mode==='pendulum'?pendulumPeriod(s):null;
    const equation=s.mode==='hoop'?'θ̈ = sinθ(Ω²cosθ − g/R); pθ = mR²θ̇; Hred = ½mR²θ̇² − ½mR²Ω²sin²θ + V; Elab − Hred = Ωpφ.':
      s.mode==='double'?'M(θ) θ̈ = f(θ,θ̇); p = M(θ) θ̇; L = T − V; H = T + V; two angles remain after two length constraints.':
      s.mode==='pendulum'?'θ̈ = −(g/l)sinθ; pθ = ml²θ̇; H = ½ml²θ̇² + mgl(1−cosθ). Small angle: ω₀ = √(g/l).':
      s.mode==='central'?'V = ½k r²; pφ = m r²φ̇ = m(xv_y−yv_x); ∂L/∂φ = 0, so ṗφ = 0.':
      s.mode==='spring'?'q̈ = −(k/m)q; p = mq̇; T = ½mq̇²; V = ½kq²; L = T−V; H = p²/(2m)+V.':
      s.mode==='free'?'q̈ = 0; p = mq̇; V = 0; H = T = p²/(2m).':s.mode==='fall'?'q measured upward: ṗ = ∂L/∂q = −mg; q̈ = −g; H = ½mq̇²+mgq.':'q measured up the fixed ramp: q̈ = −g sinα; H = ½mq̇²+mgq sinα.';
    const dynamics=numerical?`RK4 maximum step ${fmt(sol.diagnostics.maxStep)} s; h/h₂ angle difference ${fmt(sol.diagnostics.angleStepDifference)} rad and rate difference ${fmt(sol.diagnostics.rateStepDifference)} rad/s. Maximum conserved-quantity drift ${fmt(sol.diagnostics.maxInvariantDrift)} J; maximum laboratory energy/work residual ${fmt(sol.diagnostics.maxDriveBalanceResidual)} J. ${sol.diagnostics.accepted?'Refinement criteria met.':'Refinement criteria NOT met; this trajectory is tentative.'}`:'Analytic motion evaluated in floating point; no time-integration method is used.';
    const readout=`At ${fmt(s.time)} s: generalized coordinates ${current.q.map(fmt).join(', ')} ${angular?'rad':s.mode==='central'?'(r in m, φ in rad)':'m'}; rates ${current.rates.map((v,i)=>fmt(v)+' '+rateUnits[i]).join(', ')}. Canonical momenta ${current.momenta.map((v,i)=>fmt(v)+' '+momentumUnits[i]).join(', ')}. T = ${fmt(current.T)} J; V = ${fmt(current.V)} J; L = ${fmt(current.L)} J; reduced H = ${fmt(current.Hreduced)} J; laboratory E = ${fmt(current.Elab)} J. `+
      `ΔE_lab = ${fmt(deltaLab)} J; integrated drive work = ${fmt(current.driveWork)} J; balance residual = ${fmt(energyResidual)} J. `+
      (s.mode==='hoop'?`Laboratory position (x,y,z) = (${current.position.map(fmt).join(', ')}) m; velocity = (${current.velocity.map(fmt).join(', ')}) m/s; reaction force = (${current.reactionForce.map(fmt).join(', ')}) N. pφ = ${fmt(current.momentumPhi)} kg·m²/s; motor power = ${fmt(current.drivePower)} W. Reaction dotted with the allowed θ tangent = ${fmt(current.virtualWorkCoefficient)} J/rad; reaction dotted with laboratory velocity = ${fmt(current.constraintPower)} W. `:'Net ideal constraint power = 0 W. ')+
      (s.mode==='double'?`Canonical momentum rates are ${current.momentumRates.map(fmt).join(', ')} J/rad; they are generally nonzero. Four Cartesian coordinates minus two independent fixed-length constraints leave two degrees of freedom. `:'')+
      (s.mode==='pendulum'?`Small-angle angular frequency = ${fmt(omegaSmall)} rad/s; finite-energy libration period = ${fmt(period)} s (${period==null?'not a librating state':start.Elab===0?'limiting response period; the equilibrium itself does not oscillate':'energy-integral prediction, not a measured curve period'}). `:'')+
      dynamics;
    const note='Point masses and ideal massless rigid rods/wire, without friction, damping, collisions or air drag. The simple pendulum uses a rigid rod that can push or pull; a string might slacken at some of these large-angle/rotation states and is not substituted. Potential references are stated: spring zero at equilibrium; free particle zero everywhere; fall/ramp zero at q=0; angular examples zero with rods hanging down; central potential zero at the origin. Negative gravitational potential is allowed, and the linear examples have no ground or track endpoints. The hoop motor imposes constant Ω during each complete 0–4 s calculation; changing a control selects a new initial-value problem, not an acceleration protocol for that motor. Its ideal reaction has zero allowed virtual work at fixed time, yet the moving constraint can do actual laboratory work. Reduced H is the autonomous first integral; laboratory T+V is different and changes by motor work. For fixed ideal constraints the net constraint power is zero. In a double pendulum, a moving internal rod can exchange energy between bobs while its force pair does zero net work. A closed central orbit is special to the selected isotropic spring potential, not guaranteed for arbitrary central potentials. The polar chart is singular at the origin; Cartesian motion remains defined there. Numeric refinement differences are diagnostics, not rigorous error bounds; no infinite-time accuracy, Lyapunov exponent or proof of chaos is supplied. Display curves connect finite samples, and dot size is a viewing aid.';
    return {state,current,start,points:sol.points,diagnostics:sol.diagnostics,T:current.T,V:current.V,L:current.L,Hreduced:current.Hreduced,Elab:current.Elab,
      deltaLab,deltaReduced,driveWork:current.driveWork,energyResidual,omegaSmall,period,momentumUnit,momentumUnits,rateUnits,equation,readout,note};}
  function el(tag,attrs={},...children){const e=document.createElement(tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));for(const c of children)if(c!=null)e.append(c.nodeType?c:document.createTextNode(String(c)));return e;}
  function sn(tag,attrs={},text){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(text!=null)e.textContent=String(text);return e;}
  let serial=0;
  function render(item,hooks){if(item?.props?.scenario!=='phys.4.classical.constraints-energy'||Object.keys(item.props).length!==1||item.renderer&&item.renderer!=='physics-constraints-lab')return null;
    const uid='constraints-'+ ++serial,root=el('section',{class:'card lesson-model physics-constraints-lab','data-renderer':'physics-constraints-lab','aria-labelledby':uid+'-title'});let model=build(initial),enlarged=false;
    const heading=el('div',{class:'model-heading-row'},el('h3',{id:uid+'-title'},item.title||'Constraints, momentum and real work'));
    const select=el('select',{'data-constraints-mode':'','aria-label':'Mechanics example'});for(const [v,label] of modes)select.append(el('option',{value:v},label));select.addEventListener('change',()=>{model=build({...model.state,mode:select.value,time:0});refresh(true);});
    const widgets=new Map(),inputs=el('div',{class:'model-controls concept-controls'}),buttons=el('div',{class:'model-button-row'});
    for(const c of controls){const id=uid+'-'+c.key,input=el('input',{id,type:'range',min:c.min,max:c.max,step:c.step,'data-constraints-control':c.key}),number=el('input',{id:id+'-number',type:'number',min:c.min,max:c.max,step:'any','data-constraints-number':c.key}),output=el('output',{for:id}),label=el('label',{for:id,class:'model-range-control'},c.label,output,input),numberLabel=el('label',{for:id+'-number',class:'constraints-number-control'},'Enter '+c.label.toLowerCase()+' ('+c.unit+')',number),wrap=el('div',{class:'constraints-widget'},label,numberLabel);
      input.addEventListener('input',()=>{model=build({...model.state,[c.key]:input.value});refresh(false);});input.addEventListener('change',()=>{live.textContent=model.readout;});number.addEventListener('change',()=>{model=build({...model.state,[c.key]:number.value});refresh(true);});inputs.append(wrap);widgets.set(c.key,{input,number,output,wrap,c});}
    const presets=[['driven','Moving hoop: drive does work',{...initial}],['fixed','Same hoop, motor off',{...initial,driveOmega:0}],['spring','Spring: H fixed, L varies',{mode:'spring',mass:1,stiffness:4,q0:1,v0:0,time:PI/4}],['fall','Upward coordinate, downward acceleration',{mode:'fall',mass:1,gravity:9.8,q0:2,v0:0,time:.5}],['incline','Thirty-degree fixed ramp',{mode:'incline',mass:1,gravity:9.8,incline:30,q0:0,v0:0,time:1}],['frequency','Pendulum: ω₀ = 2 rad/s',{mode:'pendulum',mass:1,length:2.45,gravity:9.8,angle:5,rate:0,time:1}],['double','Two angles and coupled momenta',{mode:'double',mass:1,mass2:1,length:1,length2:1,gravity:9.8,angle:45,angle2:80,rate:0,rate2:0,time:1}],['free','Free particle: H = 4 J',{mode:'free',mass:.5,q0:0,v0:4,time:1}]];
    for(const [key,label,patch] of presets){const b=el('button',{type:'button',class:'btn ghost small','data-constraints-preset':key},label);b.addEventListener('click',()=>{model=build({...model.state,...patch});refresh(true);});buttons.append(b);}
    const reset=el('button',{type:'button',class:'btn ghost small','data-constraints-action':'reset'},'Reset activity');reset.addEventListener('click',()=>{model=build(initial);size(false);refresh(true);});buttons.append(reset);
    const enlarge=el('button',{type:'button',class:'btn ghost small','data-constraints-action':'enlarge','aria-pressed':'false'},'Enlarge plots');function size(on){enlarged=on;root.classList.toggle('is-enlarged',on);enlarge.setAttribute('aria-pressed',String(on));enlarge.textContent=on?'Fit plots':'Enlarge plots';}enlarge.addEventListener('click',()=>size(!enlarged));heading.append(enlarge);
    const panels=el('div',{class:'constraints-panels'}),views=[];for(let i=0;i<2;i++){const svg=sn('svg',{viewBox:'0 0 480 390',role:'img'});views.push(svg);panels.append(el('div',{class:'constraints-viewport',tabindex:0,role:'region','aria-label':i?'Energy and drive work; enlarge and scroll':'Physical geometry; enlarge and scroll'},svg));}
    const summary=el('p',{class:'constraints-summary'}),readout=el('p',{class:'constraints-readout'}),equation=el('p',{class:'constraints-equation'}),note=el('p',{class:'spatial-note'}),diagnostics=el('p',{class:'constraints-diagnostics'}),ledger=el('table',{class:'constraints-ledger'}),ledgerWrap=el('div',{class:'constraints-ledger-region',tabindex:0,role:'region','aria-label':'Canonical momentum and energy ledger; scroll horizontally'},ledger),live=el('p',{class:'constraints-live',role:'status','aria-live':'polite','aria-atomic':'true'});
    root.append(heading,el('p',{class:'model-instructions'},item.instructions||'Choose a constrained system. Inspect time, generalized momentum, and the energy/work ledgers.'),select,buttons,inputs,summary,panels,ledgerWrap,equation,readout,diagnostics,el('details',{class:'constraints-assumptions'},el('summary',{},'Model assumptions and numerical limits'),note),el('p',{class:'constraints-sources'},el('a',{href:'https://davidtong.org/teaching/classical-dynamics/dynhtml/S2#S2.SS5.SSS1',target:'_blank',rel:'noopener noreferrer'},'Tong: constraints and rotating hoop'),' · ',el('a',{href:'https://openstax.org/books/university-physics-volume-1/pages/15-4-pendulums',target:'_blank',rel:'noopener noreferrer'},'OpenStax: pendulum and small-angle limit'),'. Original diagrams; no source figure copied.'),live);
    if(hooks?.speakButton)heading.prepend(hooks.speakButton(()=>model.readout+' '+model.equation+' '+model.note,'Read this mechanics activity aloud'));
    function text(svg,x,y,t,attrs={}){svg.append(sn('text',{x,y,fill:'#263b46','font-size':12,...attrs},t));}function line(svg,a,b,color,attrs={}){svg.append(sn('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:color,'stroke-width':2,...attrs}));}
    function setup(index,title){const svg=views[index];svg.replaceChildren(sn('title',{id:uid+'-svg-title-'+index},title),sn('desc',{id:uid+'-svg-desc-'+index},model.readout),sn('rect',{width:480,height:390,rx:10,fill:'#f5efdf'}));svg.setAttribute('aria-labelledby',uid+'-svg-title-'+index);svg.setAttribute('aria-describedby',uid+'-svg-desc-'+index);text(svg,18,26,title,{'font-size':16,'font-weight':600});return svg;}
    function geometry(svg){const m=model,s=m.state,central=s.mode==='central',hoop=s.mode==='hoop',angular=['pendulum','double','hoop'].includes(s.mode);const coords=p=>hoop?[s.length*Math.sin(p.q[0]),p.positions[0][2]]:[p.positions.at(-1)[0],p.positions.at(-1)[central?1:2]];
      const path=m.points.map(coords),all=m.points.flatMap(p=>hoop?[coords(p)]:p.positions.map(r=>[r[0],r[central?1:2]]));if(angular)all.push([-s.length-(s.mode==='double'?s.length2:0),-s.length-(s.mode==='double'?s.length2:0)],[s.length+(s.mode==='double'?s.length2:0),s.length]);all.push([0,0]);
      const loX=Math.min(...all.map(p=>p[0])),hiX=Math.max(...all.map(p=>p[0])),loY=Math.min(...all.map(p=>p[1])),hiY=Math.max(...all.map(p=>p[1]));const scale=260/Math.max(.5,hiX-loX,hiY-loY),cx=(loX+hiX)/2,cy=(loY+hiY)/2,X=x=>240+(x-cx)*scale,Y=y=>204-(y-cy)*scale;
      text(svg,18,49,hoop?'Meridional view in the rotating hoop plane':'Cartesian geometry; positions in metres');text(svg,18,69,hoop?'Azimuth φ = Ωt; laboratory 3D vectors in the ledger.':'One common metre scale on both displayed axes.');
      line(svg,[X(loX),Y(0)],[X(hiX),Y(0)],'#d5cfbf',{'stroke-width':1});line(svg,[X(0),Y(loY)],[X(0),Y(hiY)],'#d5cfbf',{'stroke-width':1});
      if(['hoop','pendulum'].includes(s.mode))svg.append(sn('circle',{cx:X(0),cy:Y(0),r:s.length*scale,fill:'none',stroke:'#c8c1b1','stroke-width':1.5,'data-constraints-circle-radius':s.length}));
      svg.append(sn('path',{d:path.map((p,i)=>(i?'L':'M')+X(p[0])+' '+Y(p[1])).join(' '),fill:'none',stroke:'#317e78','stroke-width':1.5,'data-constraints-path':'position'}));
      const positions=hoop?[coords(m.current)]:m.current.positions.map(r=>[r[0],r[central?1:2]]);let previous=[0,0];positions.forEach((p,i)=>{if(angular&&s.mode!=='hoop')line(svg,[X(previous[0]),Y(previous[1])],[X(p[0]),Y(p[1])],'#263b46');svg.append(sn('circle',{cx:X(p[0]),cy:Y(p[1]),r:5,fill:i?'#b98a2f':'#b96652','data-constraints-body':i,'data-x':p[0],'data-y':p[1],'data-metre-scale':scale}));previous=p;});
      text(svg,18,359,angular?(s.mode==='double'?'Four planar coordinates − two length constraints = 2 DOF.':'Two planar coordinates − one radius constraint = 1 DOF.'):central?'Two planar coordinates; φ is cyclic for this central force.':'One dynamical coordinate; a fixed track supplies no net work.');
      text(svg,18,380,'Path covers 0–4 s; dot is current time. Axes refit; dot size is visual.');}
    function energy(svg){const m=model,values=m.points.flatMap(p=>[p.T,p.V,p.L,p.Hreduced,p.Elab,p.driveWork]),lo=Math.min(0,...values),hi=Math.max(1,...values),pad=(hi-lo)*.07,min=lo-pad,max=hi+pad,X=t=>70+380*t/HORIZON,Y=e=>309-220*(e-min)/(max-min);
      text(svg,18,49,'Energy / drive work (J), common signed scale');for(let i=0;i<=4;i++){const t=i,e=min+(max-min)*i/4;line(svg,[X(t),89],[X(t),309],'#d5cfbf',{'stroke-width':1});text(svg,X(t),330,fmt(t),{'text-anchor':'middle'});line(svg,[70,Y(e)],[450,Y(e)],'#d5cfbf',{'stroke-width':1});text(svg,62,Y(e)+4,axisFmt(e),{'text-anchor':'end','font-size':10});}
      for(const [key,color] of [['T','#3e7085'],['V','#317e78'],['L','#876888'],['Hreduced','#b98a2f'],...(m.state.mode==='hoop'?[['Elab','#263b46'],['driveWork','#b96652']]:[])])svg.append(sn('path',{d:m.points.map((p,i)=>(i?'L':'M')+X(p.t)+' '+Y(p[key])).join(' '),fill:'none',stroke:color,'stroke-width':key==='Hreduced'?3:1.5,'data-constraints-energy':key,'data-min':min,'data-max':max}));
      line(svg,[X(m.state.time),89],[X(m.state.time),309],'#8b7e66',{'stroke-dasharray':'3 3'});text(svg,240,359,'Blue T · teal V · purple L · gold reduced H',{'text-anchor':'middle'});text(svg,240,380,m.state.mode==='hoop'?'Black laboratory E · coral motor work':'For these fixed examples, laboratory E = H.',{'text-anchor':'middle'});}
    function refresh(announce){const m=model,s=m.state;root.setAttribute('data-constraints-state',JSON.stringify(s));select.value=s.mode;for(const w of widgets.values()){const active=w.c.modes.includes(s.mode);w.wrap.hidden=!active;w.input.disabled=w.number.disabled=!active;w.input.value=w.number.value=s[w.c.key];w.output.textContent=fmt(s[w.c.key])+' '+w.c.unit;w.input.setAttribute('aria-valuetext',w.output.textContent);}
      summary.textContent=s.mode==='hoop'?'Moving ideal constraint: zero allowed virtual work does not imply zero laboratory power. Reduced H is conserved; laboratory E changes by drive work.':s.mode==='double'?'Two independent angles; the coupled conjugate momenta generally change while the total mechanical energy stays constant.':'Fixed autonomous example: H = T + V; L = T − V generally varies. Parameter edits recalculate an initial-value problem.';
      geometry(setup(0,'Constraint geometry and current position'));energy(setup(1,'Momentum is not energy; compare the energy ledger'));
      const rows=[['T',m.T,'J'],['V',m.V,'J'],['L = T − V',m.L,'J'],['Reduced H',m.Hreduced,'J'],['Laboratory E',m.Elab,'J'],['Motor work since start',m.driveWork,'J'],['ΔE − motor work',m.energyResidual,'J'],...m.current.momenta.map((p,i)=>['Conjugate p'+(i+1),p,m.momentumUnits[i]])];
      if(s.mode==='hoop')rows.push(['Azimuthal momentum pφ',m.current.momentumPhi,'kg·m²/s'],['Motor torque',m.current.driveTorque,'N·m'],['Motor power',m.current.drivePower,'W'],['Reaction·allowed θ tangent',m.current.virtualWorkCoefficient,'J/rad'],['Reaction·laboratory velocity',m.current.constraintPower,'W'],...['x','y','z'].flatMap((axis,i)=>[['Lab position '+axis,m.current.position[i],'m'],['Lab velocity '+axis,m.current.velocity[i],'m/s'],['Reaction '+axis,m.current.reactionForce[i],'N']]));
      ledger.replaceChildren(el('caption',{},'Current quantities retain their own units'),el('thead',{},el('tr',{},el('th',{scope:'col'},'Quantity'),el('th',{scope:'col'},'Value'),el('th',{scope:'col'},'Unit'))),el('tbody',{},...rows.map(([label,value,unit])=>el('tr',{'data-constraints-ledger':label},el('th',{scope:'row'},label),el('td',{},fmt(value)),el('td',{},unit)))));
      equation.textContent=m.equation;readout.textContent=m.readout;note.textContent=m.note;diagnostics.textContent=m.diagnostics.accepted?'Bounded-window numerical/analytic checks are shown in the readout.':'Numerical refinement criteria were not met; do not treat this curve as a converged trajectory.';diagnostics.classList.toggle('is-unresolved',!m.diagnostics.accepted);if(announce)live.textContent=m.readout;}
    refresh(false);return root;}
  const api=Object.freeze({initial,controls,modes,TOLERANCES,HORIZON,normalize,hoopSnapshot,doubleAcceleration,doubleSnapshot,springAt,linearAt,centralAt,stateInitial,derivative,rk4Step,energyOf,integrate,snapshot,solve,ellipticK,pendulumPeriod,build,render});
  if(typeof window!=='undefined')window.PrimerPhysicsConstraintsLab=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})();

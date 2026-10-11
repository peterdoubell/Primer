'use strict';
// Independent re-audit: exercise the actual scene engine, interrogate emitted
// primitives, invert their declared coordinates and evaluate interiors.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto'),path=require('node:path');
const root=process.cwd();const q=require(path.join(root,'web/physics-qft-lab.js'));
global.window={PrimerPhysicsQftLab:q};require(path.join(root,'web/spatial-qft.js'));require(path.join(root,'web/spatial-models.js'));require(path.join(root,'web/spatial-module-objects.js'));
const binding=JSON.parse(fs.readFileSync('data/module-models.json')).models.find(x=>x.node_id==='phys.5.qft');
assert(window.PrimerModuleObjects.ensure({props:{scenario:'module.phys.5.qft',family:binding.family,context:binding.context,mode:binding.mode,lesson:'Quantum Field Theory'}}));
const build=s=>window.PrimerSpatial.build('module.phys.5.qft',s),close=(a,b,message,abs=2e-12)=>assert(Math.abs(a-b)<=abs*Math.max(1,Math.abs(b)),`${message}: ${a} vs ${b}`);
const out={singleton:[],surfaces:[],gates:[],scattering:[],limits:['Actual SVG/browser paint and interaction are a separate pending reader requirement.','Face-interior measurements are samples. Universal error proof is separately derived, not inferred from a sampled pass.']};
for(const chargeUnits of [-3,-2,-1,0,1,2,3])for(const momentumMeV of [0,.17,10]){
 const state={mode:'antiparticle',chargeUnits,momentumMeV,massMeV:.37};const scene=build(state),chart=scene.qft.charts[1];
 const glyphs=scene.primitives.filter(x=>x.fidelity_kind==='qft_singleton_curve'&&x.panel===1);
 assert.equal(glyphs.length,2);
 for(const [key,charge] of [['particle',chargeUnits],['antiparticle',-chargeUnits]]){
  const p=glyphs.find(v=>v.key===key);assert.equal(p.kind,'sphere');assert(p.radius>0&&p.opacity>0);
  close((p.points[0][0]-chart.origin[0])/chart.xGain+chart.xmin,charge,'charge coordinate');
  close((p.points[0][1]-chart.origin[1])/chart.yGain+chart.ymin,Math.sqrt(.37*.37+momentumMeV*momentumMeV),'positive energy coordinate');
  assert(scene.primitives.some(v=>v.kind==='label'&&v.text===p.label));
 }
 if(chargeUnits===0){assert.deepEqual(glyphs[0].points,glyphs[1].points);assert.notEqual(glyphs[0].radius,glyphs[1].radius);assert.notEqual(glyphs[0].color,glyphs[1].color);assert(glyphs[1].opacity<1);}
 out.singleton.push({state,count:glyphs.length,neutralCoincident:chargeUnits===0});
}
const states=[];for(let n=1;n<=6;n++){states.push({mode:'casimir',gapUm:5,parallelK:10,normalMode:n});states.push({mode:'casimir',gapUm:.1,parallelK:0,normalMode:n});}
states.push({mode:'casimir',gapUm:4.8,parallelK:10,normalMode:1},{mode:'casimir',gapUm:3.213,parallelK:3.777,normalMode:4},{mode:'casimir',gapUm:.101,parallelK:.001,normalMode:6});
let triangles=0,probes=0,maxError=0,maxPrimitives=0;
const weights=[[.11,.23,.66],[.73,.17,.10],[.05,.9,.05],[.25,.5,.25],[.5,.5,0],[0,.5,.5],[1/3,1/3,1/3]];
for(const state of states){
 const scene=build(state),meta=scene.qft.extra.find(v=>v.kind==='standing-factor'),faces=scene.primitives.filter(v=>v.fidelity_kind==='qft_standing_factor');
 assert.deepEqual(meta.origin,[-1,-4,0]);assert.equal(meta.xGain,2);assert.equal(meta.zGain,2);assert.equal(meta.factorGain,.7);
 const A=state.normalMode*Math.PI,B=state.gapUm*state.parallelK;
 const nx=Math.max(16,Math.ceil(B/.2)),nz=Math.max(24,Math.ceil(A/.2));assert.equal(meta.nx,nx);assert.equal(meta.nz,nz);
 const bound=(A/nz+B/nx)**2/8;assert(bound<=.02+1e-15);close(meta.interpolationErrorBound,bound,'published proof bound');
 assert.equal(faces.length,2*nx*nz);assert(faces.length<=47500);assert(scene.primitives.length<=50000);maxPrimitives=Math.max(maxPrimitives,scene.primitives.length);
 const seen=new Set();let worst=0,maxPhaseWidth=0;
 for(const face of faces){
  assert.equal(face.kind,'polygon');assert.equal(face.points.length,3);assert(!seen.has(face.cell.join(',')+':'+face.triangle));seen.add(face.cell.join(',')+':'+face.triangle);
  const v=face.points.map(p=>({x:(p[0]+1)/2,z:p[2]/2,f:(p[1]+4)/.7}));
  v.forEach(p=>close(p.f,Math.sin(A*p.z)*Math.cos(B*p.x),'actual emitted vertex'));
  const phaseWidths=[1,-1].map(sign=>{const phi=v.map(p=>A*p.z+sign*B*p.x);return Math.max(...phi)-Math.min(...phi)});
  for(const width of phaseWidths)assert(width<=A/nz+B/nx+5e-14);maxPhaseWidth=Math.max(maxPhaseWidth,...phaseWidths);
  for(const w of weights){let px=0,pz=0,pf=0;for(let i=0;i<3;i++){px+=w[i]*v[i].x;pz+=w[i]*v[i].z;pf+=w[i]*v[i].f;}const err=Math.abs(pf-Math.sin(A*pz)*Math.cos(B*px));assert(err<=bound+2e-12);worst=Math.max(worst,err);probes++;}
 }
 triangles+=faces.length;maxError=Math.max(maxError,worst);out.surfaces.push({state,nx,nz,triangles:faces.length,primitives:scene.primitives.length,bound,maxPhaseWidth,maxObservedError:worst});
}
// Check every exact gate independently with fresh engine state. We control
// only local fixture specs; no application scene is replaced.
const engine=fs.readFileSync('web/spatial-models.js','utf8');
for(let bits=0;bits<16;bits++){
 const context=vm.createContext({window:{}});vm.runInContext(engine,context);
 const id=bits&1?'module.phys.5.qft':'module.phys.5.other',familyId=bits&2?'qft-observable-geometry':'other',linkedStateKey=bits&4?'phys.5.qft':'other',mode=bits&8?'casimir':'modes';
 const spec={initial:{mode},controls:[],familyId,linkedStateKey,primitiveBudget:()=>50000,build(s,g){for(let j=0;j<3001;j++)g.sphere([0,0,0],.1,'#000000');return {};}};
 context.window.PrimerSpatial.register({[id]:spec});let accepted=false;
 try{accepted=context.window.PrimerSpatial.build(id).primitives.length===3001;}catch(e){assert(String(e).includes('geometry limit'));}
 assert.equal(accepted,bits===15);assert.throws(()=>context.window.PrimerSpatial.register({[id]:spec}),/Duplicate spatial scene/);
 out.gates.push({bits,accepted});
}
// The budget gates on normalized state, not a raw supplied mode.
{
 const context=vm.createContext({window:{}});vm.runInContext(engine,context);context.window.PrimerSpatial.register({'module.phys.5.qft':{initial:{mode:'modes'},controls:[],familyId:'qft-observable-geometry',linkedStateKey:'phys.5.qft',normalize:()=>({mode:'modes'}),build(s,g){for(let j=0;j<3001;j++)g.sphere([0,0,0],.1,'#000000');return {};}}});
 assert.throws(()=>context.window.PrimerSpatial.build('module.phys.5.qft',{mode:'casimir'}),/geometry limit/);out.normalizedModeGate=true;
}
// Classification is mathematical, not based on a rounded invariant zero.
// Tiny-angle logarithmic oracle uses t=-p² theta²[1+O(theta²)] directly
// in log space, avoiding any Float64 subnormal sine evaluation.
for(const angleDeg of [0,Number.MIN_VALUE,1e-322,5e-322,6e-322,1e-321,1e-320,1e-310,1e-200,1e-160,1e-7,17.3,90,180-2**-45,180-2**-44,180])for(const momentumMeV of [0,Number.MIN_VALUE,1e-200,1,10]){
 const m=q.build({mode:'scattering',angleDeg,momentumMeV}),d=m.current,zero=angleDeg===0||momentumMeV===0;
 assert.equal(d.zeroTransfer,zero);assert.equal(d.photonOnShell,zero);assert.equal(d.transferClassification,zero?'zero transfer':'spacelike');
 const row={angleDeg,momentumMeV,t:d.t,u:d.u,tUnderflow:d.tUnderflow,classification:d.transferClassification};
 if(!zero&&d.t===0){assert(d.tUnderflow);assert(m.readout.includes('underflows Float64'));assert(Number.isFinite(d.log10AbsT));}
 if(!zero&&angleDeg<1e-150){const oracle=2*(Math.log10(momentumMeV)+Math.log10(angleDeg)+Math.log10(Math.PI/180));row.logReported=d.log10AbsT;row.logOracle=oracle;row.errorDex=Math.abs(d.log10AbsT-oracle);}
 const uZero=angleDeg===180||momentumMeV===0;assert.equal(d.uZeroTransfer,uZero);assert.equal(d.uPhotonOnShell,uZero);assert.equal(d.uTransferClassification,uZero?'zero transfer':'spacelike');
 if(!uZero&&d.u===0){assert(d.uUnderflow);assert(m.readout.includes('exchanged u transfer'));assert(m.ledger.find(v=>v[0]==='u channel q²')[1].includes('Float64 underflow'));assert(Number.isFinite(d.log10AbsU));}
 for(const [channel,deg,zeroChannel,value,logValue] of [['t',angleDeg,zero,d.t,d.log10AbsT],['u',180-angleDeg,uZero,d.u,d.log10AbsU]]){
  if(!zeroChannel&&deg<1e-150){const oracle=2*(Math.log10(momentumMeV)+Math.log10(deg)+Math.log10(Math.PI/180));close(logValue,oracle,'stable accepted-value tiny '+channel+' logarithm',4e-16);row[channel+'LogErrorDex']=Math.abs(logValue-oracle);}
  if(!zeroChannel&&deg<1e-10&&momentumMeV>=1){const rad=deg*(Math.PI/180),expected=-momentumMeV*momentumMeV*rad*rad;assert(Math.abs(value/expected-1)<4e-15,'accepted-degree endpoint invariant '+channel);}
  if(!zeroChannel&&deg===180&&momentumMeV>1e-150){close(value,-4*momentumMeV*momentumMeV,'opposite endpoint '+channel,1e-15);}
 }
 out.scattering.push(row);
 if(angleDeg===1e-7&&momentumMeV===1){const theta=angleDeg*Math.PI/180;close(d.t,-theta*theta,'small-angle noncancelling selected invariant',1e-33);}
 for(const p of m.panels[1].curves[0].points){const theta=p.x*Math.PI/180,oracle=-2*momentumMeV**2*(1-Math.cos(theta));if(theta>.1)close(p.y,oracle,'normal-angle plotted invariant');}
}
out.summary={singletonStates:out.singleton.length,surfaceStates:out.surfaces.length,triangles,facetInteriorProbes:probes,maxObservedError:maxError,maxPrimitives,gateCases:out.gates.length,scatterStates:out.scattering.length,maxTinyLogErrorDex:Math.max(...out.scattering.map(v=>v.errorDex||0))};
out.pins=Object.fromEntries(['web/physics-qft-lab.js','web/spatial-qft.js','web/spatial-models.js','web/spatial-module-objects.js','tools/check_physics_qft_integrated_geometry.js'].map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')]));
fs.writeFileSync('.research/qft-integrated-science-audit-20261011/final-independent-emission-result.json',JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(out.summary,null,2));

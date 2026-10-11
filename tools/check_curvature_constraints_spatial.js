#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
global.window = {};
window.PrimerMathCurvatureLab = require('../web/math-curvature-lab.js');
window.PrimerPhysicsConstraintsLab = require('../web/physics-constraints-lab.js');
require('../web/spatial-models.js');
require('../web/spatial-module-objects.js');
const spatial = window.PrimerSpatial, objects = window.PrimerModuleObjects;
const manifest = JSON.parse(fs.readFileSync(require('node:path').join(__dirname, '../data/module-models.json'), 'utf8'));
for (const id of ['math.5.diffgeo', 'phys.4.classical']) {
  const row = manifest.models.find(row => row.node_id === id);
  assert.ok(row);
  assert.equal(row.mode, 'model');
  assert.equal(objects.ensure({props:{scenario:'module.'+id,family:row.family,context:row.context,mode:row.mode,lesson:id}}), true);
}
function near(a,b,label='scalar') {assert.ok(Number.isFinite(a) && Math.abs(a-b)<=3e-11*Math.max(1,Math.abs(a),Math.abs(b)),label+': '+a+' versus '+b);}
function vector(a,b,label) {assert.equal(a.length,b.length);a.forEach((x,i)=>near(x,b[i],label));}
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),scale=(a,k)=>a.map(v=>v*k),add=(a,b)=>a.map((v,i)=>v+b[i]);
function surface(kind,r,R,a,b) {
  const u=kind==='plane'?r*a:Math.PI*a, v=kind==='sphere'?Math.PI*b/2:kind==='torus'?Math.PI*b:r*b;
  if(kind==='plane')return {point:[u,v,0],K:0};
  if(kind==='cylinder')return {point:[r*Math.cos(u),r*Math.sin(u),v],K:0};
  if(kind==='sphere')return {point:[r*Math.cos(v)*Math.cos(u),r*Math.cos(v)*Math.sin(u),r*Math.sin(v)],K:1/(r*r)};
  return {point:[(R+r*Math.cos(v))*Math.cos(u),(R+r*Math.cos(v))*Math.sin(u),r*Math.sin(v)],K:Math.cos(v)/(r*(R+r*Math.cos(v)))};
}
let surfaceStates=0,hoopStates=0;
for(const kind of ['plane','cylinder','sphere','torus'])for(const r of [.5,1,2])for(const R of [3,6])for(const [a,b] of [[-1,-1],[0,0],[.5,.5],[1,1]])for(const coverage of [0,5,50,100]) {
  const supplied={surface:kind,radius:r,major:R,a,b,coverage},s=spatial.build('module.math.5.diffgeo',supplied),c=s.curvature;
  assert.equal(c.state.surface,kind);
  vector(c.local.point,surface(kind,r,R,a,b).point,'actual probe position');
  near(c.local.gaussian,surface(kind,r,R,a,b).K,'probe K');
  const cells=s.primitives.filter(p=>p.curvature_kind==='surface_cell');
  assert.equal(cells.length,c.faces.length);
  const cut=-1+2*coverage/100;
  let selectedParameterArea=0;
  for(let i=0;i<c.faces.length;i++) {
    const f=c.faces[i],p=f.parameters;
    assert.equal(f.selected,p.a1<=cut);
    assert.ok(p.a1<=cut || p.a0>=cut,'cell is split exactly at the selected parameter boundary');
    if(f.selected)selectedParameterArea+=(p.a1-p.a0)*(p.b1-p.b0);
    const expected=[[p.a0,p.b0],[p.a1,p.b0],[p.a1,p.b1],[p.a0,p.b1]].map(([x,y])=>surface(kind,r,R,x,y).point);
    expected.forEach((v,j)=>{vector(f.corners[j],v,'analytic cell corner');vector(cells[i].points[j],v,'rendered cell corner');});
    near(f.gaussian,surface(kind,r,R,(p.a0+p.a1)/2,(p.b0+p.b1)/2).K,'cell midpoint K');
  }
  near(selectedParameterArea,4*coverage/100,'selected fractional parameter area');
  const area=kind==='plane'?4*r*r*coverage/100:kind==='cylinder'?4*Math.PI*r*r*coverage/100:kind==='sphere'?4*Math.PI*r*r*coverage/100:4*Math.PI*Math.PI*R*r*coverage/100;
  near(c.integral.area,area,'analytic area');
  near(c.integral.curvatureIntegral,kind==='sphere'?4*Math.PI*coverage/100:0,'analytic integrated curvature');
  const flipped=spatial.build('module.math.5.diffgeo',{...supplied,normal:'inward'}).curvature;
  c.faces.forEach((f,i)=>f.corners.forEach((p,j)=>vector(flipped.faces[i].corners[j],p,'normal flip preserves actual surface')));
  vector(flipped.local.normal,scale(c.local.normal,-1),'normal reversal');
  c.local.principal.forEach((x,i)=>near(flipped.local.principal[i],-x,'principal sign'));
  near(flipped.local.gaussian,c.local.gaussian,'intrinsic K invariant');
  if(kind==='sphere' && Math.abs(b)===1)assert.equal(c.local.regular,false);
  surfaceStates++;
}
for(const R of [.5,1,2])for(const m of [.5,1,2])for(const angle of [-180,-90,-45,0,45,90,180])for(const w of [-3,0,3])for(const O of [-4,0,4])for(const phase of [0,90,180]) {
  const scene=spatial.build('module.phys.4.classical',{radius:R,mass:m,angle,rate:w,omega:O,phase}),h=scene.constraints.snapshot;
  const t=angle*Math.PI/180,p=phase*Math.PI/180,a=Math.sin(t),b=Math.cos(t),c=Math.cos(p),d=Math.sin(p);
  const er=[a*c,a*d,-b],et=[b*c,b*d,a],ep=[-d,c,0];
  const display=p=>[p[0],p[2],-p[1]];
  assert.deepEqual(scene.constraints.displayFrame,[[1,0,0],[0,0,1],[0,-1,0]]);
  const position=scale(er,R),velocity=add(scale(et,R*w),scale(ep,R*O*a));
  // Resolve Newton acceleration in the radial/meridional/azimuthal frame;
  // this is independent of the runtime's Cartesian second-derivative formula.
  const acceleration=add(add(scale(et,-9.8*a),scale(er,-R*(w*w+O*O*a*a))),scale(ep,2*R*O*w*b));
  const gravity=[0,0,-9.8*m],reaction=add(scale(acceleration,m),scale(gravity,-1));
  vector(h.position,position,'laboratory position');vector(h.velocity,velocity,'laboratory velocity');
  vector(h.acceleration,acceleration,'Newtonian acceleration');vector(h.reactionForce,reaction,'constraint force');
  near(dot(reaction,scale(et,R)),0,'zero virtual work coefficient');
  near(dot(reaction,velocity),2*m*R*R*O*O*a*b*w,'drive power');
  near(h.Elab-h.Hreduced,m*R*R*O*O*a*a,'laboratory minus reduced energy');
  for(const [key,value,k] of [['gravity',gravity,.1],['reaction',reaction,.1],['velocity',velocity,.2],['virtual',scale(et,R),.2]]) {
    const primitive=scene.primitives.find(x=>x.constraints_kind===({virtual:'virtual_theta'}[key]||key));
    vector(primitive.points[0],display(position),'rigid display glyph anchor');vector(primitive.points[1],display(add(position,scale(value,k))),'true calibrated display glyph');
  }
  assert.equal(scene.constraints.wire.length,97);
  const drawnWire=scene.primitives.find(p=>p.constraints_kind==='wire').points;
  scene.constraints.wire.forEach((p,i)=>vector(drawnWire[i],display(p),'actual rigid display wire'));
  const bead=scene.primitives.find(p=>p.constraints_kind==='bead');vector(bead.points[0],display(position),'actual rigid display bead');
  for(const p of scene.constraints.wire){near(dot(p,p),R*R,'wire radius');near(-d*p[0]+c*p[1],0,'wire plane');}
  if(O===0)near(h.constraintPower,0,'fixed ideal constraint is workless');
  hoopStates++;
}
console.log('Verified '+surfaceStates+' independently parameterized surface states and '+hoopStates+' Newtonian hoop states; exact patch splits, poles, normal invariance, force glyphs and laboratory/virtual-work distinctions passed.');

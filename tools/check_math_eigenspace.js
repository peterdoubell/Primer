#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
globalThis.window = {};
require('../web/math-eigenspace.js');
const api = window.PrimerMathEigenspace;
const matrices = [
  { a: [[1,0],[0,1]], eigen: [1,1], rank: 2, dimensions: [2], name: 'Identity' },
  { a: [[2,0],[0,1]], eigen: [2,1], rank: 2, dimensions: [1,1], name: 'Stretch x by 2' },
  { a: [[1,1],[0,1]], eigen: [1,1], rank: 2, dimensions: [1], name: 'Shear x by y' },
  { a: [[1,0],[0,-1]], eigen: [1,-1], rank: 2, dimensions: [1,1], name: 'Reflect across x-axis' },
  { a: [[1,0],[0,0]], eigen: [1,0], rank: 1, dimensions: [1,1], name: 'Project onto x-axis' },
];
function near(a,b,tolerance=1e-12) { assert.ok(Math.abs(a-b)<=tolerance*Math.max(1,Math.abs(b)),`${a} vs ${b}`); }
let states = 0;
for (const example of matrices) for (let angle = 0; angle <= 180; angle += 5) {
  const m = api.analyze(example.a,angle);
  assert.equal(m.rank,example.rank);
  assert.deepEqual(m.spaces.map(s=>s.dimension),example.dimensions);
  const values = m.spaces.flatMap(s=>Array(s.multiplicity).fill(s.value));
  assert.deepEqual(values,example.eigen);
  near(values.reduce((a,b)=>a+b),m.trace); near(values.reduce((a,b)=>a*b),m.determinant);
  for (const space of m.spaces) for (const v of space.basis) {
    // Characteristic equation and Av=λv are independent of the renderer's basis algorithm.
    const [[a,b],[c,d]]=example.a, l=space.value;
    near((a-l)*(d-l)-b*c,0); near(a*v[0]+b*v[1],l*v[0]); near(c*v[0]+d*v[1],l*v[1]);
  }
  for (const v of m.kernel) {
    near(example.a[0][0]*v[0]+example.a[0][1]*v[1],0);
    near(example.a[1][0]*v[0]+example.a[1][1]*v[1],0);
  }
  assert.equal(m.rank+m.kernel.length,2);
  near(m.v[0]**2+m.v[1]**2,1);
  near(m.parallel[0]+m.residual[0],m.image[0]); near(m.parallel[1]+m.residual[1],m.image[1]);
  near(m.v[0]*m.residual[0]+m.v[1]*m.residual[1],0);
  if (example.name==='Identity') assert.equal(m.residualNorm,0);
  states++;
}
assert.equal(api.analyze([[1,1],[0,1]]).diagonalizable,false);
assert.equal(api.analyze([[1,0],[0,1]]).diagonalizable,true);
assert.equal(api.analyze([[1,0],[0,0]],90).residualNorm,0);
assert.deepEqual(api.analyze([[1,0],[0,0]],90).image,[0,0]);
assert.equal(api.analyze([[1,0],[0,-1]],90).quotient,-1);
for (const a of [null,[[1]],[[1,2],[3,NaN]],[[1,2],[3,'4']]]) assert.throws(()=>api.analyze(a),TypeError);
for (const a of [-1,181,Infinity,NaN]) assert.throws(()=>api.analyze([[1,0],[0,1]],a),RangeError);

class Text { constructor(value) {this.nodeType=3;this.textContent=String(value);} }
class Element {
  constructor(tag) {this.tagName=tag;this.nodeType=1;this.attributes={};this.children=[];this.events={};
    this.classList={toggle:(name,on)=>{const tokens=new Set((this.attributes.class||'').split(/\s+/).filter(Boolean));
      if(on)tokens.add(name);else tokens.delete(name);this.attributes.class=[...tokens].join(' ');}}; }
  setAttribute(k,v){this.attributes[k]=String(v);if(k==='value')this.value=String(v);}
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=items;}
  get textContent(){return this.children.map(c=>c.textContent).join('');}
  set textContent(v){this.children=[new Text(v)];}
  addEventListener(k,h){(this.events[k]||=[]).push(h);}
  fire(k){(this.events[k]||[]).forEach(h=>h({target:this}));}
  all(){return [this,...this.children.filter(c=>c.nodeType===1).flatMap(c=>c.all())];}
}
globalThis.document={createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),createTextNode:v=>new Text(v)};
const controller=api.create(), root=controller.element;
const one=k=>root.all().find(e=>e.attributes[k]);
const readout=()=>root.all().find(e=>e.attributes.class==='math-eigen-readout').textContent;
const initial=readout();let mounted=0;
for(const example of matrices){
 controller.setMatrix(example.a,example.name);
 const slider=one('data-eigen-angle');
 for(let angle=0;angle<=180;angle+=5){
  slider.value=String(angle);slider.fire('input');slider.fire('change');
  const v=angle===0?[1,0]:angle===90?[0,1]:angle===180?[-1,0]:[Math.cos(angle*Math.PI/180),Math.sin(angle*Math.PI/180)];
  const image=[example.a[0][0]*v[0]+example.a[0][1]*v[1],example.a[1][0]*v[0]+example.a[1][1]*v[1]];
  for(const [role,point] of [['probe',v],['image',image]]){
   const line=root.all().find(e=>e.attributes['data-eigen-vector']===role);
   near(Number(line.attributes.x1),232);near(Number(line.attributes.y1),195);
   near(Number(line.attributes.x2),232+72*point[0]);near(Number(line.attributes.y2),195-72*point[1]);
  }
  assert.ok(slider.attributes['aria-valuetext']);assert.doesNotMatch(readout(),/NaN|Infinity/);
  for(const e of root.all())for(const value of Object.values(e.attributes))assert.doesNotMatch(value,/NaN|Infinity/);
  mounted++;
 }
}
controller.reset();controller.setMatrix([[1,1],[0,1]],'Shear x by y');assert.equal(readout(),initial);
const enlarge=root.all().find(e=>e.attributes['aria-pressed']!==undefined);
enlarge.fire('click');assert.equal(enlarge.attributes['aria-pressed'],'true');
enlarge.fire('click');assert.equal(enlarge.attributes['aria-pressed'],'false');
console.log(`Verified ${states} eigen/projection states and ${mounted} mounted coordinate states; all five eigenspaces, rank/nullity, negative and zero eigenvalues, defective shear and reset passed.`);

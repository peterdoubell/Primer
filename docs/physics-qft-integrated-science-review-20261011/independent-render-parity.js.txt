'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const current=fs.readFileSync('web/spatial-models.js','utf8'),previous=fs.readFileSync(require('node:path').join(__dirname,'frozen-original-spatial-models.js'),'utf8'),modules=fs.readFileSync('web/spatial-module-objects.js','utf8');
class E {constructor(tag){this.tag=tag;this.attrs={};this.children=[];this.events={};this.style={};this.dataset={};this.textContent='';this.value='';this.isConnected=true;this.classList={toggle(){},remove(){},add(){}};}setAttribute(k,v){this.attrs[k]=String(v);if(k==='value')this.value=String(v);}append(...children){this.children.push(...children)}prepend(...c){this.children.unshift(...c)}replaceChildren(...c){this.children=c}addEventListener(k,f){(this.events[k]??=[]).push(f)}focus(){}setPointerCapture(){}hasPointerCapture(){return false}get options(){return this.children.filter(c=>c.tag==='option')}dispatch(k,props={}){for(const f of this.events[k]||[])f({preventDefault(){},...props});}}
const document={createElement:t=>new E(t),createElementNS:(ns,t)=>new E(t),createTextNode:t=>Object.assign(new E('#text'),{textContent:String(t)})};
function context(engine,qft=false){const c=vm.createContext({window:{},document,requestAnimationFrame:f=>{f();return 1},cancelAnimationFrame(){}});if(qft){vm.runInContext(fs.readFileSync('web/physics-qft-lab.js','utf8'),c);vm.runInContext(fs.readFileSync('web/spatial-qft.js','utf8'),c)}vm.runInContext(engine,c);vm.runInContext(modules,c);return c;}
function find(e,tag){if(e.tag===tag)return e;for(const child of e.children){const r=find(child,tag);if(r)return r}return null}
function canon(e){return JSON.stringify({tag:e.tag,attrs:e.attrs,text:e.textContent,children:e.children.map(c=>JSON.parse(canon(c)))});}
const manifest=JSON.parse(fs.readFileSync('data/module-models.json')).models;
const a=context(previous),b=context(current),results=[];
for(const family of ['pendulum','lattice','cell','magnet','molecule','surface','urn','lens']){
 const binding=manifest.find(x=>x.family===family);if(!binding)continue;
 const id='module.'+binding.node_id,item={title:binding.title,instructions:binding.instructions,props:{scenario:id,family:binding.family,context:binding.context,mode:binding.mode,lesson:binding.node_id}};
 assert(a.window.PrimerModuleObjects.ensure(item));assert(b.window.PrimerModuleObjects.ensure(item));
 const ctl=a.window.PrimerSpatial.controls(id),states=[{},Object.fromEntries(ctl.map(c=>[c.key,c.options?c.options[0].value:c.min])),Object.fromEntries(ctl.map(c=>[c.key,c.options?c.options.at(-1).value:c.max]))];
 for(const state of states){
  assert.equal(JSON.stringify(a.window.PrimerSpatial.build(id,state)),JSON.stringify(b.window.PrimerSpatial.build(id,state)));
  const ra=a.window.PrimerSpatial.render(item,{state}),rb=b.window.PrimerSpatial.render(item,{state}),sa=find(ra,'svg'),sb=find(rb,'svg');
  assert.equal(canon(sa),canon(sb),'ordinary SVG draw parity '+family);
  let paints=1;for(const key of ['ArrowLeft','ArrowUp','+','Home','ArrowRight']){sa.dispatch('keydown',{key});sb.dispatch('keydown',{key});assert.equal(canon(sa),canon(sb),'camera projection parity '+family+' '+key);paints++}
  results.push({family,id,state,primitiveCount:b.window.PrimerSpatial.build(id,state).primitives.length,identicalSvgPaints:paints});
 }
}
// Reconstruct only the pre-fix extrema expressions in the integrated engine.
// This reproduces the >142k-argument failure without changing product files.
let unbounded=current.replace('(bounds.reduce((v,p)=>Math.min(v,p[axis]),Infinity) + bounds.reduce((v,p)=>Math.max(v,p[axis]),-Infinity)) / 2','(Math.min(...bounds.map(p => p[axis])) + Math.max(...bounds.map(p => p[axis]))) / 2')
 .replace('const radius = current.primitives.filter(p => p.kind !== \'label\').reduce((r,p)=>\n      p.points.reduce((v,point)=>Math.max(v,length(subtract(point,center))+(p.radius||0)),r),.1);','const radius = Math.max(.1, ...current.primitives.filter(p => p.kind !== \'label\')\n      .flatMap(p => p.points.map(v => length(subtract(v, center)) + (p.radius || 0))));')
 .replace('282 / extents.reduce((v,p)=>Math.max(v,Math.abs(p.point[0])+p.radius),.1)','282 / Math.max(.1, ...extents.map(p => Math.abs(p.point[0]) + p.radius))')
 .replace('192 / extents.reduce((v,p)=>Math.max(v,Math.abs(p.point[1])+p.radius),.1)','192 / Math.max(.1, ...extents.map(p => Math.abs(p.point[1]) + p.radius))');
assert.notEqual(unbounded,current);
const old=context(unbounded,true),now=context(current,true),binding=manifest.find(x=>x.node_id==='phys.5.qft');
const item={title:binding.title,instructions:binding.instructions,props:{scenario:'module.phys.5.qft',family:binding.family,context:binding.context,mode:binding.mode,lesson:'Quantum Field Theory'}};
assert(old.window.PrimerModuleObjects.ensure(item));assert(now.window.PrimerModuleObjects.ensure(item));
const maxState={mode:'casimir',gapUm:5,parallelK:10,normalMode:6};let oldError;
try{old.window.PrimerSpatial.render(item,{state:maxState})}catch(e){oldError=String(e)}assert(oldError&&oldError.includes('Maximum call stack size exceeded'),'preserve exact maximum-mesh spread failure');
const scene=now.window.PrimerSpatial.build('module.phys.5.qft',maxState),root=now.window.PrimerSpatial.render(item,{state:maxState}),svg=find(root,'svg');
function count(e,tag){return (e.tag===tag?1:0)+e.children.reduce((v,c)=>v+count(c,tag),0)}
assert.equal(count(svg,'polygon'),47500);for(const key of ['ArrowLeft','+','Home']){svg.dispatch('keydown',{key});assert.equal(count(svg,'polygon'),47500)}
const result={status:'pass',engine_sha256:crypto.createHash('sha256').update(current).digest('hex'),ordinaryRendererParity:results,ordinaryIdenticalPaints:results.reduce((n,r)=>n+r.identicalSvgPaints,0),maxMesh:{state:maxState,primitives:scene.primitives.length,svgPolygons:count(svg,'polygon'),cameraActions:3},preservedUnboundedFailure:oldError,limits:'In-memory document exercises actual SVG element/coordinate production, not browser painting, CSS, performance or real viewport behavior. Separate maximum-mesh desktop/mobile QA remains required.'};
fs.mkdirSync('.research/qft-integrated-science-audit-20261011',{recursive:true});
fs.writeFileSync('.research/qft-integrated-science-audit-20261011/independent-render-parity-result.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,ordinaryCases:results.length,ordinaryIdenticalPaints:result.ordinaryIdenticalPaints,maxMesh:result.maxMesh,preservedUnboundedFailure:oldError},null,2));

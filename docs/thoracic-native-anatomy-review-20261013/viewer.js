'use strict';
const canvas = document.querySelector('canvas');
const status = document.querySelector('#status');
const select = document.querySelector('#part');
const gl = canvas.getContext('webgl2', {antialias: true, preserveDrawingBuffer: true});
const cache = new Map(), pending = new Map();
let manifest, program, visible = [], azimuth = 0, elevation = -.9, distance = 4, drag = null, generation = 0;
const vertex = `#version 300 es
precision highp float;
in vec3 position; in vec3 normal;
uniform vec3 center; uniform float scale; uniform float azimuth; uniform float elevation;
uniform float distance; uniform float aspect; out vec3 surfaceNormal;
vec3 rotate(vec3 q) {
  float a=cos(azimuth),b=sin(azimuth),c=cos(elevation),d=sin(elevation);
  vec3 p=vec3(a*q.x-b*q.y,b*q.x+a*q.y,q.z);
  return vec3(p.x,c*p.y-d*p.z,d*p.y+c*p.z);
}
void main() {
  vec3 p=rotate((position-center)*scale); float z=distance-p.z;
  gl_Position=vec4(2.0*p.x/aspect,2.0*p.y,1.002002*z-.2002002,z);
  surfaceNormal=rotate(normal);
}`;
const fragment = `#version 300 es
precision highp float; in vec3 surfaceNormal; uniform vec3 displayColor; out vec4 color;
void main() {
  vec3 n=normalize(surfaceNormal); float light=.25+.75*abs(dot(n,normalize(vec3(.3,.5,1.0))));
  color=vec4(displayColor*light,1.0);
}`;
function shader(kind, source) {
  const item = gl.createShader(kind); gl.shaderSource(item, source); gl.compileShader(item);
  if (!gl.getShaderParameter(item, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(item));
  return item;
}
async function sha(bytes) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
}
function color(part) {
  if (part.id.startsWith('FJ1451')) return [.82,.57,.33];
  if (part.id.startsWith('FJ1455')) return [.32,.65,.82];
  if (part.id.startsWith('FJ1454')) return [.38,.75,.49];
  return part.id === 'FJ3131' ? [.79,.59,.39] : [.76,.55,.83];
}
async function loadMesh(part) {
  if (cache.has(part.id)) return cache.get(part.id);
  const response = await fetch(part.file);
  if (!response.ok) throw Error('Source transport unavailable: '+part.id);
  let bytes = await response.arrayBuffer();
  const header = new Uint8Array(bytes,0,2);
  if (header[0]===31 && header[1]===139) {
    if (await sha(bytes)!==part.transport_sha256) throw Error('Compressed source hash differs');
    bytes = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  }
  if (await sha(bytes)!==part.decoded_sha256) throw Error('Decoded source hash differs');
  const view = new DataView(bytes), nv = view.getUint32(4,true), ni = view.getUint32(8,true);
  if (new TextDecoder().decode(bytes.slice(0,4))!=='BP3D' || nv!==part.vertices || ni!==part.faces*3 || bytes.byteLength!==12+nv*24+ni*4) throw Error('Source array layout differs');
  const vao = gl.createVertexArray(); gl.bindVertexArray(vao); const buffers = [];
  for (const [name,offset] of [['position',12],['normal',12+nv*12]]) {
    const buffer=gl.createBuffer(); buffers.push(buffer); gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(bytes,offset,nv*3),gl.STATIC_DRAW);
    const location=gl.getAttribLocation(program,name); gl.enableVertexAttribArray(location);
    gl.vertexAttribPointer(location,3,gl.FLOAT,false,0,0);
  }
  const index=gl.createBuffer(); buffers.push(index); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,index);
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint32Array(bytes,12+nv*24,ni),gl.STATIC_DRAW);
  const mesh={part,vao,buffers}; cache.set(part.id,mesh); return mesh;
}
async function load(part) {
  if (cache.has(part.id)) return cache.get(part.id);
  if (pending.has(part.id)) return pending.get(part.id);
  const request = loadMesh(part); pending.set(part.id, request);
  try { return await request; } finally { pending.delete(part.id); }
}
function draw() {
  if (!visible.length) return;
  const ratio=Math.min(devicePixelRatio,2), w=Math.round(canvas.clientWidth*ratio), h=Math.round(canvas.clientHeight*ratio);
  if (canvas.width!==w || canvas.height!==h) {canvas.width=w;canvas.height=h;}
  gl.viewport(0,0,w,h); gl.clearColor(.03,.05,.08,1); gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT); gl.useProgram(program);
  const lo=[0,1,2].map(i=>Math.min(...visible.map(m=>m.part.bounds[0][i])));
  const hi=[0,1,2].map(i=>Math.max(...visible.map(m=>m.part.bounds[1][i])));
  gl.uniform3fv(gl.getUniformLocation(program,'center'),lo.map((x,i)=>(x+hi[i])/2));
  const scale=2/Math.max(...lo.map((x,i)=>hi[i]-x));
  for (const [key,value] of Object.entries({scale,azimuth,elevation,distance,aspect:w/h})) gl.uniform1f(gl.getUniformLocation(program,key),value);
  for (const mesh of visible) {
    gl.bindVertexArray(mesh.vao); gl.uniform3fv(gl.getUniformLocation(program,'displayColor'),color(mesh.part));
    gl.drawElements(gl.TRIANGLES,mesh.part.faces*3,gl.UNSIGNED_INT,0);
  }
  if (gl.getError()) throw Error('Source geometry rendering failed');
  canvas.dataset.faces=String(visible.reduce((n,m)=>n+m.part.faces,0));
  canvas.dataset.parts=visible.map(m=>m.part.id).join(',');
}
function selectedParts(id) {
  if (id==='all') return manifest.parts;
  if (id==='intercostals') return manifest.parts.filter(p=>p.id.startsWith('FJ145'));
  if (id==='valves') return manifest.parts.filter(p=>!p.id.startsWith('FJ145') && p.id!=='FJ3131');
  return manifest.parts.filter(p=>p.id===id);
}
async function choose(id) {
  const request=++generation; canvas.dataset.ready='false'; canvas.dataset.error='false'; canvas.hidden=true;
  document.querySelector('#retry').hidden=true; document.querySelector('#original').hidden=true;
  document.querySelector('#evidence').textContent=''; document.querySelector('#selection-context').textContent='Loading the selected source…';
  status.textContent='Loading original source transport…';
  try {
  const parts=selectedParts(id); if (!parts.length) throw Error('Unknown source selection');
  const meshes=await Promise.all(parts.map(load)); if (request!==generation) return;
  visible=meshes; canvas.hidden=false; azimuth=0;elevation=-.9;distance=4;draw();
  document.querySelector('#selection-context').textContent = id==='all' || id==='intercostals'
    ? 'Intercostal muscle surfaces are included; rib bones, lungs and pleural layers remain unavailable in this assembly.'
    : id==='valves' || parts.every(p=>!p.id.startsWith('FJ145') && p.id!=='FJ3131')
      ? 'Source valve leaflets are included; chambers, annuli and pericardium remain unavailable in this assembly.'
      : 'Original source surface with no current-patient registration or verified physiological motion.';
  document.querySelector('#legend').textContent = 'Display colours: external intercostal muscles — amber; internal — blue; innermost — green; diaphragm — tan; valve leaflets — violet.';
  document.querySelector('#evidence').textContent=JSON.stringify(parts,null,2);
  const original=document.querySelector('#original'); original.hidden=parts.length!==1;
  if (parts.length===1) {original.href=parts[0].source_obj;original.textContent='Unchanged original OBJ (gzip) · '+parts[0].id;}
  status.textContent=parts.length+' source object(s) · all '+Number(canvas.dataset.faces).toLocaleString()+' source faces · common original coordinates · assembly unapproved';
  canvas.dataset.selection=id; canvas.dataset.ready='true';
  } catch (error) {
    if (request!==generation) return;
    canvas.hidden=true; canvas.dataset.error='true'; status.textContent=error.message;
    document.querySelector('#selection-context').textContent='The selected source is unavailable. No previous geometry is displayed as this selection.';
    document.querySelector('#retry').hidden=false;
  }
}
function reset(){azimuth=0;elevation=-.9;distance=4;draw();}
canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);canvas.focus();});
canvas.addEventListener('pointermove',e=>{if(drag){azimuth+=(e.clientX-drag[0])*.01;elevation+=(e.clientY-drag[1])*.01;drag=[e.clientX,e.clientY];draw();}});
for(const event of ['pointerup','pointercancel'])canvas.addEventListener(event,()=>drag=null);
canvas.addEventListener('wheel',e=>{e.preventDefault();distance=Math.max(2,Math.min(12,distance+e.deltaY*.005));draw();},{passive:false});
canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','='].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')azimuth-=.15;if(e.key==='ArrowRight')azimuth+=.15;if(e.key==='ArrowUp')elevation-=.15;if(e.key==='ArrowDown')elevation+=.15;if(['+','='].includes(e.key))distance=Math.max(2,distance-.2);if(e.key==='-')distance=Math.min(12,distance+.2);draw();});
document.querySelector('#fit').onclick=reset;
document.querySelector('#retry').onclick=()=>choose(select.value);
for(const button of document.querySelectorAll('[data-camera]'))button.onclick=()=>{azimuth=button.dataset.camera==='yz'?-Math.PI/2:0;elevation=button.dataset.camera==='xy'?0:-Math.PI/2;draw();};
select.onchange=()=>choose(select.value).catch(e=>{status.textContent=e.message;canvas.dataset.error='true';});
window.addEventListener('resize',draw);
(async()=>{
  if(!gl)throw Error('WebGL2 unavailable');
  program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.enable(gl.DEPTH_TEST);
  manifest=await (await fetch('manifest.json')).json();
  for(const [id,label] of [['all','All retained source objects'],['intercostals','Intercostal source layers and M variants'],['valves','All five source valve leaflets']])select.append(new Option(label,id));
  for(const part of manifest.parts)select.append(new Option(part.id+' · '+part.label+(part.producer_M_variant?' · producer M variant':''),part.id));
  for(const text of manifest.limitations){const li=document.createElement('li');li.textContent=text;document.querySelector('#limits').append(li);}
  const credit=document.querySelector('#credit');credit.append(document.createTextNode(manifest.attribution+' '));const link=document.createElement('a');link.href=manifest.license_url;link.textContent=manifest.license;credit.append(link);
  select.value='FJ3131';await choose(select.value);
})().catch(e=>{status.textContent=e.message;canvas.dataset.error='true';});

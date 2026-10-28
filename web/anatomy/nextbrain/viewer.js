import {sha, decode, payload} from './transport.js';
const $ = id => document.getElementById(id);
const state = {code:19, ijk:[0,0,0], yaw:2.65, pitch:.25, zoom:1};
let manifest, labels, config, planeController, meshController, planeGeneration=0, meshGeneration=0, gpu;
const panels = [['axial',2],['coronal',1],['sagittal',0]];
for (const [name,axis] of panels) {
  const section=document.createElement('section');
  section.innerHTML=`<h2>${name[0].toUpperCase()+name.slice(1)}</h2><label>Source ${'ijk'[axis]}<input type="range" id="slice${axis}" min="0" step="1"></label><div class="viewport" tabindex="0"><div class="plane-image"><div class="orientation-row" id="top${axis}"></div><div class="plane-mid"><span id="left${axis}"></span><canvas id="plane${axis}" role="img" aria-label="${name} source plane"></canvas><span id="right${axis}"></span></div><div class="orientation-row" id="bottom${axis}"></div><div class="plane-mid"><span></span><svg id="scale${axis}" role="img" aria-label="10 millimetre source scale"></svg><span></span></div><span class="scale-label">10 mm</span></div></div><p id="axes${axis}"></p>`;
  $('panels').append(section);
  $('slice'+axis).oninput=()=>{state.ijk[axis]=Number($('slice'+axis).value);renderPlanes();};
}
function selected(){return labels.classes.find(r=>r.code===state.code);}
async function plane(volume,axis,index,signal){
  const row=manifest.volumes[volume].planes[axis][index];
  const packed=await payload(config.blobPrefix,row.file,manifest.packs[row.file],row,signal);
  return {row,bytes:await decode(packed,row.decodedBytes,row.decodedSHA256)};
}
function clearPlanes(){for(const [,axis] of panels){const c=$('plane'+axis);c.getContext('2d').clearRect(0,0,c.width,c.height);$('axes'+axis).textContent='';}}
async function renderPlanes(){
  if(!manifest)return;
  planeController?.abort();planeController=new AbortController();const signal=planeController.signal,generation=++planeGeneration;
  delete document.body.dataset.planesReady;clearPlanes();$('status').textContent='Loading verified source planes…';
  const ijk=[...state.ijk],code=state.code,mode=$('display').value,overlay=$('overlay').checked,outline=$('outline').checked;
  const low=Number($('low').value),high=Number($('high').value);
  if(!Number.isFinite(low)||!Number.isFinite(high)||low<0||high>255||low>=high){$('status').textContent='Choose a window with 0 ≤ low < high ≤ 255.';return;}
  try{
    const result=await Promise.all(panels.map(async([name,axis])=>{
      const [m,l]=await Promise.all([mode==='mri'?plane('MRI',axis,ijk[axis],signal):null,plane('labels',axis,ijk[axis],signal)]);
      const [w,h]=l.row.shape,display=manifest.displayPlanes[name],pixels=new Uint8ClampedArray(w*h*4);
      for(let y=0;y<h;y++)for(let x=0;x<w;x++){
        const source=x+w*y,value=l.bytes[source],hit=value===code;
        const edge=hit&&(x===0||y===0||x===w-1||y===h-1||l.bytes[source-1]!==code||l.bytes[source+1]!==code||l.bytes[source-w]!==code||l.bytes[source+w]!==code);
        const dx=display.flipX?w-1-x:x,dy=display.flipY?h-1-y:y,k=4*(dx+w*dy);
        let grey=mode==='mri'?Math.round(255*Math.max(0,Math.min(1,(m.bytes[source]-low)/(high-low)))):value?100:20;
        pixels[k]=pixels[k+1]=pixels[k+2]=grey;pixels[k+3]=255;
        if((mode==='schematic'||overlay)&&hit&&(!outline||edge)){pixels[k]=20;pixels[k+1]=180;pixels[k+2]=175;}
      }
      return {axis,w,h,pixels,display};
    }));
    if(signal.aborted||generation!==planeGeneration)return;
    for(const {axis,w,h,pixels,display}of result){
      const c=$('plane'+axis);c.width=w;c.height=h;c.getContext('2d').putImageData(new ImageData(pixels,w,h),0,0);
      ['left','right','top','bottom'].forEach((key,i)=>$(key+axis).textContent=display.edges[i]);
      const svg=$('scale'+axis);svg.setAttribute('viewBox',`0 0 ${w} 20`);
      svg.innerHTML='<line x1="20" y1="12" x2="70" y2="12" stroke="currentColor" stroke-width="3"/>';
      const world=manifest.volumes.MRI.voxelToSourceWorld[axis][axis]*ijk[axis]+manifest.volumes.MRI.voxelToSourceWorld[axis][3];
      $('axes'+axis).textContent=`Source ${'ijk'[axis]} = ${ijk[axis]} · ${'RAS'[axis]} = ${world.toFixed(2)} mm`;
      $('slice'+axis).value=ijk[axis];
    }
    document.body.dataset.planesReady=String(code);$('status').textContent=`Source region ${code}: ${mode==='mri'?'MRI':'segmentation schematic'} planes verified.`;
  }catch(e){if(generation===planeGeneration&&!signal.aborted){clearPlanes();$('status').textContent='Planes unavailable: '+e.message+'. Use Retry.';}}
}
const canvas=$('mesh'),gl=canvas.getContext('webgl2',{preserveDrawingBuffer:true,antialias:true});
let program,uniforms,attribute,contextEpoch=0;
function setupGL(){
  const shaders=[ [gl.VERTEX_SHADER,`#version 300 es
in vec3 position;uniform vec3 center;uniform float radius,yaw,pitch,aspect;out vec3 p;
void main(){vec3 q=position-center,b=vec3(q.x,q.z,-q.y);float c=cos(yaw),s=sin(yaw),a=cos(pitch),d=sin(pitch);vec3 r=vec3(c*b.x+s*b.z,b.y,-s*b.x+c*b.z);p=vec3(r.x,a*r.y-d*r.z,d*r.y+a*r.z);gl_Position=vec4(p.x/(radius*aspect),p.y/radius,-p.z/(4.0*radius),1.0);}`], [gl.FRAGMENT_SHADER,`#version 300 es
precision highp float;in vec3 p;out vec4 color;
void main(){vec3 n=normalize(cross(dFdx(p),dFdy(p)));float light=.48+.52*abs(dot(n,normalize(vec3(.3,.5,1.0))));color=vec4(vec3(.14,.55,.59)*light,1.0);}`]];
  program=gl.createProgram();for(const [type,text]of shaders){const s=gl.createShader(type);gl.shaderSource(s,text);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('3D shader unavailable');gl.attachShader(program,s);gl.deleteShader(s);}
  gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('3D program unavailable');
  uniforms=Object.fromEntries(['center','radius','yaw','pitch','aspect'].map(k=>[k,gl.getUniformLocation(program,k)]));attribute=gl.getAttribLocation(program,'position');
}
// A restored WebGL context owns new resources; stale decode cleanup must not
// delete opaque buffer handles from an invalidated context.
function release(m){if(m&&m.contextEpoch===contextEpoch&&!gl.isContextLost()){gl.deleteBuffer(m.positions);gl.deleteBuffer(m.indices);}}
function clearMesh(){if(gl){gl.clearColor(.965,.949,.906,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);}}
function draw(){
  if(!gl||!gpu||gl.isContextLost())return;
  const [lo,hi]=gpu.boundsSourceWorld,center=lo.map((n,i)=>(n+hi[i])/2);
  const radius=Math.hypot(...lo.map((n,i)=>(hi[i]-n)/2))*1.12/state.zoom;
  gl.useProgram(program);gl.viewport(0,0,canvas.width,canvas.height);clearMesh();gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);
  gl.uniform3fv(uniforms.center,center);gl.uniform1f(uniforms.radius,radius);gl.uniform1f(uniforms.yaw,state.yaw);gl.uniform1f(uniforms.pitch,state.pitch);gl.uniform1f(uniforms.aspect,canvas.width/canvas.height);
  gl.bindBuffer(gl.ARRAY_BUFFER,gpu.positions);gl.vertexAttribPointer(attribute,3,gl.FLOAT,false,0,0);gl.enableVertexAttribArray(attribute);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gpu.indices);gl.drawElements(gl.TRIANGLES,gpu.triangles*3,gl.UNSIGNED_INT,0);
  if(gl.getError()!==gl.NO_ERROR)throw Error('3D draw failed');
  const ctx=$('orientation').getContext('2d');ctx.clearRect(0,0,160,150);ctx.font='bold 15px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';
  for(const [vector,name,color]of [[[1,0,0],'R','#a33'],[[0,1,0],'A','#176c43'],[[0,0,1],'S','#275bba']]){
    const b=[vector[0],vector[2],-vector[1]],c=Math.cos(state.yaw),s=Math.sin(state.yaw),a=Math.cos(state.pitch),d=Math.sin(state.pitch);
    const r=[c*b[0]+s*b[2],b[1],-s*b[0]+c*b[2]],x=r[0],y=a*r[1]-d*r[2];
    ctx.strokeStyle=ctx.fillStyle=color;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(80,75);ctx.lineTo(80+45*x,75-45*y);ctx.stroke();ctx.fillText(name,80+60*x,75-60*y);
  }
  $('mesh-scale').textContent=`Orthographic frame height: ${(radius*2).toFixed(1)} mm in source coordinates. ${state.zoom>1?'Zoomed view may crop source geometry.':'Complete model fits within the view.'}`;
}
async function loadMesh(){
  meshController?.abort();meshController=new AbortController();const signal=meshController.signal,generation=++meshGeneration,code=state.code;
  delete document.body.dataset.meshReady;release(gpu);gpu=null;clearMesh();
  if(!gl||gl.isContextLost()){$('mesh-status').textContent='3D requires WebGL 2. MRI and schematics remain available.';return;}
  const row=manifest.meshParts[code],pending={...row,code,contextEpoch,positions:gl.createBuffer(),indices:gl.createBuffer()};
  $('mesh-status').textContent=`Loading source region ${code} in bounded chunks…`;
  try{
    for(const [kind,target]of [['positions',gl.ARRAY_BUFFER],['indices',gl.ELEMENT_ARRAY_BUFFER]]){
      const group=row.parts[kind];gl.bindBuffer(target,pending[kind]);gl.bufferData(target,group.bytes,gl.STATIC_DRAW);
      if(gl.getError()!==gl.NO_ERROR)throw Error('Insufficient 3D memory');
      for(const part of group.chunks){
        const packed=await payload(config.blobPrefix,part.file,{bytes:part.gzipBytes,sha256:part.gzipSHA256},null,signal);
        const raw=await decode(packed,part.bytes,part.sha256);
        if(signal.aborted||generation!==meshGeneration)throw new DOMException('Superseded','AbortError');
        gl.bindBuffer(target,pending[kind]);gl.bufferSubData(target,part.offset,raw);
        if(gl.getError()!==gl.NO_ERROR)throw Error('3D buffer upload failed');
      }
    }
    if(signal.aborted||generation!==meshGeneration)throw new DOMException('Superseded','AbortError');
    gpu=pending;draw();document.body.dataset.meshReady=String(code);
    $('mesh-status').textContent=`Region ${code}: ${row.triangles.toLocaleString()} source triangles; all ${selected().components26.length.toLocaleString()} components retained.`;
  }catch(e){release(pending);if(generation===meshGeneration&&!signal.aborted){gpu=null;clearMesh();$('mesh-status').textContent='3D unavailable: '+e.message+'. Use Retry.';}}
}
function focus(){const component=selected().components26[Number($('component').value)];state.ijk=component.focusSourceIJK.map((n,i)=>n+manifest.annotationCrop.offsetMRIijk[i]);renderPlanes();}
function choose(){
  state.code=Number($('structure').value);const row=selected();$('component').replaceChildren();
  row.components26.forEach((c,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${i+1}: ${c.voxels.toLocaleString()} cells`; $('component').append(option);});
  $('meaning').textContent=`Source code ${row.code} · original LUT name: ${row.rawLUTName} · ${row.voxels.toLocaleString()} labelled cells. Selection names do not resolve the source laterality conflict.`;
  state.zoom=1;$('zoom').value=1;focus();loadMesh();
}
$('structure').onchange=choose;$('component').onchange=focus;
for(const id of ['display','overlay','outline','low','high'])$(id).onchange=renderPlanes;
$('retry').onclick=()=>{if(manifest){renderPlanes();loadMesh();}else initialize();};
$('enlarge').onclick=()=>{document.body.classList.toggle('enlarged');$('enlarge').textContent=document.body.classList.contains('enlarged')?'Fit planes':'Enlarge planes';};
function rotate(y,p){state.yaw+=y;state.pitch=Math.max(-1.5,Math.min(1.5,state.pitch+p));draw();}
$('left').onclick=()=>rotate(-.2,0);$('right').onclick=()=>rotate(.2,0);$('up').onclick=()=>rotate(0,.2);$('down').onclick=()=>rotate(0,-.2);
$('reset').onclick=()=>{state.yaw=2.65;state.pitch=.25;state.zoom=1;$('zoom').value=1;draw();};$('zoom').oninput=()=>{state.zoom=Number($('zoom').value);draw();};
let drag;canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(drag){rotate((e.clientX-drag[0])*.008,(e.clientY-drag[1])*.008);drag=[e.clientX,e.clientY];}};canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};
canvas.onkeydown=e=>{const v={ArrowLeft:[-.2,0],ArrowRight:[.2,0],ArrowUp:[0,.2],ArrowDown:[0,-.2]}[e.key];if(v){e.preventDefault();rotate(...v);}};
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();contextEpoch++;meshController?.abort();++meshGeneration;gpu=null;delete document.body.dataset.meshReady;$('mesh-status').textContent='3D context lost. Waiting for recovery.';});
canvas.addEventListener('webglcontextrestored',()=>{try{setupGL();loadMesh();}catch(e){$('mesh-status').textContent=e.message;}});
async function jsonFile(name,hash){const response=await fetch(name,{credentials:'same-origin'});if(!response.ok)throw Error('Metadata unavailable');const bytes=await response.arrayBuffer();if(hash&&await sha(bytes)!==hash)throw Error('Metadata identity differs');return JSON.parse(new TextDecoder().decode(bytes));}
async function initialize(){try{
  $('retry').disabled=true;config=await jsonFile('config.json');
  const [m,l]=await Promise.all([jsonFile('manifest.json',config.manifestSHA256),jsonFile('labels.json',config.labelsSHA256)]);
  if(m.dataset!=='ds005422'||m.version!=='1.0.1'||m.clinicalApproval!==false||l.classes.length!==98)throw Error('Unexpected source scope');
  manifest=m;labels=l;$('structure').replaceChildren();for(const row of labels.classes){const option=document.createElement('option');option.value=row.code;option.textContent=`${row.code} · ${row.displayName}`;$('structure').append(option);}
  for(let a=0;a<3;a++)$('slice'+a).max=manifest.volumes.MRI.shape[a]-1;
  $('structure').value=state.code;$('structure').disabled=$('component').disabled=false;
  if(gl)try{setupGL();}catch(e){$('mesh-status').textContent=e.message;}
  choose();
}catch(e){$('status').textContent='Source reader unavailable: '+e.message+'. Use Retry.';}finally{$('retry').disabled=false;}}
// Inspection hook exposes the actual buffers and state used for display.
window.NextBrainReader={state,plane,draw,get manifest(){return manifest;},get labels(){return labels;},get gpu(){return gpu;},gl};
initialize();

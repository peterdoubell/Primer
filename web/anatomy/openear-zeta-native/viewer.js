import {sha, decode, payload} from './transport.js';
const $=id=>document.getElementById(id),state={code:4,ijk:[0,0,0],yaw:2.65,pitch:.25,zoom:1};
let manifest,config,planeController,meshController,planeGeneration=0,meshGeneration=0,gpu,contextEpoch=0;
const panels=[['xy',2],['xz',1],['yz',0]],littleEndian=new Uint8Array(new Uint16Array([1]).buffer)[0]===1;
for(const[name,axis]of panels){
 const section=document.createElement('section');section.innerHTML=`<h2>Source ${name.toUpperCase()} plane</h2><label>Source ${'ijk'[axis]}<input type="range" id="slice${axis}" min="0" step="1"></label><div class="viewport" tabindex="0"><div class="plane-image"><div class="orientation-row" id="top${axis}"></div><div class="plane-mid"><span id="left${axis}"></span><canvas id="plane${axis}" role="img" aria-label="Source ${name.toUpperCase()} plane"></canvas><span id="right${axis}"></span></div><div class="orientation-row" id="bottom${axis}"></div></div></div><div class="scale"><span class="scale-line" id="scale${axis}"></span><span id="scale-label${axis}"></span></div><p id="axes${axis}"></p>`;$('panels').append(section);$('slice'+axis).oninput=()=>{state.ijk[axis]=Number($('slice'+axis).value);renderPlanes();};
}
function selected(){return manifest.selections.find(r=>r.code===state.code);}
function values(bytes,dtype){const Type=dtype==='<i2'?Int16Array:Uint16Array;if(littleEndian)return new Type(bytes.buffer,bytes.byteOffset,bytes.byteLength/2);const out=new Type(bytes.byteLength/2),v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);for(let i=0;i<out.length;i++)out[i]=dtype==='<i2'?v.getInt16(2*i,true):v.getUint16(2*i,true);return out;}
async function plane(volume,axis,index,signal){const v=manifest.volumes[volume],row=v.planes[axis][index],packed=await payload(config.blobPrefix,row.file,manifest.packs[row.file],row,signal),bytes=await decode(packed,row.decodedBytes,row.decodedSHA256);return{row,bytes,values:values(bytes,v.dtype)};}
function clearPlanes(){for(const[,a]of panels){const c=$('plane'+a);c.getContext('2d').clearRect(0,0,c.width,c.height);$('axes'+a).textContent='';}}
function scaleAndFocus(center=false){
 const zoom=Number($('magnification').value);
 for(const[name,a]of panels){const c=$('plane'+a),wrap=c.closest('.plane-image'),viewport=c.closest('.viewport');wrap.style.width=zoom?`${c.width*zoom+56}px`:'100%';const ratio=c.getBoundingClientRect().width/c.width,mm=zoom===4?1:zoom===2?2:zoom===1?5:10;$('scale'+a).style.width=`${mm/.125*ratio}px`;$('scale'+a).dataset.sourcePixels=String(mm/.125);$('scale-label'+a).textContent=`${mm} mm`;
  if(center&&manifest){const row=manifest.displayPlanes[name],x=state.ijk[row.sourceAxes[0]],y=state.ijk[row.sourceAxes[1]],dx=row.flipX?c.width-1-x:x,dy=row.flipY?c.height-1-y:y,rect=c.getBoundingClientRect(),view=viewport.getBoundingClientRect();viewport.scrollLeft+=rect.left-view.left+(dx+.5)*ratio-viewport.clientWidth/2;viewport.scrollTop+=rect.top-view.top+(dy+.5)*ratio-viewport.clientHeight/2;}
 }
}
new ResizeObserver(()=>scaleAndFocus()).observe($('panels'));
function updateControls(){const schematic=$('display').value==='schematic';for(const id of ['contrast','low','high','overlay'])$(id).disabled=schematic;$('context').disabled=!schematic;}
async function renderPlanes(){
 if(!manifest)return;updateControls();planeController?.abort();planeController=new AbortController();const signal=planeController.signal,generation=++planeGeneration;delete document.body.dataset.planesReady;clearPlanes();$('status').textContent='Loading source planes…';
 const ijk=[...state.ijk],code=state.code,mode=$('display').value,contrast=$('contrast').value,overlay=$('overlay').checked,outline=$('outline').checked,context=$('context').checked,overlaps=$('overlaps').checked,low=Number($('low').value),high=Number($('high').value);
 if(mode==='cbct'&&($('low').value.trim()===''||$('high').value.trim()===''||!Number.isFinite(low)||!Number.isFinite(high)||!Number.isFinite(high-low)||low>=high)){$('status').textContent='Choose a finite display window with low below high.';return;}
 try{const result=await Promise.all(panels.map(async([name,axis])=>{const[image,mask]=await Promise.all([mode==='cbct'?plane(contrast,axis,ijk[axis],signal):null,plane('masks',axis,ijk[axis],signal)]),[w,h]=mask.row.shape,display=manifest.displayPlanes[name],pixels=new Uint8ClampedArray(w*h*4),flag=1<<code;
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=x+w*y,value=mask.values[i],hit=(value&flag)!==0,original=value&8191,multiple=(original&(original-1))!==0,edge=hit&&(x===0||y===0||x===w-1||y===h-1||!(mask.values[i-1]&flag)||!(mask.values[i+1]&flag)||!(mask.values[i-w]&flag)||!(mask.values[i+w]&flag)),dx=display.flipX?w-1-x:x,dy=display.flipY?h-1-y:y,k=4*(dx+w*dy);const grey=mode==='cbct'?Math.round(255*Math.max(0,Math.min(1,(image.values[i]-low)/(high-low)))):context&&value?100:20;pixels[k]=pixels[k+1]=pixels[k+2]=grey;pixels[k+3]=255;if((mode==='schematic'||overlay)&&hit&&(!outline||edge)){pixels[k]=20;pixels[k+1]=180;pixels[k+2]=175;}if(overlaps&&multiple){pixels[k]=245;pixels[k+1]=145;pixels[k+2]=45;}}
   return{axis,w,h,pixels,display};}));
  if(signal.aborted||generation!==planeGeneration)return;
  for(const{axis,w,h,pixels,display}of result){const c=$('plane'+axis);c.width=w;c.height=h;c.getContext('2d').putImageData(new ImageData(pixels,w,h),0,0);['left','right','top','bottom'].forEach((key,i)=>$(key+axis).textContent=display.edges[i]);const A=manifest.volumes.unembedded.voxelToSourceWorld,world=A[axis][axis]*ijk[axis]+A[axis][3];$('axes'+axis).textContent=`Source ${'ijk'[axis]} = ${ijk[axis]} · ${'XYZ'[axis]} = ${world.toFixed(3)} mm`;$('slice'+axis).value=ijk[axis];}
  scaleAndFocus(true);document.body.dataset.planesReady=String(code);$('status').textContent=`${selected().name}: ${mode==='cbct'?contrast+' CBCT':'mask schematic'} source planes verified.`;
 }catch(e){if(generation===planeGeneration&&!signal.aborted){clearPlanes();$('status').textContent='Planes unavailable: '+e.message+'. Use Retry.';}}
}
const canvas=$('mesh'),gl=canvas.getContext('webgl2',{preserveDrawingBuffer:true,antialias:true});
let program,uniforms,attribute;
function setupGL(){
  const shaders=[ [gl.VERTEX_SHADER,`#version 300 es
in vec3 position;uniform vec3 center;uniform float radius,yaw,pitch,aspect;out vec3 p;
void main(){vec3 q=position-center,b=vec3(q.x,q.z,-q.y);float c=cos(yaw),s=sin(yaw),a=cos(pitch),d=sin(pitch);vec3 r=vec3(c*b.x+s*b.z,b.y,-s*b.x+c*b.z);p=vec3(r.x,a*r.y-d*r.z,d*r.y+a*r.z);gl_Position=vec4(p.x/(radius*aspect),p.y/radius,-p.z/(4.0*radius),1.0);}`], [gl.FRAGMENT_SHADER,`#version 300 es
precision highp float;in vec3 p;out vec4 color;
void main(){vec3 n=normalize(cross(dFdx(p),dFdy(p)));float light=.48+.52*abs(dot(n,normalize(vec3(.3,.5,1.0))));color=vec4(vec3(.57,.66,.68)*light,1.0);}`]];
  program=gl.createProgram();for(const [type,text]of shaders){const s=gl.createShader(type);gl.shaderSource(s,text);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('3D shader unavailable');gl.attachShader(program,s);gl.deleteShader(s);}
  gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('3D program unavailable');
  uniforms=Object.fromEntries(['center','radius','yaw','pitch','aspect'].map(k=>[k,gl.getUniformLocation(program,k)]));attribute=gl.getAttribLocation(program,'position');
}
function release(m){if(m&&gl&&!gl.isContextLost()&&m.contextEpoch===contextEpoch){gl.deleteBuffer(m.positions);gl.deleteBuffer(m.indices);}}
function clearMesh(){if(gl&&!gl.isContextLost()){gl.clearColor(.965,.949,.906,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);}}
function draw(){
  if(!gl||!gpu||gl.isContextLost()||gpu.contextEpoch!==contextEpoch)return;
  const [lo,hi]=gpu.boundsSourceWorld,center=lo.map((n,i)=>(n+hi[i])/2);
  const radius=Math.hypot(...lo.map((n,i)=>(hi[i]-n)/2))*1.12/state.zoom;
  gl.useProgram(program);gl.viewport(0,0,canvas.width,canvas.height);clearMesh();gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);
  gl.uniform3fv(uniforms.center,center);gl.uniform1f(uniforms.radius,radius);gl.uniform1f(uniforms.yaw,state.yaw);gl.uniform1f(uniforms.pitch,state.pitch);gl.uniform1f(uniforms.aspect,canvas.width/canvas.height);
  gl.bindBuffer(gl.ARRAY_BUFFER,gpu.positions);gl.vertexAttribPointer(attribute,3,gl.FLOAT,false,0,0);gl.enableVertexAttribArray(attribute);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gpu.indices);gl.drawElements(gl.TRIANGLES,gpu.triangles*3,gl.UNSIGNED_INT,0);
  if(gl.getError()!==gl.NO_ERROR)throw Error('3D draw failed');
  const ctx=$('orientation').getContext('2d');ctx.clearRect(0,0,160,150);ctx.font='bold 15px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';
  for(const [vector,name,color]of [[[1,0,0],'X','#a33'],[[0,1,0],'Y','#176c43'],[[0,0,1],'Z','#275bba']]){
    const b=[vector[0],vector[2],-vector[1]],c=Math.cos(state.yaw),s=Math.sin(state.yaw),a=Math.cos(state.pitch),d=Math.sin(state.pitch);
    const r=[c*b[0]+s*b[2],b[1],-s*b[0]+c*b[2]],x=r[0],y=a*r[1]-d*r[2];
    ctx.strokeStyle=ctx.fillStyle=color;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(80,75);ctx.lineTo(80+45*x,75-45*y);ctx.stroke();ctx.fillText(name,80+60*x,75-60*y);
  }
  $('mesh-scale').textContent=`Orthographic frame height: ${(radius*2).toFixed(1)} mm in source coordinates. ${state.zoom>1?'Zoomed view may crop source geometry.':'Complete model fits within the view.'}`;
}
async function loadMesh(){
  meshController?.abort();meshController=new AbortController();const signal=meshController.signal,generation=++meshGeneration,code=state.code;
  delete document.body.dataset.meshReady;release(gpu);gpu=null;clearMesh();
  if(!gl||gl.isContextLost()){$('mesh-status').textContent='3D requires WebGL 2. CBCT and schematics remain available.';return;}
  const meshId=selected().meshId,row=manifest.meshes[meshId],pending={...row,code,meshId,contextEpoch,positions:gl.createBuffer(),indices:gl.createBuffer()};
  $('mesh-status').textContent=`Loading source region ${code} in bounded chunks…`;
  try{
    for(const [kind,target]of [['positions',gl.ARRAY_BUFFER],['indices',gl.ELEMENT_ARRAY_BUFFER]]){
      const group=row.parts[kind];gl.bindBuffer(target,pending[kind]);gl.bufferData(target,group.bytes,gl.STATIC_DRAW);
      if(gl.getError()!==gl.NO_ERROR)throw Error('Insufficient 3D memory');
      for(const part of group.chunks){
        const packed=await payload(config.blobPrefix,part.file,{bytes:part.gzipBytes,sha256:part.gzipSHA256},null,signal);
        const raw=await decode(packed,part.bytes,part.sha256);
        if(signal.aborted||generation!==meshGeneration||gl.isContextLost()||pending.contextEpoch!==contextEpoch)throw new DOMException('Superseded','AbortError');
        gl.bindBuffer(target,pending[kind]);gl.bufferSubData(target,part.offset,raw);
        if(gl.getError()!==gl.NO_ERROR)throw Error('3D buffer upload failed');
      }
    }
    if(signal.aborted||generation!==meshGeneration||gl.isContextLost()||pending.contextEpoch!==contextEpoch)throw new DOMException('Superseded','AbortError');
    gpu=pending;draw();document.body.dataset.meshReady=String(code);
    $('mesh-status').textContent=`Region ${code}: ${row.triangles.toLocaleString()} original triangles · ${row.name}. Mask components and author surfaces can differ.`;
  }catch(e){release(pending);if(generation===meshGeneration&&!signal.aborted){gpu=null;clearMesh();$('mesh-status').textContent='3D unavailable: '+e.message+'. Use Retry.';}}
}
function focus(){if(!manifest)return;const row=selected().components26[Number($('component').value)];state.ijk=[...row.focusMRIijk];renderPlanes();}
function choose(){state.code=Number($('structure').value);const row=selected();$('component').replaceChildren();row.components26.forEach((c,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${i+1}: ${c.voxels.toLocaleString()} source cells`;$('component').append(option);});$('meaning').textContent=`${row.name}. ${row.voxels.toLocaleString()} source cells in ${row.components26.length} component(s). Coverage: ${row.sourceCoverage}. The 3D view retains the complete original author surface, which may extend beyond a cropped mask and can differ from its small islands.`;state.zoom=1;$('zoom').value=1;focus();loadMesh();}
$('structure').onchange=choose;$('component').onchange=focus;$('focus').onclick=focus;
for(const id of ['display','overlay','outline','context','overlaps','low','high'])$(id).onchange=renderPlanes;
$('contrast').onchange=()=>{const window=$('contrast').value==='embedded'?[-1300,3300]:[-1000,2600];$('low').value=window[0];$('high').value=window[1];renderPlanes();};
$('magnification').onchange=()=>scaleAndFocus(true);$('retry').onclick=()=>{if(manifest){renderPlanes();loadMesh();}else initialize();};
function rotate(y,p){state.yaw+=y;state.pitch=Math.max(-1.5,Math.min(1.5,state.pitch+p));draw();}
$('left').onclick=()=>rotate(-.2,0);$('right').onclick=()=>rotate(.2,0);$('up').onclick=()=>rotate(0,.2);$('down').onclick=()=>rotate(0,-.2);
$('reset').onclick=()=>{state.yaw=2.65;state.pitch=.25;state.zoom=1;$('zoom').value=1;draw();};$('zoom').oninput=()=>{state.zoom=Number($('zoom').value);draw();};
let drag;canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(drag){rotate((e.clientX-drag[0])*.008,(e.clientY-drag[1])*.008);drag=[e.clientX,e.clientY];}};canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};canvas.onkeydown=e=>{const v={ArrowLeft:[-.2,0],ArrowRight:[.2,0],ArrowUp:[0,.2],ArrowDown:[0,-.2]}[e.key];if(v){e.preventDefault();rotate(...v);}};
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();++contextEpoch;meshController?.abort();++meshGeneration;gpu=null;delete document.body.dataset.meshReady;$('mesh-status').textContent='3D context lost. Waiting for recovery.';});canvas.addEventListener('webglcontextrestored',()=>{try{setupGL();loadMesh();}catch(e){$('mesh-status').textContent=e.message;}});
async function jsonFile(name,hash){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);try{const response=await fetch(name,{credentials:'same-origin',signal:controller.signal});if(!response.ok)throw Error('Metadata unavailable');const bytes=await response.arrayBuffer();if(hash&&await sha(bytes)!==hash)throw Error('Metadata identity differs');return JSON.parse(new TextDecoder().decode(bytes));}finally{clearTimeout(timer);}}
async function initialize(){try{$('retry').disabled=true;config=await jsonFile('config.json');const m=await jsonFile('manifest.json',config.manifestSHA256);if(m.schemaVersion!==1||m.record!==1473724||m.dataset!=='OpenEar ZETA'||m.license!=='CC BY 4.0'||m.clinicalApproval!==false||m.effectiveSpatialResolutionEstablished!==false||m.selections.length!==14||m.sourceMeshCount!==13)throw Error('Unexpected source scope');manifest=m;$('structure').replaceChildren();for(const row of manifest.selections){const option=document.createElement('option');option.value=row.code;option.textContent=row.name;$('structure').append(option);}for(let a=0;a<3;a++)$('slice'+a).max=manifest.volumes.unembedded.shape[a]-1;$('structure').value=state.code;$('structure').disabled=$('component').disabled=$('focus').disabled=false;if(gl)try{setupGL();}catch(e){$('mesh-status').textContent=e.message;}choose();}catch(e){$('status').textContent='Source reader unavailable: '+e.message+'. Use Retry.';}finally{$('retry').disabled=false;}}
window.OpenEarReader={state,plane,draw,get manifest(){return manifest;},get gpu(){return gpu;},gl};
initialize();

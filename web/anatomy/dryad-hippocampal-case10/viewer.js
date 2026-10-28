import {sha,decode,payload} from './transport.js';
const $=id=>document.getElementById(id),state={code:3,ijk:[164,192,56],yaw:.3,pitch:.2,zoom:1};
let manifest,config,planeController,meshController,planeGeneration=0,meshGeneration=0,contextEpoch=0,gpu;
const colours=[[0,0,0],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[174,0,255],[190,112,38],[0,255,255]],axes=[2,1,0];
const rater=()=>$('rater').value,volume=()=>manifest.volumes[$('image').value];
const spacing=(v,axis)=>Math.hypot(...v.affine.slice(0,3).map(row=>row[axis]));
for(const axis of axes){
 const section=document.createElement('section');section.innerHTML=`<h2>Native ${'ijk'[axis]} plane</h2><label>Slice <input id="slice${axis}" type="range" min="0" step="1"></label><div class="viewport" tabindex="0"><div class="plane-container"><canvas id="plane${axis}" role="img" aria-label="Native MRI plane"></canvas><canvas class="crosshair" id="cross${axis}" aria-hidden="true"></canvas></div></div><p class="axis-label" id="axes${axis}"></p><p class="scale" id="scale${axis}"></p>`;$('panels').append(section);
 $('slice'+axis).oninput=()=>{state.ijk[axis]=Number($('slice'+axis).value);renderPlanes();};
 $('plane'+axis).onclick=e=>{if(!manifest||!document.body.dataset.planesReady)return;const group=volume().planes[axis],rect=e.currentTarget.getBoundingClientRect();state.ijk[group.uAxis]=Math.max(0,Math.min(group.width-1,Math.floor((e.clientX-rect.left)/rect.width*group.width)));state.ijk[group.vAxis]=Math.max(0,Math.min(group.height-1,group.height-1-Math.floor((e.clientY-rect.top)/rect.height*group.height)));renderPlanes();};
}
function directionLabel(v,axis,positive){const column=v.affine.slice(0,3).map(row=>row[axis]),dominant=column.map(Math.abs).indexOf(Math.max(...column.map(Math.abs))),names=[['L','R'],['P','A'],['I','S']];return names[dominant][column[dominant]*(positive?1:-1)>0?1:0];}
function values(bytes,dtype){const n=bytes.byteLength/2,out=dtype==='<i2'?new Int16Array(n):new Uint16Array(n),view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);for(let i=0;i<n;i++)out[i]=dtype==='<i2'?view.getInt16(i*2,true):view.getUint16(i*2,true);return out;}
async function plane(key,axis,index,signal){const v=manifest.volumes[key],group=v.planes[axis],row=group.rows[index],packed=await payload(config.blobPrefix,row.pack,manifest.packs[row.pack],row,signal),raw=await decode(packed,row.bytes,row.sha256);return{group,row,raw,values:values(raw,v.dtype)};}
function clearPlanes(){for(const a of axes)for(const id of ['plane','cross']){const c=$(id+a);c.getContext('2d').clearRect(0,0,c.width,c.height);}}
function scaleImages(center=false){if(!manifest)return;const zoom=Number($('magnification').value);for(const a of axes){const canvas=$('plane'+a),group=volume().planes[a],container=canvas.parentElement,viewport=container.parentElement,ratio=spacing(volume(),group.vAxis)/spacing(volume(),group.uAxis);container.style.width=zoom?`${group.width*zoom}px`:'100%';container.style.aspectRatio=String(group.width/(group.height*ratio));for(const c of container.querySelectorAll('canvas')){c.style.width='100%';c.style.height='100%';}const rect=canvas.getBoundingClientRect();$('scale'+a).textContent=`Grid spacing: ${spacing(volume(),group.uAxis).toFixed(4)} × ${spacing(volume(),group.vAxis).toFixed(4)} mm. Both screen directions use the same millimetre scale.`;if(center){const view=viewport.getBoundingClientRect();viewport.scrollLeft+=rect.left-view.left+(state.ijk[group.uAxis]+.5)*rect.width/group.width-viewport.clientWidth/2;viewport.scrollTop+=rect.top-view.top+(group.height-state.ijk[group.vAxis]-.5)*rect.height/group.height-viewport.clientHeight/2;}}}
new ResizeObserver(()=>scaleImages()).observe($('panels'));
async function renderPlanes(){
 if(!manifest)return;planeController?.abort();planeController=new AbortController();const signal=planeController.signal,generation=++planeGeneration;delete document.body.dataset.planesReady;clearPlanes();
 const ijk=[...state.ijk],image=$('image').value,annotation=rater(),code=state.code,mode=$('display').value,low=Number($('low').value),high=Number($('high').value);$('low').disabled=$('high').disabled=mode==='schematic';
 if(mode!=='schematic'&&(!$('low').value.trim()||!$('high').value.trim()||!Number.isFinite(low)||!Number.isFinite(high)||!Number.isFinite(high-low)||low>=high)){$('status').textContent='Enter a finite intensity window with low below high. No stale image is displayed.';return;}
 $('status').textContent='Loading verified source planes…';
 try{
  const results=await Promise.all(axes.map(async axis=>{
   const [scan,main,second]=await Promise.all([mode==='schematic'?null:plane(image,axis,ijk[axis],signal),plane('primary',axis,ijk[axis],signal),plane('second',axis,ijk[axis],signal)]),group=main.group,w=group.width,h=group.height,pixels=new Uint8ClampedArray(w*h*4),labels=annotation==='primary'?main.values:second.values,v=manifest.volumes[image];
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const i=x+w*y,k=4*(x+w*(h-1-y)),label=labels[i];let grey=mode==='schematic'?(label?90:15):Math.round(255*Math.max(0,Math.min(1,(scan.values[i]*v.slope+v.intercept-low)/(high-low))));let rgb=[grey,grey,grey];
    if((mode==='overlay'||mode==='schematic')&&label===code)rgb=colours[code].map(c=>Math.round(.55*c+.45*grey));
    if(mode==='difference'&&main.values[i]!==second.values[i]){const c=main.values[i]&&second.values[i]?[255,160,0]:main.values[i]?[30,140,240]:[235,80,190];rgb=c.map(v=>Math.round(.7*v+.3*grey));}
    pixels.set([...rgb,255],k);
   }
   const probeIndex=ijk[group.uAxis]+w*ijk[group.vAxis];return{axis,group,pixels,probe:{primary:main.values[probeIndex],second:second.values[probeIndex],intensity:scan?scan.values[probeIndex]*v.slope+v.intercept:null}};
  }));
  if(signal.aborted||generation!==planeGeneration)return;
  for(const{axis,group,pixels}of results){const c=$('plane'+axis),overlay=$('cross'+axis);c.width=overlay.width=group.width;c.height=overlay.height=group.height;c.getContext('2d').putImageData(new ImageData(pixels,group.width,group.height),0,0);c.dataset.ijk=JSON.stringify(ijk);const ctx=overlay.getContext('2d');ctx.strokeStyle='rgba(255,255,255,.7)';ctx.lineWidth=1;const x=ijk[group.uAxis]+.5,y=group.height-ijk[group.vAxis]-.5;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,group.height);ctx.moveTo(0,y);ctx.lineTo(group.width,y);ctx.stroke();$('slice'+axis).value=ijk[axis];const edges=[directionLabel(volume(),group.uAxis,false),directionLabel(volume(),group.uAxis,true),directionLabel(volume(),group.vAxis,true),directionLabel(volume(),group.vAxis,false)];c.dataset.orientation=JSON.stringify(edges);c.setAttribute('aria-label',`${image}, ${mode}, native ${'ijk'[axis]} plane ${ijk[axis]}`);$('axes'+axis).textContent=`${'ijk'[axis]}=${ijk[axis]}. Image edges: left ${edges[0]}, right ${edges[1]}, top ${edges[2]}, bottom ${edges[3]} (source header directions; oblique planes). Click a pixel to move the crosshair.`;}
  const probe=results[0].probe;if(results.some(r=>JSON.stringify(r.probe)!==JSON.stringify(probe)))throw Error('Source planes disagree at crosshair');$('status').dataset.probe=JSON.stringify(probe);const labelName=c=>c?manifest.labelNames[c]:'unlabelled';
  scaleImages(true);document.body.dataset.planesReady=String(generation);$('status').textContent=`${mode==='schematic'?'Source labels':manifest.volumes[image].sourceFile} · voxel (${ijk.join(', ')}) · ${mode}. At crosshair: Main Sample ${labelName(probe.primary)}; Reliability ${labelName(probe.second)}.${probe.intensity===null?'':' MRI intensity '+Number(probe.intensity.toPrecision(6))+' (source units).'} Crosshairs are separate from the original displayed pixels.`;
 }catch(e){if(!signal.aborted&&generation===planeGeneration){clearPlanes();$('status').textContent='Source plane unavailable: '+e.message+'. Use Retry.';}}
}
function updateRegion(){
 if(!manifest)return;
 const v=manifest.volumes[rater()],code=String(state.code),components=v.components[code]||[];$('component').replaceChildren();components.forEach((row,index)=>{const option=document.createElement('option');option.value=index;option.textContent=`${index+1}: ${row.voxels.toLocaleString()} annotated voxels`;$('component').append(option);});$('component').disabled=$('focus').disabled=!components.length;
 const count=v.counts[code]||0;$('meaning').textContent=`${manifest.labelNames[code]} · ${rater()==='primary'?'Main Sample':'Reliability'}: ${count.toLocaleString()} labelled voxels, ${components.length} connected component(s). ${count?'The 3D view contains the complete selected annotation; focusing does not discard components.':'This label is absent from this annotation; no geometry is invented.'}`;
 if(components.length)state.ijk=[...components[0].focusIJK];state.zoom=1;$('zoom').value=1;renderPlanes();loadMesh();
}
function focus(){const component=manifest?.volumes[rater()].components[state.code]?.[Number($('component').value)];if(component){state.ijk=[...component.focusIJK];renderPlanes();draw();}}
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
  const component=manifest.volumes[rater()].components[state.code]?.[Number($('component').value)],focused=$('framing').value==='component'&&component;const [lo,hi]=focused?component.boundsSourceWorld:gpu.boundsSourceWorld,center=lo.map((n,i)=>(n+hi[i])/2);
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
  $('mesh-scale').textContent=`Orthographic frame height: ${(radius*2).toFixed(1)} mm in source coordinates. ${focused?'Selected component frame; other components remain in the model and may lie outside this view.':state.zoom>1?'Zoomed view may crop source geometry.':'Complete model fits within the view.'}`;
}
async function loadMesh(){
 meshController?.abort();meshController=new AbortController();const signal=meshController.signal,generation=++meshGeneration;delete document.body.dataset.meshReady;release(gpu);gpu=null;clearMesh();
 const key=rater()+':'+state.code,row=manifest.meshes[key];if(!row){$('mesh-status').textContent='Selected label absent from this annotation.';document.body.dataset.meshReady='absent';return;}
 if(!gl||gl.isContextLost()){$('mesh-status').textContent='3D requires WebGL 2. MRI, labels and comparisons remain available.';return;}
 const epoch=contextEpoch;let pending;
 try{
  $('mesh-status').textContent='Loading complete source boundary…';const bytes=await payload(config.blobPrefix,row.file,{bytes:row.compressedBytes,sha256:row.compressedSHA256},null,signal),raw=await decode(bytes,row.bytes,row.sha256);if(signal.aborted||generation!==meshGeneration||gl.isContextLost()||epoch!==contextEpoch)return;
  const view=new DataView(raw.buffer,raw.byteOffset,raw.byteLength),magic=String.fromCharCode(...raw.slice(0,4)),nv=view.getUint32(4,true),nt=view.getUint32(8,true);if(magic!=='HVX1'||nv!==row.vertices||nt!==row.triangles||view.getUint32(12,true)!==0||raw.length!==16+nv*12+nt*12)throw Error('Unexpected mesh layout');
  const xyz=new Float32Array(nv*3),indices=new Uint32Array(nt*3);for(let i=0;i<xyz.length;i++)xyz[i]=view.getFloat32(16+i*4,true);for(let i=0;i<indices.length;i++)indices[i]=view.getUint32(16+nv*12+i*4,true);if(xyz.some(x=>!Number.isFinite(x))||indices.some(x=>x>=nv))throw Error('Invalid source geometry');
  const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(let i=0;i<nv;i++)for(let a=0;a<3;a++){lo[a]=Math.min(lo[a],xyz[i*3+a]);hi[a]=Math.max(hi[a],xyz[i*3+a]);}
  pending={key,contextEpoch:epoch,triangles:nt,boundsSourceWorld:[lo,hi],positions:gl.createBuffer(),indices:gl.createBuffer()};gl.bindBuffer(gl.ARRAY_BUFFER,pending.positions);gl.bufferData(gl.ARRAY_BUFFER,xyz,gl.STATIC_DRAW);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,pending.indices);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices,gl.STATIC_DRAW);if(gl.getError()!==gl.NO_ERROR)throw Error('3D upload failed');
  if(signal.aborted||generation!==meshGeneration||gl.isContextLost()||epoch!==contextEpoch){release(pending);return;}gpu=pending;draw();document.body.dataset.meshReady=key;$('mesh-status').textContent=`${nt.toLocaleString()} triangles preserve every exposed face of ${manifest.labelNames[state.code]} in ${rater()==='primary'?'Main Sample':'Reliability'}.`;
 }catch(e){release(pending);if(!signal.aborted&&generation===meshGeneration){gpu=null;clearMesh();$('mesh-status').textContent='3D unavailable: '+e.message+'. Use Retry.';}}
}
$('region').onchange=()=>{state.code=Number($('region').value);updateRegion();};$('rater').onchange=updateRegion;$('component').onchange=focus;$('focus').onclick=focus;
for(const id of ['display','low','high'])$(id).onchange=renderPlanes;
function windowForImage(){const p=volume().scaledNonzeroPercentiles;$('low').value=p[0];$('high').value=p[2];}
$('image').onchange=()=>{if(manifest){windowForImage();renderPlanes();}};$('magnification').onchange=()=>scaleImages(true);$('retry').onclick=()=>{if(manifest){renderPlanes();loadMesh();}else initialize();};
function rotate(y,p){state.yaw+=y;state.pitch=Math.max(-1.5,Math.min(1.5,state.pitch+p));draw();}
$('framing').onchange=draw;
$('left').onclick=()=>rotate(-.2,0);$('right').onclick=()=>rotate(.2,0);$('up').onclick=()=>rotate(0,.2);$('down').onclick=()=>rotate(0,-.2);$('zoom').oninput=()=>{state.zoom=Number($('zoom').value);draw();};$('reset').onclick=()=>{$('framing').value='whole';state.yaw=.3;state.pitch=.2;state.zoom=1;$('zoom').value=1;draw();};
let drag;canvas.onpointerdown=e=>{if(e.button!==0)return;drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(drag){rotate((e.clientX-drag[0])*.008,(e.clientY-drag[1])*.008);drag=[e.clientX,e.clientY];}};canvas.onpointerup=canvas.onpointercancel=canvas.onlostpointercapture=()=>{drag=null;};canvas.onkeydown=e=>{const d={ArrowLeft:[-.2,0],ArrowRight:[.2,0],ArrowUp:[0,.2],ArrowDown:[0,-.2]}[e.key];if(d){e.preventDefault();rotate(...d);}};
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();++contextEpoch;meshController?.abort();++meshGeneration;gpu=null;delete document.body.dataset.meshReady;$('mesh-status').textContent='3D context lost; waiting for recovery.';});canvas.addEventListener('webglcontextrestored',()=>{try{setupGL();loadMesh();}catch(e){$('mesh-status').textContent=e.message;}});
async function jsonFile(name,digest){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);try{const r=await fetch(name,{credentials:'same-origin',signal:controller.signal});if(!r.ok)throw Error('Metadata unavailable');const b=await r.arrayBuffer();if(digest&&await sha(b)!==digest)throw Error('Metadata identity differs');return JSON.parse(new TextDecoder().decode(b));}finally{clearTimeout(timer);}}
async function initialize(){try{$('retry').disabled=true;config=await jsonFile('config.json');const m=await jsonFile('manifest.json',config.manifestSHA256);if(m.schemaVersion!==1||m.sourceDOI!=='10.5061/dryad.2v6wwpzt3'||m.sourceVersion!==7||m.license!=='CC0-1.0'||m.clinicalApproval!==false||m.planeCount!==4944)throw Error('Unexpected source scope');if(typeof m.fullArchiveVerificationPending!=='boolean')throw Error('Missing source-verification status');if(m.fullArchiveVerificationPending!==false&&location.hostname!=='127.0.0.1')throw Error('Source archive verification is pending');manifest=m;for(const [code,name]of Object.entries(m.labelNames)){const o=document.createElement('option');o.value=code;o.textContent=code+': '+name;$('region').append(o);}$('region').value=state.code;for(let a=0;a<3;a++)$('slice'+a).max=m.volumes.mean.shape[a]-1;windowForImage();if(gl)try{setupGL();}catch(e){$('mesh-status').textContent=e.message;}updateRegion();}catch(e){$('status').textContent='Source reader unavailable: '+e.message+'. Use Retry.';}finally{$('retry').disabled=false;}}
window.HippocampalRaterReader={state,plane,renderPlanes,loadMesh,draw,get manifest(){return manifest;},get gpu(){return gpu;},gl};
initialize();

import {payload,decode} from './transport.js';
export function installMesh(manifest){
const $=id=>document.getElementById(id),state={yaw:.3,pitch:.2,zoom:1};let gpu,meshController,meshGeneration=0,contextEpoch=0;
const canvas=$('mesh'),gl=canvas.getContext('webgl2',{preserveDrawingBuffer:true,antialias:true});
let program,uniforms,attribute;
function setupGL(){
  const shaders=[ [gl.VERTEX_SHADER,`#version 300 es
in vec3 position;uniform vec3 center;uniform float radius,yaw,pitch,aspect;out vec3 p;
void main(){vec3 q=position-center,b=vec3(q.x,q.z,-q.y);float c=cos(yaw),s=sin(yaw),a=cos(pitch),d=sin(pitch);vec3 r=vec3(c*b.x+s*b.z,b.y,-s*b.x+c*b.z);p=vec3(r.x,a*r.y-d*r.z,d*r.y+a*r.z);gl_Position=vec4(p.x/(radius*aspect),p.y/radius,-p.z/(4.0*radius),1.0);}`], [gl.FRAGMENT_SHADER,`#version 300 es
precision highp float;in vec3 p;out vec4 color;
void main(){vec3 n=normalize(cross(dFdx(p),dFdy(p)));float light=.48+.52*abs(dot(n,normalize(vec3(.3,.5,1.0))));color=vec4(vec3(1.0,.55,.20)*light,1.0);}`]];
  program=gl.createProgram();for(const [type,text]of shaders){const s=gl.createShader(type);gl.shaderSource(s,text);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('3D shader unavailable');gl.attachShader(program,s);gl.deleteShader(s);}
  gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('3D program unavailable');
  uniforms=Object.fromEntries(['center','radius','yaw','pitch','aspect'].map(k=>[k,gl.getUniformLocation(program,k)]));attribute=gl.getAttribLocation(program,'position');
}
function release(m){if(m&&gl&&!gl.isContextLost()&&m.contextEpoch===contextEpoch){gl.deleteBuffer(m.positions);gl.deleteBuffer(m.indices);}}
function clearMesh(){if(gl&&!gl.isContextLost()){gl.clearColor(.063,.094,.125,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);}}
function draw(){
  if(!gl||!gpu||gl.isContextLost()||gpu.contextEpoch!==contextEpoch)return;
  const focused=false;const [lo,hi]=gpu.boundsSourceWorld,center=lo.map((n,i)=>(n+hi[i])/2);
  const radius=Math.hypot(...lo.map((n,i)=>(hi[i]-n)/2))*1.12/(state.zoom*Math.min(1,canvas.width/canvas.height));
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
 if($('volume').value!=='flair'){$('mesh-status').textContent='The lesion references FLAIR. T1 registration remains unverified.';document.body.dataset.meshReady='unregistered';return;}
 const key='lesion',row=manifest.meshes[key];if(!row){$('mesh-status').textContent='Selected label absent from this annotation.';document.body.dataset.meshReady='absent';return;}
 if(!gl||gl.isContextLost()){$('mesh-status').textContent='3D requires WebGL 2. MRI, labels and comparisons remain available.';return;}
 const epoch=contextEpoch;let pending;
 try{
  $('mesh-status').textContent='Loading complete source boundary…';const bytes=await payload('/payload/',row.file,{bytes:row.compressedBytes,sha256:row.compressedSHA256},null,signal),raw=await decode(bytes,row.bytes,row.sha256);if(signal.aborted||generation!==meshGeneration||gl.isContextLost()||epoch!==contextEpoch)return;
  const view=new DataView(raw.buffer,raw.byteOffset,raw.byteLength),magic=String.fromCharCode(...raw.slice(0,4)),nv=view.getUint32(4,true),nt=view.getUint32(8,true);if(magic!=='HVX1'||nv!==row.vertices||nt!==row.triangles||view.getUint32(12,true)!==0||raw.length!==16+nv*12+nt*12)throw Error('Unexpected mesh layout');
  const xyz=new Float32Array(nv*3),indices=new Uint32Array(nt*3);for(let i=0;i<xyz.length;i++)xyz[i]=view.getFloat32(16+i*4,true);for(let i=0;i<indices.length;i++)indices[i]=view.getUint32(16+nv*12+i*4,true);if(xyz.some(x=>!Number.isFinite(x))||indices.some(x=>x>=nv))throw Error('Invalid source geometry');
  const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(let i=0;i<nv;i++)for(let a=0;a<3;a++){lo[a]=Math.min(lo[a],xyz[i*3+a]);hi[a]=Math.max(hi[a],xyz[i*3+a]);}
  pending={key,contextEpoch:epoch,triangles:nt,boundsSourceWorld:[lo,hi],positions:gl.createBuffer(),indices:gl.createBuffer()};gl.bindBuffer(gl.ARRAY_BUFFER,pending.positions);gl.bufferData(gl.ARRAY_BUFFER,xyz,gl.STATIC_DRAW);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,pending.indices);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices,gl.STATIC_DRAW);if(gl.getError()!==gl.NO_ERROR)throw Error('3D upload failed');
  if(signal.aborted||generation!==meshGeneration||gl.isContextLost()||epoch!==contextEpoch){release(pending);return;}gpu=pending;draw();document.body.dataset.meshReady=key;$('mesh-status').textContent=`${nt.toLocaleString()} triangles preserve every exposed face of the source lesion annotation.`;
 }catch(e){release(pending);if(!signal.aborted&&generation===meshGeneration){gpu=null;clearMesh();$('mesh-status').textContent='3D unavailable: '+e.message+'. Use Retry.';}}
}

function rotate(y,p){state.yaw+=y;state.pitch=Math.max(-1.5,Math.min(1.5,state.pitch+p));draw();}
for(const [id,y,p] of [['left',-.2,0],['right',.2,0],['up',0,.2],['down',0,-.2]])$(id).onclick=()=>rotate(y,p);
$('zoom').oninput=()=>{state.zoom=Number($('zoom').value);draw();};
$('reset').onclick=()=>{state.yaw=.3;state.pitch=.2;state.zoom=1;$('zoom').value=1;draw();};
canvas.onkeydown=e=>{const d={ArrowLeft:[-.2,0],ArrowRight:[.2,0],ArrowUp:[0,.2],ArrowDown:[0,-.2]}[e.key];if(d){e.preventDefault();rotate(...d);}};
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();++contextEpoch;meshController?.abort();++meshGeneration;gpu=null;delete document.body.dataset.meshReady;$('mesh-status').textContent='3D context lost; waiting for recovery.';});
canvas.addEventListener('webglcontextrestored',()=>{try{setupGL();loadMesh();}catch(e){$('mesh-status').textContent=e.message;}});
if(gl)try{setupGL();}catch(error){$('mesh-status').textContent='3D unavailable: '+error.message;return {loadMesh(){},draw(){},gl:null,gpu:null};}
loadMesh();
return {loadMesh,draw,gl,get gpu(){return gpu;}};
}

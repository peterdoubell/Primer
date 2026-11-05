'use strict';
async function loadSurfaces() {
  const canvas = document.querySelector('#surface');
  const status = document.querySelector('#surface-status');
  const gl = canvas.getContext('webgl2', {preserveDrawingBuffer:true});
  if (!gl) {status.textContent='WebGL 2 is required for the surface view.';return;}
  const manifest = await fetch('surfaces.json');
  if (!manifest.ok) throw Error('Missing source manifest');
  const rows = await manifest.json();
  const program = gl.createProgram();
  const shaders = [
    [gl.VERTEX_SHADER, `#version 300 es
    in vec3 position;
    uniform vec3 center;
    uniform float yaw, pitch, radius;
    out vec3 view;
    void main() {
      vec3 p=position-center;
      float x=cos(yaw)*p.x-sin(yaw)*p.y;
      float d=sin(yaw)*p.x+cos(yaw)*p.y;
      view=vec3(x,cos(pitch)*p.z-sin(pitch)*d,sin(pitch)*p.z+cos(pitch)*d);
      gl_Position=vec4(view.x/(radius*4./3.),view.y/radius,-view.z/(2.*radius),1.);
    }`],
    [gl.FRAGMENT_SHADER, `#version 300 es
    precision highp float;
    in vec3 view;
    uniform vec3 tint;
    out vec4 color;
    void main(){vec3 normal=normalize(cross(dFdx(view),dFdy(view)));
      color=vec4(tint*(.5+.5*abs(dot(normal,normalize(vec3(.3,.5,1.))))),1.);}`]
  ];
  for(const [type,source] of shaders){
    const shader=gl.createShader(type);
    gl.shaderSource(shader,source);gl.compileShader(shader);
    if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error('Shader compilation failed');
    gl.attachShader(program,shader);gl.deleteShader(shader);
  }
  gl.linkProgram(program);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Shader link failed');
  gl.useProgram(program);
  const meshes=await Promise.all(rows.map(async row=>{
    const response=await fetch(row.file);
    if(!response.ok)throw Error('Missing surface');
    const bytes=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
    if(digest!==row.sha256 || bytes.byteLength!==12*(row.vertices+row.triangles))throw Error('Surface bytes differ');
    const vao=gl.createVertexArray();gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(bytes,0,3*row.vertices),gl.STATIC_DRAW);
    const attribute=gl.getAttribLocation(program,'position');
    gl.enableVertexAttribArray(attribute);gl.vertexAttribPointer(attribute,3,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gl.createBuffer());
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint32Array(bytes,12*row.vertices),gl.STATIC_DRAW);
    return {vao,row};
  }));
  function fit() {
    const active = meshes.filter((_,i)=>document.querySelectorAll('.layer')[i].checked);
    if (!active.length) return;
    const bounds = active.map(item=>item.row.bounds);
    const low=[0,1,2].map(k=>Math.min(...bounds.map(b=>b[0][k])));
    const high=[0,1,2].map(k=>Math.max(...bounds.map(b=>b[1][k])));
    gl.uniform3fv(gl.getUniformLocation(program,'center'),low.map((v,k)=>(v+high[k])/2));
    gl.uniform1f(gl.getUniformLocation(program,'radius'),.52*Math.hypot(...high.map((v,k)=>v-low[k])));
  }
  const colors=[[242,82,87],[77,171,245],[255,199,61]];
  const layers=Array.from(document.querySelectorAll('.layer'));
  function draw(){
    gl.clearColor(.06,.09,.12,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);
    for(const [id,key] of [['rotation','yaw'],['tilt','pitch']])gl.uniform1f(gl.getUniformLocation(program,key),Number(document.getElementById(id).value)*Math.PI/180);
    let triangles=0;
    meshes.forEach(({vao,row},i)=>{
      if(!layers[i].checked)return;
      gl.uniform3fv(gl.getUniformLocation(program,'tint'),(row.color || colors[i]).map(x=>x/255));
      gl.bindVertexArray(vao);gl.drawElements(gl.TRIANGLES,row.triangles*3,gl.UNSIGNED_INT,0);
      triangles+=row.triangles;
    });
    status.textContent=triangles.toLocaleString()+' source triangles visible';
  }
  fit();
  document.querySelector('#fit').onclick=()=>{fit();draw();};
  document.querySelector('#group').onchange=event=>{
    const group=event.target.value;
    layers.forEach((layer,i)=>{layer.checked=group==='all'||rows[i].source_fma===group;});
    fit();draw();
  };
  for(const control of [...layers,document.querySelector('#rotation'),document.querySelector('#tilt')])control?.addEventListener('input',draw);
  draw();
  document.querySelector('#group').disabled = false;
  document.querySelector('#fit').disabled = false;
  document.querySelector('#pieces').disabled = false;
  document.querySelector('#rotation').disabled = false;
  document.querySelector('#tilt').disabled = false;
}
document.querySelector('#retry').onclick = () => location.reload();
loadSurfaces().catch(error => {
  console.error(error);
  document.querySelector('#surface-status').textContent = 'Source geometry could not be loaded. Retry to reload the verified source files.';
  document.querySelector('#retry').hidden = false;
});

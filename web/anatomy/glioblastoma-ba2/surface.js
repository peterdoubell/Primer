'use strict';
async function loadSurfaces() {
  const canvas = document.querySelector('#surface');
  const status = document.querySelector('#surface-status');
  // Subscribe before fetching meshes so MRI navigation during loading is retained.
  let section = null;
  let redraw = null;
  document.addEventListener('mri-section', event => {
    if (section && section.axis === event.detail.axis && section.coordinate === event.detail.coordinate) return;
    section = event.detail;
    if (redraw && cut.checked) redraw();
  });
  const cut = document.querySelector('#section-cut');
  const gl = canvas.getContext('webgl2', {preserveDrawingBuffer:true});
  if (!gl) {status.textContent='WebGL 2 is required for the surface view.';return;}
  const rows = await (await fetch('surfaces.json')).json();
  const program = gl.createProgram();
  const shaders = [
    [gl.VERTEX_SHADER, `#version 300 es
    in vec3 position;
    uniform vec3 center;
    uniform float yaw, pitch, radius;
    out vec3 view;
    out vec3 world;
    void main() {
      world=position;
      vec3 p=position-center;
      float x=cos(yaw)*p.x-sin(yaw)*p.y;
      float d=sin(yaw)*p.x+cos(yaw)*p.y;
      view=vec3(x,cos(pitch)*p.z-sin(pitch)*d,sin(pitch)*p.z+cos(pitch)*d);
      gl_Position=vec4(view.x/(radius*4./3.),view.y/radius,-view.z/(2.*radius),1.);
    }`],
    [gl.FRAGMENT_SHADER, `#version 300 es
    precision highp float;
    in vec3 view;
    in vec3 world;
    uniform int cutAxis;
    uniform float cutCoordinate;
    uniform vec3 tint;
    out vec4 color;
    void main(){vec3 normal=normalize(cross(dFdx(view),dFdy(view)));
      if(cutAxis >= 0 && world[cutAxis] > cutCoordinate) discard;
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
  const low=[0,1,2].map(k=>Math.min(...rows.map(r=>r.bounds[0][k])));
  const high=[0,1,2].map(k=>Math.max(...rows.map(r=>r.bounds[1][k])));
  gl.uniform3fv(gl.getUniformLocation(program,'center'),low.map((v,k)=>(v+high[k])/2));
  gl.uniform1f(gl.getUniformLocation(program,'radius'),.52*Math.hypot(...high.map((v,k)=>v-low[k])));
  const colors=[[242,82,87],[77,171,245],[255,199,61]];
  const layers=Array.from(document.querySelectorAll('.layer'));
  function draw(){
    gl.clearColor(.06,.09,.12,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);
    for(const [id,key] of [['rotation','yaw'],['tilt','pitch']])gl.uniform1f(gl.getUniformLocation(program,key),Number(document.getElementById(id).value)*Math.PI/180);
    const clipped = cut.checked && section !== null;
    gl.uniform1i(gl.getUniformLocation(program,'cutAxis'),clipped ? section.axis : -1);
    gl.uniform1f(gl.getUniformLocation(program,'cutCoordinate'),clipped ? section.coordinate : 0);
    const axisNames = ['R','A','S'];
    document.querySelector('#cut-info').textContent = clipped
      ? 'Open surfaces at MNI152 ' + axisNames[section.axis] + ' = ' + section.coordinate + ' mm. Showing the ' + ['left','posterior','inferior'][section.axis] + ' side of the plane.'
      : 'Whole surfaces shown.';
    let triangles=0;
    meshes.forEach(({vao,row},i)=>{
      if(!layers[i].checked)return;
      gl.uniform3fv(gl.getUniformLocation(program,'tint'),colors[i].map(x=>x/255));
      gl.bindVertexArray(vao);gl.drawElements(gl.TRIANGLES,row.triangles*3,gl.UNSIGNED_INT,0);
      triangles+=row.triangles;
    });
    status.textContent=triangles.toLocaleString()+(clipped ? ' source triangles before clipping' : ' source triangles visible');
  }
  redraw = draw;
  for(const control of [cut,...layers,document.querySelector('#rotation'),document.querySelector('#tilt')])control.addEventListener('input',draw);
  draw();
}
loadSurfaces().catch(()=>{document.querySelector('#surface-status').textContent='Surface loading failed. Reload to retry.';});

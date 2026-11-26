const vertex = `#version 300 es
in vec3 position;
uniform vec3 center;
uniform vec2 rotation;
uniform vec2 extent;
out vec3 world;
out vec3 view;
void main(){
  world=position;
  vec3 p=position-center;
  float y=rotation.x, t=rotation.y;
  float depth=sin(y)*p.x+cos(y)*p.y;
  view=vec3(cos(y)*p.x-sin(y)*p.y,cos(t)*p.z-sin(t)*depth,sin(t)*p.z+cos(t)*depth);
  gl_Position=vec4(view.x/extent.x,view.y/extent.y,-view.z/(2.0*extent.y),1.0);
}`;
const fragment = `#version 300 es
precision highp float;
in vec3 world;
in vec3 view;
uniform int axis;
uniform float sectionHeight;
uniform bool cutaway;
uniform int material;
out vec4 color;
void main(){
  if(material==1){color=vec4(1.0,.77,.28,1.0);return;}
  if(material==2){color=vec4(.24,.56,.55,1.0);return;}
  if(cutaway && world[axis]>sectionHeight)discard;
  vec3 normal=normalize(cross(dFdx(view),dFdy(view)));
  float shade=.32+.68*max(0.0,dot(normal,normalize(vec3(-.5,.55,.9))));
  color=vec4(vec3(.68,.73,.74)*shade,1.0);
}`;

export function surfaceView(canvas) {
  const gl = canvas.getContext('webgl2', {
    antialias: true,
    stencil: true,
    preserveDrawingBuffer: true
  });
  if (!gl) return null;
  let program,
    position,
    xyz,
    index,
    lines,
    cap,
    count = 0,
    lineCount = 0;
  let state, mesh, section;
  function setup() {
    program = gl.createProgram();
    for (const [type, source] of [
      [gl.VERTEX_SHADER, vertex],
      [gl.FRAGMENT_SHADER, fragment]
    ]) {
      const s = gl.createShader(type);
      gl.shaderSource(s, source);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw Error('Shader could not be compiled.');
      gl.attachShader(program, s);
      gl.deleteShader(s);
    }
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error('Program could not link.');
    position = gl.getAttribLocation(program, 'position');
    xyz = gl.createBuffer();
    index = gl.createBuffer();
    lines = gl.createBuffer();
    cap = gl.createBuffer();
    gl.enable(gl.DEPTH_TEST);
  }
  function setMesh(value) {
    mesh = value;
    count = 0;
    lineCount = 0;
    section = null;
    if (!value || gl.isContextLost()) return;
    gl.bindBuffer(gl.ARRAY_BUFFER, xyz);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.positions), gl.STATIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, mesh.indices, gl.STATIC_DRAW);
    count = mesh.indices.length;
  }
  function setSection(values) {
    section = values;
    lineCount = 0;
    if (!values || gl.isContextLost()) return;
    gl.bindBuffer(gl.ARRAY_BUFFER, lines);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(values), gl.DYNAMIC_DRAW);
    lineCount = values.length / 3;
    // The parity of overlapping fan triangles fills even concave or disconnected sections.
    const fans = new Float32Array((values.length / 6) * 9);
    const center = [0, 0, 0];
    for (let i = 0; i < values.length; i++) center[i % 3] += values[i] / lineCount;
    for (let i = 0, j = 0; i < values.length; i += 6, j += 9) {
      fans.set(center, j);
      for (let k = 0; k < 6; k++) fans[j + 3 + k] = values[i + k];
    }
    gl.bindBuffer(gl.ARRAY_BUFFER, cap);
    gl.bufferData(gl.ARRAY_BUFFER, fans, gl.DYNAMIC_DRAW);
  }
  function draw(next) {
    if (next) state = next;
    if (gl.isContextLost()) return;
    const w = Math.max(1, canvas.clientWidth),
      h = Math.max(1, canvas.clientHeight),
      dpr = Math.min(2, window.devicePixelRatio || 1);
    const px = Math.round(w * dpr),
      py = Math.round(h * dpr);
    if (canvas.width !== px || canvas.height !== py) {
      canvas.width = px;
      canvas.height = py;
    }
    gl.viewport(0, 0, px, py);
    gl.clearColor(0.04, 0.075, 0.095, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT | gl.STENCIL_BUFFER_BIT);
    if (!state || !count) return;
    gl.useProgram(program);
    const uniform = (name) => gl.getUniformLocation(program, name);
    const center = state.bounds[0].map((x, i) => (x + state.bounds[1][i]) / 2);
    // Sphere enclosing every vertex in all orientations, independent of aspect.
    const half = state.radius / Math.min(1, w / h);
    gl.uniform3fv(uniform('center'), center);
    gl.uniform2f(uniform('extent'), (half * w) / h, half);
    gl.uniform2f(uniform('rotation'), (state.yaw * Math.PI) / 180, (state.pitch * Math.PI) / 180);
    gl.uniform1i(uniform('axis'), state.axis);
    gl.uniform1f(uniform('sectionHeight'), state.height);
    gl.uniform1i(uniform('cutaway'), state.cut ? 1 : 0);
    gl.uniform1i(uniform('material'), 0);
    gl.enableVertexAttribArray(position);
    gl.bindBuffer(gl.ARRAY_BUFFER, xyz);
    gl.vertexAttribPointer(position, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index);
    gl.enable(gl.POLYGON_OFFSET_FILL);
    gl.polygonOffset(1, 1);
    gl.drawElements(gl.TRIANGLES, count, gl.UNSIGNED_INT, 0);
    gl.disable(gl.POLYGON_OFFSET_FILL);
    if (state.cut && lineCount && gl.getContextAttributes().stencil) {
      gl.bindBuffer(gl.ARRAY_BUFFER, cap);
      gl.vertexAttribPointer(position, 3, gl.FLOAT, false, 0, 0);
      gl.uniform1i(uniform('material'), 2);
      gl.enable(gl.STENCIL_TEST);
      gl.stencilMask(1);
      gl.stencilFunc(gl.ALWAYS, 0, 1);
      gl.stencilOp(gl.KEEP, gl.KEEP, gl.INVERT);
      gl.colorMask(false, false, false, false);
      gl.depthMask(false);
      gl.disable(gl.DEPTH_TEST);
      gl.drawArrays(gl.TRIANGLES, 0, (lineCount / 2) * 3);
      gl.colorMask(true, true, true, true);
      gl.depthMask(true);
      gl.enable(gl.DEPTH_TEST);
      gl.stencilFunc(gl.EQUAL, 1, 1);
      gl.stencilOp(gl.KEEP, gl.KEEP, gl.KEEP);
      gl.enable(gl.POLYGON_OFFSET_FILL);
      gl.polygonOffset(1, 1);
      gl.drawArrays(gl.TRIANGLES, 0, (lineCount / 2) * 3);
      gl.disable(gl.POLYGON_OFFSET_FILL);
      gl.disable(gl.STENCIL_TEST);
    }
    gl.bindBuffer(gl.ARRAY_BUFFER, lines);
    gl.vertexAttribPointer(position, 3, gl.FLOAT, false, 0, 0);
    gl.uniform1i(uniform('material'), 1);
    gl.drawArrays(gl.LINES, 0, lineCount);
    canvas.dataset.triangles = String(count / 3);
  }
  setup();
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    canvas.dataset.triangles = '0';
  });
  canvas.addEventListener('webglcontextrestored', () => {
    setup();
    const old = section;
    setMesh(mesh);
    setSection(old);
    draw();
  });
  new ResizeObserver(() => draw()).observe(canvas);
  return { setMesh, setSection, draw };
}

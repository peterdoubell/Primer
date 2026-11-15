// Each instance encodes one occupied voxel and one of its six faces.
// Grid edges are left open where the source field of view ends.
export function traceFaces(shape, sample) {
  const [nx, ny, nz] = shape;
  const maximum = 6 * 187819;
  const faces = new Uint32Array(maximum);
  let count = 0;
  for (let k = 0; k < nz; k++) {
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        if (sample(i, j, k) !== 1) continue;
        const cell = (i + nx * (j + ny * k)) * 6;
        if (i > 0 && sample(i - 1, j, k) === 0) faces[count++] = cell;
        if (i < nx - 1 && sample(i + 1, j, k) === 0) faces[count++] = cell + 1;
        if (j > 0 && sample(i, j - 1, k) === 0) faces[count++] = cell + 2;
        if (j < ny - 1 && sample(i, j + 1, k) === 0) faces[count++] = cell + 3;
        if (k > 0 && sample(i, j, k - 1) === 0) faces[count++] = cell + 4;
        if (k < nz - 1 && sample(i, j, k + 1) === 0) faces[count++] = cell + 5;
      }
    }
  }
  if (count !== 481088) throw Error('The tracing boundary differs from the verified source');
  return faces.subarray(0, count);
}

const vertexSource = `#version 300 es
precision highp float;
precision highp int;
in uint surfaceFace;
uniform uvec3 shape;
uniform vec3 spacing;
uniform float yaw, pitch, extent, depth, aspect;
out vec3 position;
out vec3 voxelPosition;
const vec2 corners[6] = vec2[6](
  vec2(-.5,-.5), vec2(.5,-.5), vec2(.5,.5), vec2(-.5,-.5), vec2(.5,.5), vec2(-.5,.5));
void main() {
  uint cell = surfaceFace / 6u;
  int face = int(surfaceFace % 6u);
  vec3 voxel = vec3(float(cell % shape.x), float((cell / shape.x) % shape.y), float(cell / (shape.x * shape.y)));
  int axis = face / 2;
  vec2 corner = corners[gl_VertexID];
  voxel[axis] += face % 2 == 0 ? -.5 : .5;
  voxel[(axis + 1) % 3] += face % 2 == 0 ? -corner.x : corner.x;
  voxel[(axis + 2) % 3] += corner.y;
  voxelPosition = voxel;
  vec3 p = (voxel - (vec3(shape) - 1.) / 2.) * spacing;
  float x = cos(yaw) * p.x - sin(yaw) * p.y;
  float d = sin(yaw) * p.x + cos(yaw) * p.y;
  position = vec3(x, cos(pitch) * p.z - sin(pitch) * d, sin(pitch) * p.z + cos(pitch) * d);
  gl_Position = vec4(position.x / (extent * aspect), position.y / extent, -position.z / depth, 1.);
}`;

const fragmentSource = `#version 300 es
precision highp float;
in vec3 position;
in vec3 voxelPosition;
uniform int clipAxis;
uniform float clipAt, clipSign;
out vec4 color;
void main() {
  if (clipAxis >= 0 && clipSign * (voxelPosition[clipAxis] - clipAt) > 0.) discard;
  vec3 normal = normalize(cross(dFdx(position), dFdy(position)));
  float light = .46 + .54 * abs(dot(normal, normalize(vec3(.3,.55,1.))));
  color = vec4(vec3(1.,.69,.32) * light, 1.);
}`;

function compile(gl, program, type, source) {
  const shader = gl.createShader(type);
  try {
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw Error('3D shader failed');
    gl.attachShader(program, shader);
  } finally {
    gl.deleteShader(shader);
  }
}

export function installTracingMesh(shape, affine, sample, points) {
  const get = id => document.getElementById(id);
  const section = get('mesh-section');
  const canvas = get('mesh');
  const status = get('mesh-status');
  const controls = get('mesh-controls');
  const yaw = get('mesh-yaw');
  const pitch = get('mesh-pitch');
  const zoom = get('mesh-zoom');
  const clip = get('mesh-clip');
  const side = get('mesh-side');
  const spacing = [0, 1, 2].map(axis => Math.hypot(...affine.slice(0, 3).map(row => row[axis])));
  const radius = Math.hypot(...shape.map((size, axis) => size * spacing[axis])) / 2;
  section.hidden = false;
  const gl = canvas.getContext('webgl2', { antialias: true });
  if (!gl) {
    status.textContent = '3D requires WebGL 2. The MRI and tracing slices are available above.';
    return;
  }
  let scene;
  let faces;

  function draw() {
    if (!scene || gl.isContextLost()) return;
    const { program, uniforms, vao } = scene;
    const aspect = canvas.width / canvas.height;
    const extent = radius * 1.05 / (zoom.valueAsNumber * Math.min(aspect, 1));
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(.02, .04, .06, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.useProgram(program);
    gl.uniform3uiv(uniforms.shape, shape);
    gl.uniform3fv(uniforms.spacing, spacing);
    gl.uniform1f(uniforms.yaw, yaw.valueAsNumber * Math.PI / 180);
    gl.uniform1f(uniforms.pitch, pitch.valueAsNumber * Math.PI / 180);
    gl.uniform1f(uniforms.extent, extent);
    gl.uniform1f(uniforms.depth, radius * 1.2);
    gl.uniform1f(uniforms.aspect, aspect);
    const axis = Number(clip.value);
    gl.uniform1i(uniforms.clipAxis, axis);
    gl.uniform1f(uniforms.clipAt, points[axis] ?? 0);
    gl.uniform1f(uniforms.clipSign, Number(side.value));
    get('mesh-clip-note').textContent = axis < 0 ? '' :
      clip.selectedOptions[0].textContent + ' section at voxel ' + points[axis] + '. ' +
      (side.value === '1' ? ['Left', 'Posterior', 'Inferior'][axis] : ['Right', 'Anterior', 'Superior'][axis]) + ' side retained.';
    side.disabled = axis < 0;
    gl.bindVertexArray(vao);
    gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, faces.length);
    if (gl.getError() !== gl.NO_ERROR) throw Error('3D draw failed');
    get('mesh-scale').textContent = 'Orthographic frame height ' + (2 * extent).toFixed(1) + ' mm';
    get('mesh-scale-bar').style.width = (50 / (2 * extent * aspect) * 100) + '%';
  }

  function setup() {
    controls.disabled = true;
    const program = gl.createProgram();
    const buffer = gl.createBuffer();
    const vao = gl.createVertexArray();
    try {
      faces ??= traceFaces(shape, sample);
      compile(gl, program, gl.VERTEX_SHADER, vertexSource);
      compile(gl, program, gl.FRAGMENT_SHADER, fragmentSource);
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error('3D program failed');
      const uniforms = Object.fromEntries(['shape', 'spacing', 'yaw', 'pitch', 'extent', 'depth', 'aspect', 'clipAxis', 'clipAt', 'clipSign']
        .map(key => [key, gl.getUniformLocation(program, key)]));
      const attribute = gl.getAttribLocation(program, 'surfaceFace');
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, faces, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(attribute);
      gl.vertexAttribIPointer(attribute, 1, gl.UNSIGNED_INT, 0, 0);
      gl.vertexAttribDivisor(attribute, 1);
      scene = { program, uniforms, vao };
      draw();
      controls.disabled = false;
      status.textContent = faces.length.toLocaleString() + ' source voxel faces rendered';
    } catch (error) {
      scene = null;
      gl.deleteProgram(program);
      gl.deleteBuffer(buffer);
      gl.deleteVertexArray(vao);
      status.textContent = '3D unavailable. ' + error.message;
    }
  }

  for (const input of [yaw, pitch, zoom]) input.addEventListener('input', draw);
  for (const input of [clip, side]) input.addEventListener('change', draw);
  get('mesh-reset').addEventListener('click', () => {
    yaw.value = 25;
    pitch.value = 18;
    zoom.value = 1.35;
    clip.value = -1;
    side.value = 1;
    draw();
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    scene = null;
    controls.disabled = true;
    status.textContent = '3D paused while the graphics context recovers.';
  });
  canvas.addEventListener('webglcontextrestored', setup);
  setup();
  return { refreshSection: () => { if (Number(clip.value) >= 0) draw(); } };
}

const get = id => document.getElementById(id);
const canvas = get('surface');
const selection = get('model');
const yaw = get('yaw');
const pitch = get('pitch');
const status = get('status');
const retry = get('retry');
const viewControls = [yaw, pitch, get('reset')];
const gl = canvas.getContext('webgl2', { antialias: true });
const manifestHash = '2bd706ffbb51f85ea5b526bc6c3c5f0797f2035e1ed879fce52022d26db9b0be';
const descriptions = {
  unicornuate: 'The source model shows an asymmetric main uterine body and a smaller opposite horn.',
  didelphys: 'The source model shows two uterine bodies with a deep separation between them.',
  bicornuate: 'The source model shows two horns with a cleft above a shared lower outline.',
};
let manifest;
let scene;
let active;
let pending;
let commonRadius;

const vertex = `#version 300 es
in vec3 point;
uniform vec3 centre;
uniform float radius, yaw, pitch, aspect;
out vec3 view;
void main() {
  vec3 q = point - centre;
  float x = cos(yaw) * q.x - sin(yaw) * q.y;
  float depth = sin(yaw) * q.x + cos(yaw) * q.y;
  view = vec3(x, sin(pitch) * depth + cos(pitch) * q.z,
    cos(pitch) * depth - sin(pitch) * q.z);
  gl_Position = vec4(view.x / (radius * aspect), view.y / radius, -view.z / radius, 1.);
}`;
const fragment = `#version 300 es
precision highp float;
in vec3 view;
out vec4 color;
void main() {
  vec3 normal = normalize(cross(dFdx(view), dFdy(view)));
  float light = .38 + .62 * abs(dot(normal, normalize(vec3(.32,.48,1.))));
  color = vec4(vec3(.77,.39,.44) * light, 1.);
}`;

function prepareCanvas() {
  const program = gl.createProgram();
  try {
    for (const [type, source] of [[gl.VERTEX_SHADER, vertex], [gl.FRAGMENT_SHADER, fragment]]) {
      const shader = gl.createShader(type);
      try {
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw Error('3D shader unavailable');
        gl.attachShader(program, shader);
      } finally {
        gl.deleteShader(shader);
      }
    }
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error('3D programme unavailable');
    const names = ['centre', 'radius', 'yaw', 'pitch', 'aspect'];
    scene = {
      program,
      attribute: gl.getAttribLocation(program, 'point'),
      uniforms: Object.fromEntries(names.map(name => [name, gl.getUniformLocation(program, name)])),
      points: gl.createBuffer(),
      faces: gl.createBuffer(),
    };
  } catch (error) {
    gl.deleteProgram(program);
    throw error;
  }
}

const digest = async data => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data)),
  value => value.toString(16).padStart(2, '0')).join('');

async function bounded(stream, expected) {
  const reader = stream.getReader();
  const buffer = new Uint8Array(expected);
  let offset = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (offset + value.length > expected) throw Error('Source exceeds the declared size');
      buffer.set(value, offset);
      offset += value.length;
    }
  } finally {
    await reader.cancel();
  }
  if (offset !== expected) throw Error('The source download is incomplete');
  return buffer;
}

function clearCanvas() {
  gl.clearColor(1, 1, 1, 1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
}

function draw() {
  if (!active || gl.isContextLost()) return;
  const { program, uniforms } = scene;
  const [low, high] = active.bounds;
  gl.viewport(0, 0, canvas.width, canvas.height);
  clearCanvas();
  gl.enable(gl.DEPTH_TEST);
  gl.useProgram(program);
  gl.uniform3fv(uniforms.centre, low.map((value, index) => (value + high[index]) / 2));
  gl.uniform1f(uniforms.radius, commonRadius);
  gl.uniform1f(uniforms.yaw, yaw.valueAsNumber * Math.PI / 180);
  gl.uniform1f(uniforms.pitch, pitch.valueAsNumber * Math.PI / 180);
  gl.uniform1f(uniforms.aspect, canvas.width / canvas.height);
  gl.drawElements(gl.TRIANGLES, active.triangles * 3, gl.UNSIGNED_INT, 0);
  if (gl.getError() !== gl.NO_ERROR) throw Error('The source mesh could not be rendered');
}

function showFailure(error) {
  active = null;
  if (gl && !gl.isContextLost()) clearCanvas();
  get('caption').textContent = '';
  canvas.removeAttribute('aria-label');
  status.textContent = error.message;
  retry.hidden = false;
  for (const control of viewControls) control.disabled = true;
}

async function loadModel() {
  pending?.abort();
  pending = new AbortController();
  const signal = AbortSignal.any([pending.signal, AbortSignal.timeout(90000)]);
  retry.hidden = true;
  active = null;
  get('caption').textContent = '';
  canvas.removeAttribute('aria-label');
  for (const control of viewControls) control.disabled = true;
  clearCanvas();
  status.textContent = 'Verifying source geometry…';
  try {
    const model = manifest.models.find(row => row.id === selection.value);
    const response = await fetch(model.file, { signal });
    if (!response.ok) throw Error('The teaching mesh is unavailable');
    const packed = await bounded(response.body, model.bytes);
    if (await digest(packed) !== model.sha256) throw Error('Compressed mesh checksum differs');
    const stream = new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'));
    const decoded = await bounded(stream, 12 * (model.vertices + model.triangles));
    if (await digest(decoded) !== model.decodedSha256) throw Error('Decoded mesh checksum differs');
    signal.throwIfAborted();
    if (gl.isContextLost()) return;
    gl.bindBuffer(gl.ARRAY_BUFFER, scene.points);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(decoded.buffer, 0, 3 * model.vertices), gl.STATIC_DRAW);
    gl.vertexAttribPointer(scene.attribute, 3, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(scene.attribute);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, scene.faces);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint32Array(decoded.buffer, 12 * model.vertices), gl.STATIC_DRAW);
    active = model;
    draw();
    canvas.setAttribute('aria-label', model.title + ' authored 3D teaching surface');
    get('caption').textContent = descriptions[model.id];
    status.textContent = model.triangles.toLocaleString() + ' original faces rendered';
    for (const control of viewControls) control.disabled = false;
  } catch (error) {
    if (signal.reason?.name === 'AbortError') return;
    showFailure(error);
  }
}

async function initialise() {
  retry.hidden = true;
  try {
    if (!gl) throw Error('This browser requires WebGL 2 for the 3D view');
    if (!manifest) {
      const response = await fetch('models.json', { signal: AbortSignal.timeout(15000) });
      if (!response.ok) throw Error('The model inventory is unavailable');
      const bytes = await response.arrayBuffer();
      if (await digest(bytes) !== manifestHash) throw Error('The model inventory checksum differs');
      manifest = JSON.parse(new TextDecoder().decode(bytes));
      selection.replaceChildren(...manifest.models.map(model => new Option(model.title, model.id)));
      commonRadius = Math.max(...manifest.models.map(({ bounds: [low, high] }) =>
        Math.hypot(...low.map((value, axis) => high[axis] - value)))) * .55;
    }
    if (!scene) prepareCanvas();
    selection.disabled = false;
    await loadModel();
  } catch (error) {
    showFailure(error);
  }
}

selection.addEventListener('change', loadModel);
for (const control of [yaw, pitch]) control.addEventListener('input', draw);
get('reset').addEventListener('click', () => {
  yaw.value = 0;
  pitch.value = 0;
  draw();
});
retry.addEventListener('click', initialise);
canvas.addEventListener('webglcontextlost', event => {
  event.preventDefault();
  pending?.abort();
  scene = null;
  active = null;
  selection.disabled = true;
  for (const control of viewControls) control.disabled = true;
  status.textContent = 'The graphics context is recovering…';
});
canvas.addEventListener('webglcontextrestored', initialise);
initialise();

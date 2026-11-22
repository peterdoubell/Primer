import { verifiedBytes } from './native-volume.mjs';

// Shader, typed-buffer layout, orbit transform and derivative lighting reuse
// Primer's bp3d-dural-4.3/surface-viewer.js. This adapter loads one manifest
// mesh at a time and projects the active native-index section into its frame.
const vertexSource = `#version 300 es
  in vec3 position;
  uniform vec3 center;
  uniform float yaw, pitch, radius;
  out vec3 view;
  void main() {
    vec3 p = position - center;
    float x = cos(yaw)*p.x - sin(yaw)*p.y;
    float d = sin(yaw)*p.x + cos(yaw)*p.y;
    view = vec3(x, cos(pitch)*p.z - sin(pitch)*d, sin(pitch)*p.z + cos(pitch)*d);
    gl_Position = vec4(view.x/(radius*4./3.), view.y/radius, -view.z/(2.*radius), 1.);
  }`;
const fragmentSource = `#version 300 es
  precision highp float;
  in vec3 view;
  uniform vec3 tint;
  out vec4 color;
  void main() {
    vec3 normal = normalize(cross(dFdx(view), dFdy(view)));
    color = vec4(tint*(.5 + .5*abs(dot(normal, normalize(vec3(.3,.5,1.))))), 1.);
  }`;

const namespace = 'http://www.w3.org/2000/svg';
function shape(tag, attributes, text) {
  const node = document.createElementNS(namespace, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

export function meshView(canvas, overlay, status, controls) {
  const gl = canvas.getContext('webgl2', { preserveDrawingBuffer: true });
  let scene = null;
  let latest = null;
  let pending = null;
  let generation = 0;
  let locator = null;

  function dispose() {
    if (scene && gl && !gl.isContextLost()) {
      gl.deleteVertexArray(scene.vao);
      gl.deleteBuffer(scene.positions);
      gl.deleteBuffer(scene.indices);
      gl.deleteProgram(scene.program);
    }
    scene = null;
  }

  function compile(program, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      gl.deleteShader(shader);
      throw Error('The 3D shader could not be compiled.');
    }
    gl.attachShader(program, shader);
    gl.deleteShader(shader);
  }

  function viewState() {
    const low = scene.bounds[0], high = scene.bounds[1];
    const center = low.map((value, axis) => (value + high[axis]) / 2);
    const radius = Math.max(.1, .56 * Math.hypot(...high.map((value, axis) => value - low[axis])))
      / controls.zoom.valueAsNumber;
    const yaw = controls.yaw.valueAsNumber * Math.PI / 180;
    const pitch = controls.pitch.valueAsNumber * Math.PI / 180;
    const project = position => {
      const p = position.map((value, axis) => value - center[axis]);
      const x = Math.cos(yaw) * p[0] - Math.sin(yaw) * p[1];
      const d = Math.sin(yaw) * p[0] + Math.cos(yaw) * p[1];
      const y = Math.cos(pitch) * p[2] - Math.sin(pitch) * d;
      return [320 + x * 240 / radius, 240 - y * 240 / radius];
    };
    return { center, radius, yaw, pitch, project };
  }

  function drawLocator(view) {
    overlay.replaceChildren();
    const fontSize = Math.max(16, 14 * 640 / Math.max(1, canvas.clientWidth));
    if (locator) {
      const { axes, position, spacing } = locator;
      const fixed = position[axes.normal] * spacing[axes.normal];
      if (fixed >= scene.bounds[0][axes.normal] && fixed <= scene.bounds[1][axes.normal]) {
        const corners = [[0, 0], [1, 0], [1, 1], [0, 1]].map(([h, v]) => {
          const point = [0, 0, 0];
          point[axes.normal] = fixed;
          point[axes.horizontal] = scene.bounds[h][axes.horizontal];
          point[axes.vertical] = scene.bounds[v][axes.vertical];
          return view.project(point);
        });
        overlay.append(shape('polygon', {
          points: corners.map(point => point.join(',')).join(' '),
          fill: '#83d2ed', 'fill-opacity': .08, stroke: '#a8e8ff', 'stroke-width': 2,
        }));
        const point = view.project(position.map((value, axis) => value * spacing[axis]));
        overlay.append(shape('circle', { cx: point[0], cy: point[1], r: 5, fill: '#ffce79', stroke: '#172333' }));
      }
      overlay.append(shape('text', { x: 18, y: 30, fill: '#d4eefa', 'font-size': fontSize },
        axes.name + ' section · ' + axes.fixedName + ' = ' + position[axes.normal]));
    }
    const desired = view.radius / 2;
    const power = 10 ** Math.floor(Math.log10(desired));
    const length = [1, 2, 5, 10].map(value => value * power).filter(value => value <= desired).at(-1);
    const pixels = length * 240 / view.radius;
    overlay.append(shape('line', { x1: 22, y1: 450, x2: 22 + pixels, y2: 450,
      stroke: '#ffffff', 'stroke-width': 3 }));
    overlay.append(shape('text', { x: 22, y: 434, fill: '#ffffff', 'font-size': fontSize },
      Number(length.toPrecision(5)) + ' mm'));
    const origin = [520, 405];
    const unit = view.project(view.center);
    ['I', 'J', 'K'].forEach((name, axis) => {
      const endpoint = [...view.center];
      endpoint[axis] += view.radius / 4;
      const projected = view.project(endpoint);
      const x = origin[0] + projected[0] - unit[0], y = origin[1] + projected[1] - unit[1];
      overlay.append(shape('line', { x1: origin[0], y1: origin[1], x2: x, y2: y, stroke: '#d4eefa', 'stroke-width': 2 }));
      overlay.append(shape('text', { x: x + 7, y: y - 4, fill: '#ffffff', 'font-size': fontSize }, '+' + name));
    });
  }

  function draw() {
    controls.yawValue.textContent = controls.yaw.value + '°';
    controls.pitchValue.textContent = controls.pitch.value + '°';
    if (!scene || gl.isContextLost()) return;
    const view = viewState();
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(.06, .09, .12, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.useProgram(scene.program);
    gl.uniform3fv(gl.getUniformLocation(scene.program, 'center'), view.center);
    gl.uniform1f(gl.getUniformLocation(scene.program, 'radius'), view.radius);
    gl.uniform1f(gl.getUniformLocation(scene.program, 'yaw'), view.yaw);
    gl.uniform1f(gl.getUniformLocation(scene.program, 'pitch'), view.pitch);
    gl.uniform3fv(gl.getUniformLocation(scene.program, 'tint'), scene.label.color.map(value => value / 255));
    gl.bindVertexArray(scene.vao);
    gl.drawElements(gl.TRIANGLES, scene.label.mesh.triangles * 3, gl.UNSIGNED_INT, 0);
    drawLocator(view);
  }

  async function load(record, label) {
    latest = { record, label };
    controls.retry.hidden = true;
    const attempt = ++generation;
    pending?.abort();
    pending = new AbortController();
    dispose();
    overlay.replaceChildren();
    canvas.hidden = true;
    if (!gl) {
      status.textContent = 'This browser needs WebGL 2 to display the source surface.';
      return;
    }
    if (gl.isContextLost()) return;
    if (!label.mesh || !label.voxelCount) {
      status.textContent = 'This label has no source surface.';
      return;
    }
    status.textContent = 'Verifying the selected source surface…';
    let resources = null;
    try {
      const metadata = label.mesh;
      const bytes = await verifiedBytes(metadata, pending.signal);
      if (bytes.byteLength !== 12 * (metadata.vertices + metadata.triangles)) {
        throw Error('The source surface byte count differs.');
      }
      if (attempt !== generation) return;
      const positions = new Float32Array(bytes, 0, metadata.vertices * 3);
      const indices = new Uint32Array(bytes, metadata.vertices * 12);
      const low = [Infinity, Infinity, Infinity], high = [-Infinity, -Infinity, -Infinity];
      for (let index = 0; index < positions.length; index += 1) {
        const value = positions[index], axis = index % 3;
        if (!Number.isFinite(value)) throw Error('A source vertex is invalid.');
        low[axis] = Math.min(low[axis], value);
        high[axis] = Math.max(high[axis], value);
      }
      if (indices.some(value => value >= metadata.vertices)) throw Error('A source face index is invalid.');
      resources = { program: gl.createProgram(), vao: gl.createVertexArray(),
        positions: gl.createBuffer(), indices: gl.createBuffer(), bounds: [low, high], label };
      compile(resources.program, gl.VERTEX_SHADER, vertexSource);
      compile(resources.program, gl.FRAGMENT_SHADER, fragmentSource);
      gl.linkProgram(resources.program);
      if (!gl.getProgramParameter(resources.program, gl.LINK_STATUS)) throw Error('The 3D program could not be linked.');
      gl.bindVertexArray(resources.vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, resources.positions);
      gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
      const attribute = gl.getAttribLocation(resources.program, 'position');
      gl.enableVertexAttribArray(attribute);
      gl.vertexAttribPointer(attribute, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, resources.indices);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
      scene = resources;
      canvas.hidden = false;
      canvas.setAttribute('aria-label', label.name + ' source mask surface. Use arrow keys to orbit and plus or minus to zoom.');
      status.textContent = metadata.triangles.toLocaleString() + ' source triangles · ' + label.name;
      draw();
    } catch (error) {
      if (attempt !== generation || pending.signal.aborted) return;
      if (resources) {
        scene = resources;
        dispose();
      }
      controls.retry.hidden = false;
      status.textContent = 'The selected source surface could not be verified. Retry the view.';
    }
  }

  for (const input of [controls.yaw, controls.pitch, controls.zoom]) input.addEventListener('input', draw);
  controls.reset.addEventListener('click', () => {
    controls.yaw.value = 25; controls.pitch.value = 18; controls.zoom.value = 1; draw();
  });
  controls.retry.addEventListener('click', () => { if (latest) load(latest.record, latest.label); });
  let dragging = null;
  canvas.addEventListener('pointerdown', event => {
    dragging = { x: event.clientX, y: event.clientY, yaw: controls.yaw.valueAsNumber, pitch: controls.pitch.valueAsNumber };
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', event => {
    if (!dragging) return;
    controls.yaw.value = ((dragging.yaw + (event.clientX - dragging.x) * .5 + 540) % 360) - 180;
    controls.pitch.value = Math.max(-85, Math.min(85, dragging.pitch + (event.clientY - dragging.y) * .5));
    draw();
  });
  for (const event of ['pointerup', 'pointercancel']) canvas.addEventListener(event, () => { dragging = null; });
  canvas.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '-', '=', 'Home'].includes(event.key)) return;
    event.preventDefault();
    const delta = { ArrowLeft: [-5, 0], ArrowRight: [5, 0], ArrowUp: [0, -5], ArrowDown: [0, 5] }[event.key];
    if (delta) {
      controls.yaw.value = ((controls.yaw.valueAsNumber + delta[0] + 540) % 360) - 180;
      controls.pitch.value = Math.max(-85, Math.min(85, controls.pitch.valueAsNumber + delta[1]));
    } else if (event.key === 'Home') {
      controls.reset.click();
    } else {
      controls.zoom.value = Math.max(.5, Math.min(3, controls.zoom.valueAsNumber * (event.key === '-' ? 1 / 1.1 : 1.1)));
    }
    draw();
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    generation += 1;
    pending?.abort();
    scene = null;
    overlay.replaceChildren();
    status.textContent = 'The graphics context was lost. Waiting for recovery.';
  });
  canvas.addEventListener('webglcontextrestored', () => { if (latest) load(latest.record, latest.label); });
  new ResizeObserver(draw).observe(canvas.parentElement);
  return { load, locator: value => { locator = value; draw(); } };
}

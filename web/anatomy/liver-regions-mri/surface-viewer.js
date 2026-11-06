'use strict';

(() => {
  const canvas = document.querySelector('#surface');
  const status = document.querySelector('#surface-status');
  const frame = document.createElement('div');
  frame.className = 'surface-frame';
  canvas.before(frame);
  frame.append(canvas);
  const scale = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  scale.setAttribute('viewBox', '0 0 640 480');
  scale.setAttribute('role', 'img');
  scale.setAttribute('aria-label', 'Source model scale in millimetres, parallel to the viewing plane');
  scale.classList.add('surface-scale');
  scale.setAttribute('hidden', '');
  frame.append(scale);
  const layers = [...document.querySelectorAll('.layer')];
  const rotation = document.querySelector('#rotation');
  const tilt = document.querySelector('#tilt');
  const retry = document.createElement('button');
  retry.type = 'button';
  retry.textContent = 'Retry 3D view';
  retry.hidden = true;
  status.after(retry);
  let frameSelection = true;
  const framing = document.createElement('button');
  framing.type = 'button';
  framing.textContent = 'Use full reference extent';
  retry.after(framing);
  framing.addEventListener('click', () => {
    frameSelection = !frameSelection;
    framing.textContent = frameSelection ? 'Use full reference extent' : 'Fit selected region';
    draw();
  });

  const gl = canvas.getContext('webgl2', {preserveDrawingBuffer: true});
  const verified = new Map();
  let generation = 0;
  let pending = null;
  let scene = null;

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

  function dispose(resources) {
    if (!resources || !gl || gl.isContextLost()) return;
    for (const mesh of resources.meshes) {
      gl.deleteVertexArray(mesh.vao);
      gl.deleteBuffer(mesh.positions);
      gl.deleteBuffer(mesh.indices);
    }
    gl.deleteProgram(resources.program);
  }

  async function decode(row, signal) {
    const key = row.file + ':' + row.sha256;
    if (verified.has(key)) return verified.get(key);
    const response = await fetch(row.file, {signal});
    if (!response.ok) throw Error('Missing surface');
    const bytes = await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
      .map(byte => byte.toString(16).padStart(2, '0')).join('');
    if (digest !== row.sha256 || bytes.byteLength !== 12*(row.vertices + row.triangles)) {
      throw Error('Surface bytes differ');
    }
    const result = {
      positions: new Float32Array(bytes, 0, 3*row.vertices),
      indices: new Uint32Array(bytes, 12*row.vertices),
    };
    verified.set(key, result);
    return result;
  }

  function compile(program, type, source) {
    const shader = gl.createShader(type);
    try {
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw Error('Shader compilation failed');
      gl.attachShader(program, shader);
    } finally {
      gl.deleteShader(shader);
    }
  }

  function upload(rows, decoded, resources) {
    const program = resources.program;
    compile(program, gl.VERTEX_SHADER, vertexSource);
    compile(program, gl.FRAGMENT_SHADER, fragmentSource);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error('Shader link failed');
    gl.useProgram(program);
    const attribute = gl.getAttribLocation(program, 'position');
    for (const [i, row] of rows.entries()) {
      const mesh = {row, vao: gl.createVertexArray(), positions: gl.createBuffer(), indices: gl.createBuffer()};
      resources.meshes.push(mesh);
      gl.bindVertexArray(mesh.vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.positions);
      gl.bufferData(gl.ARRAY_BUFFER, decoded[i].positions, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(attribute);
      gl.vertexAttribPointer(attribute, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, mesh.indices);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, decoded[i].indices, gl.STATIC_DRAW);
    }

  }

  function draw() {
    if (!scene || gl.isContextLost()) return;
    const {program, meshes} = scene;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(.06, .09, .12, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.useProgram(program);
    const selected = meshes.filter((mesh,i) => layers[i].checked);
    const framed = frameSelection && selected.length ? selected : meshes;
    const low = [0,1,2].map(axis => Math.min(...framed.map(mesh => mesh.row.bounds[0][axis])));
    const high = [0,1,2].map(axis => Math.max(...framed.map(mesh => mesh.row.bounds[1][axis])));
    gl.uniform3fv(gl.getUniformLocation(program, 'center'), low.map((value,axis) => (value + high[axis])/2));
    const radius = .52*Math.hypot(...high.map((value,axis) => value - low[axis]));
    gl.uniform1f(gl.getUniformLocation(program, 'radius'), radius);
    gl.uniform1f(gl.getUniformLocation(program, 'yaw'), rotation.valueAsNumber*Math.PI/180);
    gl.uniform1f(gl.getUniformLocation(program, 'pitch'), tilt.valueAsNumber*Math.PI/180);
    let triangles = 0;
    for (const [i, mesh] of meshes.entries()) {
      if (!layers[i].checked) continue;
      gl.uniform3fv(gl.getUniformLocation(program, 'tint'), mesh.row.color.map(value => value/255));
      gl.bindVertexArray(mesh.vao);
      gl.drawElements(gl.TRIANGLES, mesh.row.triangles*3, gl.UNSIGNED_INT, 0);
      triangles += mesh.row.triangles;
    }
    status.textContent = triangles.toLocaleString() + ' source triangles visible';
    const desired = radius / 2;
    const power = 10 ** Math.floor(Math.log10(desired));
    const length = [1, 2, 5, 10].map(value => value * power).filter(value => value <= desired).at(-1);
    const pixels = length * 240 / radius;
    scale.replaceChildren();
    const bar = document.createElementNS(scale.namespaceURI, 'line');
    for (const [key,value] of Object.entries({x1:30,x2:30+pixels,y1:440,y2:440,stroke:'#ffffff','stroke-width':3})) bar.setAttribute(key,value);
    const text = document.createElementNS(scale.namespaceURI, 'text');
    for (const [key,value] of Object.entries({x:30,y:425,fill:'#ffffff','font-size':18*640/Math.max(1,canvas.clientWidth)})) text.setAttribute(key,value);
    text.textContent = Number(length.toPrecision(6)) + ' mm';
    scale.append(bar,text);
    scale.dataset.lengthMm = length;
    scale.removeAttribute('hidden');
  }

  async function start() {
    const attempt = ++generation;
    pending?.abort();
    pending = new AbortController();
    const signal = pending.signal;
    retry.hidden = true;
    canvas.hidden = true;
    scale.setAttribute('hidden', '');
    dispose(scene);
    scene = null;
    if (!gl) {
      status.textContent = 'WebGL 2 is required for the surface view.';
      return;
    }
    if (gl.isContextLost()) return;
    status.textContent = 'Loading verified source surfaces…';
    let resources = null;
    const current = () => attempt === generation && !gl.isContextLost();
    try {
      const response = await fetch('surfaces.json', {signal});
      if (!response.ok) throw Error('Missing surface inventory');
      const metadata = await response.arrayBuffer();
      const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', metadata))]
        .map(value => value.toString(16).padStart(2, '0')).join('');
      if (digest !== document.querySelector('main').dataset.surfacesSha256) throw Error('Surface inventory checksum differs');
      const rows = JSON.parse(new TextDecoder().decode(metadata));
      if (rows.length !== layers.length) throw Error('Surface inventory differs');
      const decoded = await Promise.all(rows.map(row => decode(row, signal)));
      if (!current()) return;
      resources = {program: gl.createProgram(), meshes: []};
      upload(rows, decoded, resources);
      if (!current()) return;
      scene = resources;
      canvas.hidden = false;
      draw();
    } catch {
      if (!current()) return;
      dispose(resources);
      status.textContent = 'The source surfaces could not be loaded. Retry the 3D view.';
      retry.textContent = 'Retry 3D view';
      retry.hidden = false;
    }
  }

  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    generation++;
    pending?.abort();
    scene = null;
    canvas.hidden = true;
    scale.setAttribute('hidden', '');
    status.textContent = 'The 3D graphics context was lost. Waiting for recovery.';
    retry.textContent = 'Reload page to retry';
    retry.hidden = false;
  });
  canvas.addEventListener('webglcontextrestored', start);
  for (const control of [...layers, rotation, tilt]) control.addEventListener('input', draw);
  retry.addEventListener('click', () => {
    if (gl?.isContextLost()) location.reload();
    else start();
  });
  new ResizeObserver(draw).observe(frame);
  start();
})();

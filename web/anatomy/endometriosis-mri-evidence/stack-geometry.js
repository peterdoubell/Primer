function geometry(metadata) {
  const [, rows, columns] = metadata.shapeStackRowsColumns;
  const [rowSpacing, columnSpacing] = metadata.pixelSpacingRowsColumnsMm;
  const alongColumn = metadata.directionForIncreasingColumnLps;
  const alongRow = metadata.directionForIncreasingRowLps;
  const corners = metadata.planes.flatMap(plane => [
    [-.5, -.5, 0, 0],
    [columns - .5, -.5, 1, 0],
    [columns - .5, rows - .5, 1, 1],
    [-.5, rows - .5, 0, 1],
  ].map(([column, row, u, v]) => [
    ...plane.originLpsMm.map((origin, axis) => origin +
      column * columnSpacing * alongColumn[axis] + row * rowSpacing * alongRow[axis]),
    u, v,
  ]));
  const min = [0, 1, 2].map(axis => Math.min(...corners.map(point => point[axis])));
  const max = [0, 1, 2].map(axis => Math.max(...corners.map(point => point[axis])));
  return {
    vertices: new Float32Array(corners.flat()),
    centre: min.map((number, axis) => (number + max[axis]) / 2),
    radius: .53 * Math.hypot(...min.map((number, axis) => max[axis] - number)),
  };
}

const vertex = `#version 300 es
in vec3 position;
in vec2 sampleUV;
uniform vec3 centre;
uniform float yaw, pitch, radius, aspect;
out vec2 uv;
void main() {
  vec3 p = position - centre;
  float x = cos(yaw) * p.y + sin(yaw) * p.x;
  float depth = -sin(yaw) * p.y + cos(yaw) * p.x;
  float y = cos(pitch) * p.z + sin(pitch) * depth;
  float z = cos(pitch) * depth - sin(pitch) * p.z;
  gl_Position = vec4(x / (radius * aspect), y / radius, -z / radius, 1.);
  uv = sampleUV;
}`;

const fragment = `#version 300 es
precision highp float;
precision highp usampler2D;
in vec2 uv;
uniform usampler2D pixels;
uniform vec2 windowRange;
uniform int mode;
out vec4 color;
void main() {
  if (mode == 1) {
    float stored = float(texture(pixels, uv).r);
    float tone = clamp((stored - windowRange.x) / (windowRange.y - windowRange.x), 0., 1.);
    color = vec4(tone, tone, tone, 1.);
  } else if (mode == 2) {
    color = vec4(.39, .89, .98, 1.);
  } else {
    color = vec4(.29, .43, .50, 1.);
  }
}`;

function assembleProgram(gl) {
  const program = gl.createProgram();
  try {
    for (const [type, source] of [[gl.VERTEX_SHADER, vertex], [gl.FRAGMENT_SHADER, fragment]]) {
      const shader = gl.createShader(type);
      try {
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw Error('The slice shader is unavailable.');
        gl.attachShader(program, shader);
      } finally {
        gl.deleteShader(shader);
      }
    }
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error('The 3D slice program could not be linked.');
    return program;
  } catch (error) {
    gl.deleteProgram(program);
    throw error;
  }
}

export function installGeometry(metadata, stack, inputs) {
  const get = id => document.getElementById(id);
  const canvas = get('slice-geometry');
  const controls = get('geometry-controls');
  const status = get('geometry-status');
  const yaw = get('stack-yaw');
  const pitch = get('stack-pitch');
  const gl = canvas.getContext('webgl2', { antialias: true });
  if (!gl) {
    status.textContent = 'WebGL 2 is required for the spatial view. The acquired images remain available above.';
    return;
  }
  const [count, height, width] = metadata.shapeStackRowsColumns;
  const mesh = geometry(metadata);
  let scene;

  function draw() {
    if (!scene || gl.isContextLost()) return;
    const { slice, low, high } = inputs();
    if (!Number.isFinite(low) || !Number.isFinite(high) || high <= low) return;
    const { program, uniforms, vao, texture } = scene;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(.04, .08, .11, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.useProgram(program);
    gl.bindVertexArray(vao);
    gl.uniform3fv(uniforms.centre, mesh.centre);
    gl.uniform1f(uniforms.yaw, yaw.valueAsNumber * Math.PI / 180);
    gl.uniform1f(uniforms.pitch, pitch.valueAsNumber * Math.PI / 180);
    gl.uniform1f(uniforms.radius, mesh.radius);
    gl.uniform1f(uniforms.aspect, canvas.width / canvas.height);
    gl.uniform2f(uniforms.windowRange, low, high);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    if (scene.current !== slice) {
      const begin = width * height * slice;
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, width, height, gl.RED_INTEGER, gl.UNSIGNED_SHORT,
        stack.subarray(begin, begin + width * height));
      scene.current = slice;
    }
    gl.uniform1i(uniforms.pixels, 0);
    gl.uniform1i(uniforms.mode, 1);
    gl.drawArrays(gl.TRIANGLE_FAN, 4 * slice, 4);
    gl.depthFunc(gl.LEQUAL);
    gl.uniform1i(uniforms.mode, 0);
    for (let index = 0; index < count; index++) {
      if (index !== slice) gl.drawArrays(gl.LINE_LOOP, 4 * index, 4);
    }
    gl.uniform1i(uniforms.mode, 2);
    gl.drawArrays(gl.LINE_LOOP, 4 * slice, 4);
    gl.depthFunc(gl.LESS);
    if (gl.getError() !== gl.NO_ERROR) throw Error('The spatial slice view could not be drawn.');
    status.textContent = 'Slice ' + (slice + 1) + ' of ' + count + ' at its acquired position.';
  }

  function prepare() {
    if (gl.isContextLost()) return;
    try {
      const program = assembleProgram(gl);
      const vao = gl.createVertexArray();
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(gl.ARRAY_BUFFER, mesh.vertices, gl.STATIC_DRAW);
      for (const [name, dimensions, offset] of [['position', 3, 0], ['sampleUV', 2, 12]]) {
        const attribute = gl.getAttribLocation(program, name);
        gl.enableVertexAttribArray(attribute);
        gl.vertexAttribPointer(attribute, dimensions, gl.FLOAT, false, 20, offset);
      }
      const texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texStorage2D(gl.TEXTURE_2D, 1, gl.R16UI, width, height);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      const names = ['centre', 'yaw', 'pitch', 'radius', 'aspect', 'windowRange', 'pixels', 'mode'];
      scene = { program, vao, texture, current: -1,
        uniforms: Object.fromEntries(names.map(name => [name, gl.getUniformLocation(program, name)])) };
      draw();
      controls.disabled = false;
    } catch (error) {
      scene = null;
      controls.disabled = true;
      status.textContent = error.message;
    }
  }

  for (const input of [yaw, pitch]) input.addEventListener('input', draw);
  get('stack-reset').addEventListener('click', () => {
    yaw.value = 35;
    pitch.value = 22;
    draw();
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    scene = null;
    controls.disabled = true;
    status.textContent = 'The spatial view will return when the graphics context recovers.';
  });
  canvas.addEventListener('webglcontextrestored', prepare);
  prepare();
  return { draw };
}

import { sectionQuad, referenceAxes } from './geometry.mjs';

const vertex = `#version 300 es
layout(location=0) in vec3 position;
layout(location=1) in vec2 texcoord;
uniform vec3 center;
uniform float yaw,pitch,radius,aspect;
out vec3 nativePosition,viewPosition;
out vec2 uv;
void main() {
  vec3 p=position-center;
  float x=-cos(yaw)*p.x+sin(yaw)*p.y;
  float depth=sin(yaw)*p.x+cos(yaw)*p.y;
  viewPosition=vec3(x,cos(pitch)*p.z-sin(pitch)*depth,cos(pitch)*depth+sin(pitch)*p.z);
  gl_Position=vec4(viewPosition.x/(radius*aspect),viewPosition.y/radius,-viewPosition.z/(radius*4.),1.);
  nativePosition=position;
  uv=texcoord;
}`;
const fragment = `#version 300 es
precision highp float;
in vec3 nativePosition,viewPosition;
in vec2 uv;
uniform vec3 tint,axis;
uniform float cut,fixedMm;
uniform bool textured;
uniform sampler2D sectionImage;
out vec4 color;
void main() {
  if(textured) {
    vec4 sampleColor=texture(sectionImage,uv);
    if(sampleColor.a<0.5)discard;
    color=vec4(sampleColor.rgb,1.);
  } else {
    if(cut*(dot(axis,nativePosition)-fixedMm)>0.001)discard;
    vec3 normal=normalize(cross(dFdx(viewPosition),dFdy(viewPosition)));
    color=vec4(tint*(0.48+0.52*abs(dot(normal,normalize(vec3(.35,.45,1.))))),1.);
  }
}`;

function programFor(gl) {
  const program = gl.createProgram();
  for (const [type, text] of [
    [gl.VERTEX_SHADER, vertex],
    [gl.FRAGMENT_SHADER, fragment]
  ]) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, text);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS))
      throw Error('The graphics shader could not compile.');
    gl.attachShader(program, shader);
    gl.deleteShader(shader);
  }
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS))
    throw Error('The graphics program could not link.');
  return program;
}

function drawReference(svg, width, height, mmPerPixel, yaw, pitch) {
  const line = (x1, y1, x2, y2, stroke) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    for (const [name, value] of Object.entries({ x1, y1, x2, y2, stroke, 'stroke-width': 2 }))
      node.setAttribute(name, value);
    return node;
  };
  const label = (x, y, text, anchor) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    node.setAttribute('x', x);
    node.setAttribute('y', y);
    node.setAttribute('text-anchor', anchor);
    node.textContent = text;
    return node;
  };
  svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
  svg.replaceChildren();
  const x = 38,
    y = height - 37;
  for (const [axis, dx, dy] of referenceAxes(yaw, pitch)) {
    if (Math.hypot(dx, dy) < 0.12) continue;
    svg.append(
      line(x, y, x + 23 * dx, y - 23 * dy, '#cde4e9'),
      label(x + 30 * dx, y - 30 * dy + 4, axis, 'middle')
    );
  }
  const maxLength = Math.min(105, width * 0.22) * mmPerPixel;
  const magnitude = 10 ** Math.floor(Math.log10(maxLength));
  const length = [1, 2, 5]
    .map((n) => n * magnitude)
    .filter((v) => v <= maxLength)
    .at(-1);
  const end = width - 14,
    begin = end - length / mmPerPixel,
    bottom = height - 16;
  svg.append(
    line(begin, bottom, end, bottom, '#fff'),
    line(begin, bottom - 3, begin, bottom + 3, '#fff'),
    line(end, bottom - 3, end, bottom + 3, '#fff'),
    label((begin + end) / 2, bottom - 6, length + ' mm', 'middle')
  );
}

export function surfaceScene(canvas, status, orbit, bounds, spacing) {
  const gl = canvas.getContext('webgl2', { antialias: true, preserveDrawingBuffer: true });
  if (!gl) {
    status.textContent =
      'WebGL 2 is required for the 3D view. The CT and measurements remain available.';
    return null;
  }
  const center = spacing.map((s, k) => ((bounds[0][k] + bounds[1][k]) * s) / 2);
  const radius = 0.54 * Math.hypot(...spacing.map((s, k) => (bounds[1][k] - bounds[0][k] + 1) * s));
  let program, uniform, quad, quadBuffer, texture;
  let sourceMeshes = [],
    gpu = [],
    section = null,
    visible = new Set(),
    cut = 0;
  function init() {
    program = programFor(gl);
    gl.useProgram(program);
    uniform = Object.fromEntries(
      [
        'center',
        'yaw',
        'pitch',
        'radius',
        'aspect',
        'tint',
        'axis',
        'cut',
        'fixedMm',
        'textured',
        'sectionImage'
      ].map((name) => [name, gl.getUniformLocation(program, name)])
    );
    quad = gl.createVertexArray();
    gl.bindVertexArray(quad);
    quadBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 20, 0);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 20, 12);
    texture = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    // Keep the program's sampler complete even before a section is loaded.
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
    gl.bindVertexArray(null);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
  }
  function uploadMeshes() {
    for (const obj of gpu) {
      gl.deleteVertexArray(obj.vao);
      gl.deleteBuffer(obj.verts);
      gl.deleteBuffer(obj.indices);
    }
    gpu = sourceMeshes.map(({ row, positions, indices }) => {
      const vao = gl.createVertexArray();
      gl.bindVertexArray(vao);
      const verts = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, verts);
      gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0);
      gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
      const faces = gl.createBuffer();
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, faces);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
      return { row, vao, verts, indices: faces };
    });
    gl.bindVertexArray(null);
  }
  function uploadSection() {
    if (!section) return;
    const { data, axes, fixed } = section;
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, sectionQuad(axes, bounds, spacing, fixed), gl.DYNAMIC_DRAW);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(
      gl.TEXTURE_2D,
      0,
      gl.RGBA,
      data.width,
      data.height,
      0,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      data.texture
    );
  }
  function draw() {
    if (gl.isContextLost()) return;
    const pixels = Math.min(2, window.devicePixelRatio || 1);
    const w = Math.max(1, Math.round(canvas.clientWidth * pixels)),
      h = Math.max(1, Math.round(canvas.clientHeight * pixels));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    gl.viewport(0, 0, w, h);
    gl.clearColor(0.045, 0.08, 0.105, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(program);
    gl.uniform3fv(uniform.center, center);
    gl.uniform1f(uniform.yaw, (orbit.yaw.valueAsNumber * Math.PI) / 180);
    gl.uniform1f(uniform.pitch, (orbit.pitch.valueAsNumber * Math.PI) / 180);
    gl.uniform1f(uniform.radius, radius / orbit.zoom.valueAsNumber);
    gl.uniform1f(uniform.aspect, w / h);
    const direction = [0, 0, 0];
    if (section) direction[section.axes.normal] = 1;
    gl.uniform3fv(uniform.axis, direction);
    gl.uniform1f(uniform.cut, section ? cut : 0);
    gl.uniform1f(uniform.fixedMm, section ? section.fixed * spacing[section.axes.normal] : 0);
    gl.uniform1i(uniform.textured, 0);
    gl.uniform1i(uniform.sectionImage, 0);
    let triangles = 0;
    for (const { row, vao } of gpu) {
      if (!visible.has(row.code)) continue;
      gl.uniform3fv(
        uniform.tint,
        row.color.map((x) => x / 255)
      );
      gl.bindVertexArray(vao);
      gl.drawElements(gl.TRIANGLES, row.mesh.triangles * 3, gl.UNSIGNED_INT, 0);
      triangles += row.mesh.triangles;
    }
    if (section && cut !== 0) {
      gl.uniform1i(uniform.textured, 1);
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.bindVertexArray(quad);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }
    gl.bindVertexArray(null);
    drawReference(
      document.getElementById('model-reference'),
      canvas.clientWidth,
      canvas.clientHeight,
      (2 * radius) / (orbit.zoom.valueAsNumber * canvas.clientHeight),
      (orbit.yaw.valueAsNumber * Math.PI) / 180,
      (orbit.pitch.valueAsNumber * Math.PI) / 180
    );
    if (gpu.length)
      status.textContent =
        visible.size +
        ' visible regions · ' +
        triangles.toLocaleString('en-US') +
        ' source triangles' +
        (cut && section
          ? ' · cut at the CT section.'
          : cut
            ? ' · intact while the CT section is unavailable.'
            : '.');
  }
  init();
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    status.textContent = 'The graphics context was lost. Waiting for recovery.';
  });
  canvas.addEventListener('webglcontextrestored', () => {
    gpu = [];
    init();
    uploadMeshes();
    uploadSection();
    draw();
  });
  new ResizeObserver(draw).observe(canvas);
  return {
    setMeshes(items) {
      sourceMeshes = items;
      if (!gl.isContextLost()) {
        uploadMeshes();
        draw();
      }
    },
    update(data, axes, fixed, selected, cutDirection) {
      visible = new Set(selected);
      cut = cutDirection;
      section = data ? { data, axes, fixed } : null;
      if (!gl.isContextLost()) {
        uploadSection();
        draw();
      }
    },
    draw
  };
}

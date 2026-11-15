'use strict';

const get = id => document.getElementById(id);
const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0);

async function readSource() {
  const [manifest, image] = await Promise.all(['source.json', 't2-int16.gz'].map(async file => {
    const response = await fetch(file);
    if (!response.ok) throw Error('Source file unavailable');
    return response;
  }));
  const source = await manifest.json();
  const bytes = await new Response(image.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  const [depth, height, width] = source.shapeSliceRowColumn;
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
    .map(byte => byte.toString(16).padStart(2, '0')).join('');
  if (digest !== source.decodedInt16SHA256 || bytes.byteLength !== 2 * width * height * depth) {
    throw Error('MRI samples differ from the source receipt');
  }

  const positions = source.frames.map(frame => frame.imagePositionPatient.map(Number));
  const orientation = source.imageOrientationPatient.map(Number);
  const [rowSpacing, columnSpacing] = source.pixelSpacingRowColumnMm.map(Number);
  const columns = orientation.slice(0, 3).map(value => value * columnSpacing);
  const rows = orientation.slice(3).map(value => value * rowSpacing);
  const cc = dot(columns, columns), rr = dot(rows, rows), cr = dot(columns, rows);
  const determinant = cc * rr - cr * cr;
  const outlines = source.rois.flatMap(roi => roi.contours.map(contour => {
    const plane = contour.sliceIndex, origin = positions[plane];
    const coordinates = contour.lpsDecimalStrings.map(Number);
    if (!origin || coordinates.length !== 3 * contour.pointCount) throw Error('Invalid source contour');
    const points = [];
    for (let i = 0; i < coordinates.length; i += 3) points.push(coordinates.slice(i, i + 3));
    const pixels = points.map(point => {
      const delta = point.map((value, i) => value - origin[i]);
      const c = dot(delta, columns), r = dot(delta, rows);
      const x = (rr * c - cr * r) / determinant, y = (cc * r - cr * c) / determinant;
      const residual = Math.hypot(...delta.map((value, i) => value - x * columns[i] - y * rows[i]));
      if (!(residual < 0.001 && x >= -0.5 && x <= width - 0.5 && y >= -0.5 && y <= height - 0.5)) {
        throw Error('Contour differs from its referenced section');
      }
      return [x + 0.5, y + 0.5];
    });
    return {roi: roi.roiNumber, color: 'rgb(' + roi.sourceRGB.join(',') + ')', plane, points, pixels};
  }));
  const raw = new DataView(bytes);
  const samples = Int16Array.from({length: bytes.byteLength / 2}, (_, i) => raw.getInt16(i * 2, true));
  return {width, height, depth, samples, outlines};
}

function stroke(ctx, points, project, color) {
  ctx.strokeStyle = color;
  ctx.beginPath();
  for (const [index, point] of points.entries()) {
    const [x, y] = project(point);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.stroke();
}

function renderReader({width, height, depth, samples, outlines}) {
  const mri = get('mri'), stack = get('stack'), slice = get('slice');
  const image = mri.getContext('2d'), model = stack.getContext('2d');
  const raster = image.createImageData(width, height);
  const allPoints = outlines.flatMap(outline => outline.points);
  const bounds = [0, 1, 2].map(i => {
    const values = allPoints.map(point => point[i]);
    return [Math.min(...values), Math.max(...values)];
  });
  const centre = bounds.map(([min, max]) => (min + max) / 2);
  const scale = 400 / Math.hypot(...bounds.map(([min, max]) => max - min));
  const section = () => slice.valueAsNumber - 1;
  const visible = () => outlines.filter(outline => get('roi-' + outline.roi).checked);

  function drawMRI() {
    const plane = section();
    const black = get('black').valueAsNumber, white = get('white').valueAsNumber;
    const valid = Number.isInteger(black) && Number.isInteger(white) && black >= 0 && white <= 2719 && black < white;
    get('section').textContent = 'Section ' + (plane + 1) + ' of ' + depth;
    get('sample').textContent = '';
    get('window-status').textContent = valid ? '' : 'Enter whole numbers with 0 ≤ black < white ≤ 2719.';
    mri.hidden = !valid;
    if (!valid) return;
    const offset = plane * width * height;
    for (let i = 0; i < width * height; i++) {
      const gray = 255 * (samples[offset + i] - black) / (white - black);
      raster.data[4 * i] = raster.data[4 * i + 1] = raster.data[4 * i + 2] = gray;
      raster.data[4 * i + 3] = 255;
    }
    image.putImageData(raster, 0, 0);
    image.lineWidth = 0.8;
    for (const outline of visible()) {
      if (outline.plane === plane) stroke(image, outline.pixels, point => point, outline.color);
    }
  }

  function drawStack() {
    const plane = section(), shown = visible();
    const yaw = get('yaw').valueAsNumber * Math.PI / 180;
    const pitch = get('pitch').valueAsNumber * Math.PI / 180;
    const cosYaw = Math.cos(yaw), sinYaw = Math.sin(yaw);
    const cosPitch = Math.cos(pitch), sinPitch = Math.sin(pitch);
    function project(point) {
      const [x, y, z] = point.map((value, i) => value - centre[i]);
      const horizontal = cosYaw * x - sinYaw * y;
      const depth = sinYaw * x + cosYaw * y;
      return [320 + scale * horizontal, 240 - scale * (cosPitch * z - sinPitch * depth)];
    }
    model.fillStyle = '#111a20';
    model.fillRect(0, 0, stack.width, stack.height);
    model.globalAlpha = 0.4;
    model.lineWidth = 1;
    for (const outline of shown) {
      if (outline.plane !== plane) stroke(model, outline.points, project, outline.color);
    }
    model.globalAlpha = 1;
    model.lineWidth = 2;
    const selected = shown.filter(outline => outline.plane === plane);
    for (const outline of selected) stroke(model, outline.points, project, outline.color);
    get('contour-status').textContent = selected.length + ' visible outlines on this section. ' +
      shown.length + ' of ' + outlines.length + ' source outlines visible in the stack.';
  }

  function draw() {
    drawMRI();
    drawStack();
  }

  for (const id of ['slice', 'roi-1', 'roi-2']) get(id).addEventListener('input', draw);
  for (const id of ['black', 'white']) get(id).addEventListener('input', drawMRI);
  for (const id of ['yaw', 'pitch']) get(id).addEventListener('input', drawStack);
  mri.addEventListener('keydown', event => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    if (event.key === 'ArrowLeft') slice.stepDown();
    else slice.stepUp();
    draw();
  });
  mri.addEventListener('click', event => {
    const box = mri.getBoundingClientRect();
    const x = Math.floor((event.clientX - box.left) * width / box.width);
    const y = Math.floor((event.clientY - box.top) * height / box.height);
    if (x < 0 || x >= width || y < 0 || y >= height) return;
    const value = samples[(section() * height + y) * width + x];
    get('sample').textContent = 'Column ' + (x + 1) + ', row ' + (y + 1) + ' · source intensity ' + value;
  });
  draw();
}

async function start() {
  get('retry').hidden = true;
  get('status').textContent = 'Loading MRI and original contours…';
  try {
    const source = await readSource();
    renderReader(source);
    get('reader').hidden = false;
    get('status').textContent = 'Source MRI and ' + source.outlines.length + ' contours loaded.';
  } catch {
    get('status').textContent = 'The MRI and contour files could not be verified.';
    get('retry').hidden = false;
  }
}

get('retry').addEventListener('click', start);
start();

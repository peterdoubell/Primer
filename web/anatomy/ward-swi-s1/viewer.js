import { planeGeometry, pixelToVoxel, voxelToWorld } from '../bonn-fcd-case4/native-core.js';

import { installTracingMesh } from './mesh.js';

const metadataHash = '8fe939414aa7f48131295f5ed7998c726cd38821aa2ed741e3e791f8fbd5955e';
const get = id => document.getElementById(id);
const points = [114, 70, 43];
const sequence = get('sequence');
const mode = get('mode');
const low = get('low');
const high = get('high');
const status = get('status');
const retry = get('retry');
const cache = new Map();
const pending = new Map();
const showMesh = get('show-mesh');
let metadata;
let mesh;

const planes = ['Sagittal', 'Coronal', 'Axial'].map((name, axis) => {
  const section = document.createElement('section');
  section.innerHTML = `<h2>${name}</h2><label>Slice <input type="range" min="0" value="${points[axis]}" disabled></label>
    <p class="orientation"></p><canvas role="img"></canvas>`;
  const slider = section.querySelector('input');
  const canvas = section.querySelector('canvas');
  const orientation = section.querySelector('.orientation');
  slider.addEventListener('input', () => {
    points[axis] = slider.valueAsNumber;
    render();
  });
  canvas.addEventListener('click', event => {
    if (get('controls').disabled) return;
    const bounds = canvas.getBoundingClientRect();
    const x = Math.floor((event.clientX - bounds.left) * canvas.width / bounds.width);
    const y = Math.floor((event.clientY - bounds.top) * canvas.height / bounds.height);
    if (x < 0 || y < 0 || x >= canvas.width || y >= canvas.height) return;
    const volume = { shape: metadata.shape, affine: metadata.sources[sequence.value].affine };
    points.splice(0, 3, ...pixelToVoxel(volume, axis, points[axis], x, y));
    render();
  });
  get('planes').append(section);
  return { name, axis, canvas, slider, orientation };
});

async function digest(bytes) {
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(hash), n => n.toString(16).padStart(2, '0')).join('');
}

async function readBounded(stream, bytes) {
  const reader = stream.getReader();
  const buffer = new Uint8Array(bytes);
  let offset = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (offset + value.length > bytes) throw Error('Source exceeds the recorded size');
      buffer.set(value, offset);
      offset += value.length;
    }
  } finally {
    await reader.cancel();
  }
  if (offset !== bytes) throw Error('Source is incomplete');
  return buffer;
}

async function loadVolume(role) {
  const source = metadata.sources[role];
  const response = await fetch(source.name, { signal: AbortSignal.timeout(90000) });
  if (!response.ok) throw Error(role + ' returned HTTP ' + response.status);
  const gzip = await readBounded(response.body, source.bytes);
  if (await digest(gzip) !== source.sha256) throw Error(role + ' file checksum differs');
  const raw = await readBounded(new Blob([gzip]).stream().pipeThrough(new DecompressionStream('gzip')), source.decodedBytes);
  if (await digest(raw) !== source.decodedSha256) throw Error(role + ' decoded checksum differs');
  const header = new DataView(raw.buffer);
  const voxelOffset = header.getFloat32(108, true);
  const shape = metadata.shape;
  const length = shape.reduce((product, count) => product * count, 1);
  if (header.getInt32(0, true) !== 348 || header.getInt16(40, true) !== 3 ||
      shape.some((size, axis) => header.getInt16(42 + 2 * axis, true) !== size) ||
      header.getInt16(70, true) !== source.datatype || header.getInt16(72, true) !== source.sampleBytes * 8 ||
      voxelOffset !== 352 || header.getFloat32(112, true) !== 1 || header.getFloat32(116, true) !== 0 ||
      voxelOffset + length * source.sampleBytes !== raw.byteLength) throw Error(role + ' header differs');
  const samples = new DataView(raw.buffer, voxelOffset);
  const methods = { SWI: 'getInt16', QSM: 'getFloat64', Vein: 'getFloat32' };
  const result = (i, j, k) => samples[methods[role]]((i + shape[0] * (j + shape[1] * k)) * source.sampleBytes, true);
  cache.set(role, result);
  return result;
}

function sourceVolume(role) {
  if (cache.has(role)) return Promise.resolve(cache.get(role));
  if (!pending.has(role)) pending.set(role, loadVolume(role).finally(() => pending.delete(role)));
  return pending.get(role);
}

function render() {
  const source = sequence.value;
  const role = mode.value;
  const lower = low.valueAsNumber;
  const upper = high.valueAsNumber;
  const sample = cache.get(source);
  const vein = cache.get('Vein');
  if (!sample || role !== 'mri' && !vein) return;
  if (!Number.isFinite(lower) || !Number.isFinite(upper) || upper <= lower) {
    status.textContent = 'Window high must exceed window low.';
    return;
  }
  const volume = { shape: metadata.shape, affine: metadata.sources[source].affine };
  for (const { name, axis, canvas, slider, orientation } of planes) {
    const geometry = planeGeometry(volume, axis);
    const { width, height, uAxis, vAxis, spacingU, spacingV, edges } = geometry;
    canvas.width = width;
    canvas.height = height;
    canvas.style.aspectRatio = (width * spacingU) / (height * spacingV);
    const context = canvas.getContext('2d');
    const image = context.createImageData(width, height);
    const voxel = [...points];
    for (let y = 0; y < height; y++) {
      voxel[vAxis] = height - 1 - y;
      for (let x = 0; x < width; x++) {
        voxel[uAxis] = x;
        const offset = (y * width + x) * 4;
        const marked = role !== 'mri' && vein(...voxel) === 1;
        const grey = role === 'mask' ? 0 : Math.round(255 * Math.max(0, Math.min(1, (sample(...voxel) - lower) / (upper - lower))));
        if (marked) {
          image.data.set(role === 'mask' ? [255, 175, 82, 255] :
            [grey * 0.5 + 127.5, grey * 0.5 + 87.5, grey * 0.5 + 41, 255], offset);
        } else {
          image.data.set([grey, grey, grey, 255], offset);
        }
      }
    }
    context.putImageData(image, 0, 0);
    context.strokeStyle = '#57d8ff';
    const x = points[uAxis] + 0.5;
    const y = height - points[vAxis] - 0.5;
    context.beginPath();
    context.moveTo(x - 9, y); context.lineTo(x - 3, y);
    context.moveTo(x + 3, y); context.lineTo(x + 9, y);
    context.moveTo(x, y - 9); context.lineTo(x, y - 3);
    context.moveTo(x, y + 3); context.lineTo(x, y + 9);
    context.stroke();
    slider.max = volume.shape[axis] - 1;
    slider.value = points[axis];
    slider.setAttribute('aria-label', name + ' slice');
    orientation.textContent = 'Left/right ' + edges.slice(0, 2).join('/') + ' · top/bottom ' + edges.slice(2).join('/');
    canvas.setAttribute('aria-label', name + ' ' + source + ' slice ' + points[axis] + ', ' + mode.selectedOptions[0].textContent);
  }
  const world = voxelToWorld(volume, points).map(value => value.toFixed(2));
  const value = sample(...points);
  get('cursor').textContent = 'Voxel ' + points.join(', ') + ' · image RAS ' + world.join(', ') +
    ' mm · ' + source + ' value ' + (source === 'SWI' ? value : value.toPrecision(8)) +
    (role === 'mri' ? '' : ' · source tracing ' + (vein(...points) === 1 ? 'marked' : 'unmarked'));
  mesh?.refreshSection();
  status.textContent = 'Verified ' + source + (role === 'mri' ? '' : ' and vein tracing') + '.';
}

async function prepare() {
  get('controls').disabled = true;
  for (const { canvas, slider } of planes) {
    slider.disabled = true;
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    canvas.removeAttribute('aria-label');
  }
  get('cursor').textContent = '';
  retry.hidden = true;
  status.textContent = 'Verifying source files…';
  try {
    if (!metadata) {
      const response = await fetch('source.json', { signal: AbortSignal.timeout(15000) });
      if (!response.ok) throw Error('Source metadata unavailable');
      const bytes = await response.arrayBuffer();
      if (await digest(bytes) !== metadataHash) throw Error('Source metadata checksum differs');
      metadata = JSON.parse(new TextDecoder().decode(bytes));
    }
    const wanted = mode.value === 'mri' ? [sequence.value] : [sequence.value, 'Vein'];
    await Promise.all(wanted.map(sourceVolume));
    get('controls').disabled = false;
    showMesh.disabled = false;
    for (const { slider } of planes) slider.disabled = false;
    render();
  } catch (error) {
    status.textContent = 'Source unavailable. ' + error.message;
    retry.hidden = false;
  }
}

showMesh.addEventListener('click', async () => {
  const meshStatus = get('mesh-status');
  showMesh.disabled = true;
  meshStatus.textContent = 'Verifying vein tracing…';
  try {
    const sample = await sourceVolume('Vein');
    mesh = installTracingMesh(metadata.shape, metadata.sources.SWI.affine, sample, points);
    showMesh.hidden = true;
  } catch (error) {
    meshStatus.textContent = '3D unavailable. ' + error.message;
    showMesh.disabled = false;
  }
});

sequence.addEventListener('change', () => {
  [low.value, high.value] = sequence.value === 'SWI' ? [0, 360] : [-0.12, 0.12];
  prepare();
});
mode.addEventListener('change', prepare);
for (const control of [low, high]) control.addEventListener('change', render);
retry.addEventListener('click', prepare);

const from = new URLSearchParams(location.search).get('from');
const returnLink = get('return');
if (['ra.venous-sinus-thrombosis', 'ra.intracranial-haemorrhage', 'rad.5.intracranial-haemorrhage'].includes(from)) {
  returnLink.search = '?from=' + encodeURIComponent(from);
}
prepare();

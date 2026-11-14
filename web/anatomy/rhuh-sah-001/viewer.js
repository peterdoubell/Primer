'use strict';

const get = id => document.getElementById(id);
const canvas = get('ct');
if (new URLSearchParams(location.search).get('from') === 'ra.intracranial-haemorrhage') {
  const back = get('return-context');
  back.href = '/app/#/radiology/ra.intracranial-haemorrhage';
  back.textContent = 'Return to the haemorrhage reporting reference';
}

const plane = get('plane');
const slider = get('slice');
const layouts = {
  axial: {normal: 2, horizontal: 0, vertical: 1, reverseX: true,
    label: 'Axial. Patient right at left and anterior at top.'},
  coronal: {normal: 1, horizontal: 0, vertical: 2, reverseX: true,
    label: 'Coronal. Patient right at left and superior at top.'},
  sagittal: {normal: 0, horizontal: 1, vertical: 2, reverseX: false,
    label: 'Sagittal. Anterior at right and superior at top.'},
};
const lastSections = new Map();
let volume, ct, mask, current;

async function verify(bytes, expected) {
  const hash = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  const actual = Array.from(hash, byte => byte.toString(16).padStart(2, '0')).join('');
  if (actual !== expected) throw Error('Source checksum differs');
}

async function read(file, expected) {
  const response = await fetch(file);
  if (!response.ok) throw Error('Missing source data');
  const body = file.endsWith('.gz')
    ? new Response(response.body.pipeThrough(new DecompressionStream('gzip'))) : response;
  const data = await body.arrayBuffer();
  await verify(data, expected);
  return data;
}

async function loadArray(manifest, sampleBytes) {
  const count = volume.shape.reduce((size, axis) => size * axis, 1);
  const assembled = new Uint8Array(count * sampleBytes);
  let cursor = 0;
  for (const row of manifest.chunks) {
    const data = await read(row.file, row.sha256);
    if (row.offset !== cursor || data.byteLength !== row.count * sampleBytes) throw Error('Incorrect chunk layout');
    assembled.set(new Uint8Array(data), cursor * sampleBytes);
    cursor += row.count;
  }
  if (cursor !== count) throw Error('Incomplete source array');
  await verify(assembled, manifest.sha256);
  return assembled;
}

function draw() {
  if (!ct || !mask) return;
  canvas.hidden = true;
  current = null;
  get('sample').textContent = '';
  const black = get('black').valueAsNumber;
  const white = get('white').valueAsNumber;
  if (!Number.isFinite(black) || !Number.isFinite(white) || white <= black) {
    get('status').textContent = 'Set a white point above the black point.';
    return;
  }
  const {normal, horizontal, vertical, reverseX, label} = layouts[plane.value];
  const fixed = slider.valueAsNumber;
  const [nx, ny] = volume.shape;
  const width = volume.shape[horizontal];
  const height = volume.shape[vertical];
  const steps = [1, nx, nx * ny];
  const start = fixed * steps[normal] + (reverseX ? (width - 1) * steps[horizontal] : 0)
    + (height - 1) * steps[vertical];
  const xStep = (reverseX ? -1 : 1) * steps[horizontal];
  const yStep = -steps[vertical];
  const index = (x, y) => start + x * xStep + y * yStep;
  const labelled = (x, y) => x >= 0 && x < width && y >= 0 && y < height && mask[index(x, y)] === 1;
  const mode = get('overlay').value;
  canvas.width = width;
  canvas.height = height;
  canvas.setAttribute('aria-label', label);
  const context = canvas.getContext('2d');
  const raster = context.createImageData(width, height);
  let count = 0;
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const selected = labelled(x, y);
      if (selected) count++;
      const value = ct.getFloat32(4 * index(x, y), true);
      const gray = 255 * (value - black) / (white - black);
      const edge = selected && mode === 'outline' &&
        (!labelled(x - 1, y) || !labelled(x + 1, y) || !labelled(x, y - 1) || !labelled(x, y + 1));
      const fill = selected && mode === 'fill';
      raster.data.set(edge ? [255, 143, 118, 255] :
        fill ? [.55 * gray + 115, .55 * gray + 64, .55 * gray + 53, 255] : [gray, gray, gray, 255],
        4 * (x + y * width));
    }
  }
  context.putImageData(raster, 0, 0);
  current = {index, width, height, labelled};
  canvas.hidden = false;
  get('section').textContent = (fixed + 1) + ' / ' + volume.shape[normal];
  get('orientation').textContent = label + ' Select a pixel to inspect the source value. Use arrow keys to change section.';
  get('status').textContent = 'Verified source section. ' + count.toLocaleString() + ' labelled pixels.';
}

function selectPlane() {
  if (!volume || !ct) return;
  const axis = layouts[plane.value].normal;
  slider.max = volume.shape[axis] - 1;
  slider.value = lastSections.get(axis) ?? volume.initial[axis];
  draw();
}

async function start() {
  get('retry').hidden = true;
  get('status').textContent = 'Verifying CT and mask…';
  try {
    const metadata = await read('volume.json', document.querySelector('main').dataset.volumeSha256);
    volume = JSON.parse(new TextDecoder().decode(metadata));
    const [intensities, labels] = await Promise.all([loadArray(volume.ct, 4), loadArray(volume.mask, 1)]);
    ct = new DataView(intensities.buffer);
    mask = labels;
    slider.disabled = false;
    selectPlane();
  } catch {
    get('status').textContent = 'The CT and mask could not be verified.';
    get('retry').hidden = false;
  }
}

plane.addEventListener('change', selectPlane);
slider.addEventListener('input', () => {
  lastSections.set(layouts[plane.value].normal, slider.valueAsNumber);
  draw();
});
for (const id of ['black', 'white', 'overlay']) get(id).addEventListener('input', draw);
get('retry').addEventListener('click', start);
canvas.addEventListener('keydown', event => {
  if (!current || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'ArrowLeft') slider.stepDown();
  else slider.stepUp();
  slider.dispatchEvent(new Event('input'));
});
canvas.addEventListener('click', event => {
  if (!current) return;
  const bounds = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - bounds.left) * current.width / bounds.width);
  const y = Math.floor((event.clientY - bounds.top) * current.height / bounds.height);
  if (x < 0 || y < 0 || x >= current.width || y >= current.height) return;
  const value = ct.getFloat32(4 * current.index(x, y), true);
  get('sample').textContent = 'Source intensity ' + value.toPrecision(5) +
    (current.labelled(x, y) ? ' · Within the expert mask' : ' · Outside the expert mask');
});
start();

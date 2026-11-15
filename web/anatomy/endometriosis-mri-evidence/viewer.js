import { installGeometry } from './stack-geometry.js';

const get = id => document.getElementById(id);
const selection = get('figure');
const image = get('image');
const figureStatus = get('figure-status');
const retryFigure = get('retry-figure');
const stackStatus = get('stack-status');
const stackButton = get('load-stack');
const canvas = get('plane');
const slice = get('slice');
const query = new URLSearchParams(location.search);
const figureHash = '2455eec29a955c76d432ccf5314e4a27d8b3394a8458b47ceb1a82f18d2eacce';
const stackHash = '4d48058ac5a0684d830a2a866354d3daac1133bca233c26797da175dd37176dd';
const figureCache = new Map();
let figures;
let stack;
let metadata;
let spatialView;
let spatialInitialised = false;
let cursor = [160, 160];

const digest = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
  byte => byte.toString(16).padStart(2, '0')).join('');

async function checked(url, sha256, exactLength) {
  const response = await fetch(url, { signal: AbortSignal.timeout(60000) });
  if (!response.ok) throw Error('The source file is unavailable.');
  const bytes = await response.arrayBuffer();
  if ((exactLength !== undefined && bytes.byteLength !== exactLength) || await digest(bytes) !== sha256) {
    throw Error('The source file checksum differs.');
  }
  return bytes;
}

async function readManifest(url, sha256) {
  return JSON.parse(new TextDecoder().decode(await checked(url, sha256)));
}

function resizeImage() {
  image.style.width = get('zoom').value === 'fit' ? '100%' :
    image.naturalWidth * Number(get('zoom').value) + 'px';
}

function imageURL(bytes) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(Error('The source image could not be read.'));
    reader.readAsDataURL(new Blob([bytes], {type:'image/png'}));
  });
}

async function showFigure() {
  selection.disabled = true;
  image.hidden = true;
  retryFigure.hidden = true;
  get('caption').textContent = '';
  get('figure-key').replaceChildren();
  figureStatus.textContent = 'Verifying the published figure…';
  try {
    if (!figures) {
      figures = (await readManifest('figures.json', figureHash)).figures;
      selection.replaceChildren(...figures.map(row => new Option(row.title, row.id)));
      const requested = query.get('figure');
      if (figures.some(row => row.id === requested)) selection.value = requested;
    }
    const figure = figures.find(row => row.id === selection.value);
    if (!figureCache.has(figure.id)) {
      const bytes = await checked(figure.file, figure.sha256, figure.bytes);
      figureCache.set(figure.id, await imageURL(bytes));
    }
    image.src = figureCache.get(figure.id);
    await image.decode();
    if (image.naturalWidth !== figure.width || image.naturalHeight !== figure.height) {
      throw Error('The figure dimensions differ from the publisher copy.');
    }
    image.alt = figure.title + ' · original Figure ' + figure.id;
    image.hidden = false;
    resizeImage();
    image.parentElement.scrollTo(0, 0);
    get('caption').textContent = figure.caption;
    get('figure-key').replaceChildren(...figure.markers.map(([mark, finding]) => {
      const row = document.createElement('tr');
      const key = document.createElement('th');
      key.scope = 'row';
      key.textContent = mark;
      const meaning = document.createElement('td');
      meaning.textContent = finding;
      row.append(key, meaning);
      return row;
    }));
    figureStatus.textContent = 'Original Figure ' + figure.id + ' · ' + figure.width + ' × ' + figure.height + ' source pixels.';
  } catch (error) {
    figureStatus.textContent = error.message;
    retryFigure.hidden = false;
  } finally {
    selection.disabled = !figures;
  }
}

async function decodeStack(bytes, expected) {
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  const reader = stream.getReader();
  const raw = new Uint8Array(expected);
  let offset = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (offset + value.length > expected) throw Error('The decoded stack exceeds the recorded size.');
      raw.set(value, offset);
      offset += value.length;
    }
  } finally {
    await reader.cancel();
  }
  if (offset !== expected) throw Error('The decoded stack is incomplete.');
  return raw;
}

function drawPlane() {
  const low = get('low').valueAsNumber;
  const high = get('high').valueAsNumber;
  if (!Number.isFinite(low) || !Number.isFinite(high) || high <= low) {
    stackStatus.textContent = 'Window high must exceed window low.';
    return;
  }
  const [count, rows, columns] = metadata.shapeStackRowsColumns;
  const index = slice.valueAsNumber;
  const plane = metadata.planes[index];
  const start = index * rows * columns;
  const context = canvas.getContext('2d');
  const image = context.createImageData(columns, rows);
  for (let i = 0; i < rows * columns; i++) {
    const grey = Math.round(255 * Math.max(0, Math.min(1, (stack[start + i] - low) / (high - low))));
    image.data[4 * i] = grey;
    image.data[4 * i + 1] = grey;
    image.data[4 * i + 2] = grey;
    image.data[4 * i + 3] = 255;
  }
  context.putImageData(image, 0, 0);
  const [x, y] = cursor;
  context.strokeStyle = '#69dcf3';
  context.strokeRect(x - 3.5, y - 3.5, 8, 8);
  const [rowSpacing, columnSpacing] = metadata.pixelSpacingRowsColumnsMm;
  const world = plane.originLpsMm.map((origin, axis) => origin +
    x * columnSpacing * metadata.directionForIncreasingColumnLps[axis] +
    y * rowSpacing * metadata.directionForIncreasingRowLps[axis]);
  const label = 'Slice ' + (index + 1) + ' of ' + count + ' · ' + plane.positionAlongNormalMm.toFixed(1) + ' mm along the acquisition normal';
  get('slice-number').textContent = label;
  slice.setAttribute('aria-valuetext', label);
  get('sample').textContent = 'Column ' + x + ', row ' + y + ' · LPS ' +
    world.map(value => value.toFixed(2)).join(', ') + ' mm · stored value ' + stack[start + y * columns + x];
  canvas.setAttribute('aria-label', label + '. Anterior at left, superior at top. Use arrow keys to move the pixel cursor.');
  stackStatus.textContent = 'Original sagittal samples verified.';
  if (get('geometry').open) spatialView?.draw();
}

async function loadStack() {
  stackButton.disabled = true;
  stackStatus.textContent = 'Verifying the acquired samples…';
  try {
    metadata = await readManifest('sagittal-source.json', stackHash);
    const compressed = await checked(metadata.file, metadata.sha256, metadata.bytes);
    const raw = await decodeStack(compressed, metadata.decodedBytes);
    if (await digest(raw) !== metadata.decodedSha256) throw Error('The decoded samples differ.');
    stack = new Uint16Array(raw.buffer);
    const [, rows, columns] = metadata.shapeStackRowsColumns;
    canvas.width = columns;
    canvas.height = rows;
    document.querySelector('.ruler span').style.width =
      (20 / (columns * metadata.pixelSpacingRowsColumnsMm[1]) * 100) + '%';
    get('acquired').hidden = false;
    stackButton.hidden = true;
    drawPlane();
    slice.focus();
  } catch (error) {
    stackStatus.textContent = error.message;
    stackButton.disabled = false;
  }
}

canvas.addEventListener('click', event => {
  const rect = canvas.getBoundingClientRect();
  cursor = [
    Math.min(canvas.width - 1, Math.max(0, Math.floor((event.clientX - rect.left) * canvas.width / rect.width))),
    Math.min(canvas.height - 1, Math.max(0, Math.floor((event.clientY - rect.top) * canvas.height / rect.height))),
  ];
  drawPlane();
});
canvas.addEventListener('keydown', event => {
  const delta = {ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[event.key];
  if (!delta) return;
  event.preventDefault();
  cursor = cursor.map((value, axis) => Math.min((axis === 0 ? canvas.width : canvas.height) - 1,
    Math.max(0, value + delta[axis])));
  drawPlane();
});
get('geometry').addEventListener('toggle', event => {
  if (!event.currentTarget.open || !stack) return;
  if (spatialInitialised) {
    spatialView?.draw();
    return;
  }
  spatialInitialised = true;
  spatialView = installGeometry(metadata, stack, () => ({
    slice: slice.valueAsNumber,
    low: get('low').valueAsNumber,
    high: get('high').valueAsNumber,
  }));
});
stackButton.addEventListener('click', loadStack);
slice.addEventListener('input', drawPlane);
for (const id of ['low','high']) get(id).addEventListener('change', drawPlane);
selection.addEventListener('change', showFigure);
get('zoom').addEventListener('change', resizeImage);
retryFigure.addEventListener('click', showFigure);

if (query.get('from') === 'rad.5.uterine-mr') {
  const link = get('return');
  link.href = '/app/#/node/rad.5.uterine-mr';
  link.textContent = 'Return to Uterus and Cervix';
}
showFigure();

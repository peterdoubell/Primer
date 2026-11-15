'use strict';

const get = id => document.getElementById(id);
const cache = new Map();
const canvas = get('ct');
if (new URLSearchParams(location.search).get('from') === 'ra.intracranial-haemorrhage') {
  const back = get('return-context');
  back.href = '/app/#/radiology/ra.intracranial-haemorrhage';
  back.textContent = 'Return to the haemorrhage reporting reference';
}

let volume, current, generation = 0;

async function verifiedBytes(file, sha256) {
  const response = await fetch(file);
  if (!response.ok) throw Error('Missing source data');
  const body = file.endsWith('.gz')
    ? new Response(response.body.pipeThrough(new DecompressionStream('gzip')))
    : response;
  const bytes = await body.arrayBuffer();
  const hash = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  const actual = Array.from(hash, byte => byte.toString(16).padStart(2, '0')).join('');
  if (actual !== sha256) throw Error('Source checksum differs');
  return bytes;
}

function loadChunk(chunk) {
  if (!cache.has(chunk.file)) {
    const task = verifiedBytes(chunk.file, chunk.sha256).then(bytes => {
      if (bytes.byteLength !== chunk.decodedBytes) throw Error('Incorrect chunk size');
      return new DataView(bytes);
    });
    cache.set(chunk.file, task);
    task.catch(() => { if (cache.get(chunk.file) === task) cache.delete(chunk.file); });
    if (cache.size > 4) cache.delete(cache.keys().next().value);
  }
  return cache.get(chunk.file);
}

async function draw() {
  const attempt = ++generation;
  const index = get('slice').valueAsNumber;
  const black = get('black').valueAsNumber;
  const white = get('white').valueAsNumber;
  canvas.hidden = true;
  current = null;
  get('sample').textContent = '';
  get('retry').hidden = true;
  get('section').textContent = index + ' / ' + volume.shape[2];
  if (!Number.isFinite(black) || !Number.isFinite(white) || white <= black) {
    get('status').textContent = 'Set a white point above the black point.';
    return;
  }
  get('status').textContent = 'Verifying source section…';
  try {
    const chunk = volume.chunks.find(row => index >= row.firstSection && index < row.firstSection + row.sections);
    const stored = await loadChunk(chunk);
    if (attempt !== generation) return;
    const [width, height] = volume.shape;
    const offset = (index - chunk.firstSection) * width * height;
    const section = volume.sections[index - 1];
    const attenuation = pixel => stored.getInt16(2 * (offset + pixel), true) * section.slope + section.intercept;
    const context = canvas.getContext('2d');
    const raster = context.createImageData(width, height);
    for (let pixel = 0; pixel < width * height; pixel++) {
      const gray = 255 * (attenuation(pixel) - black) / (white - black);
      const channel = 4 * pixel;
      raster.data[channel] = gray;
      raster.data[channel + 1] = gray;
      raster.data[channel + 2] = gray;
      raster.data[channel + 3] = 255;
    }
    context.putImageData(raster, 0, 0);
    if (get('overlay').checked) {
      const layers = document.querySelectorAll('.layer');
      const contours = [[section.contour, '#ff8f76'], [section.arteryContour, '#6ec8ff']];
      for (const [index, [segments, color]] of contours.entries()) {
        if (!layers[index].checked) continue;
        context.beginPath();
        context.strokeStyle = color;
        context.lineWidth = 0.85;
        for (const [[x1, y1], [x2, y2]] of segments) {
          context.moveTo(x1 + 0.5, y1 + 0.5);
          context.lineTo(x2 + 0.5, y2 + 0.5);
        }
        context.stroke();
      }
    }
    current = {width, height, attenuation};
    canvas.hidden = false;
    get('status').textContent = section.contour.length
      ? 'Verified source section. The sac surface intersects this plane.'
      : 'Verified source section.';
  } catch {
    if (attempt !== generation) return;
    get('status').textContent = 'The source section could not be verified.';
    get('retry').hidden = false;
  }
}

async function start() {
  get('retry').hidden = true;
  try {
    const bytes = await verifiedBytes('volume.json', document.querySelector('main').dataset.volumeSha256);
    volume = JSON.parse(new TextDecoder().decode(bytes));
    get('slice').max = volume.shape[2];
    get('slice').value = volume.initialSection;
    get('slice').disabled = false;
    get('jump').disabled = false;
    await draw();
  } catch {
    get('status').textContent = 'The CTA inventory could not be verified.';
    get('retry').hidden = false;
  }
}

for (const id of ['slice', 'black', 'white', 'overlay']) {
  get(id).addEventListener('input', () => { if (volume) draw(); });
}
for (const layer of document.querySelectorAll('.layer')) {
  layer.addEventListener('input', () => { if (volume) draw(); });
}
get('jump').addEventListener('click', () => {
  get('slice').value = volume.initialSection;
  draw();
});
get('zoom').addEventListener('change', () => {
  const zoom = get('zoom').value;
  canvas.style.width = zoom === 'fit' ? '' : canvas.width * Number(zoom) + 'px';
});
get('retry').addEventListener('click', () => volume ? draw() : start());
canvas.addEventListener('keydown', event => {
  if (!current || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'ArrowLeft') get('slice').stepDown();
  else get('slice').stepUp();
  draw();
});
canvas.addEventListener('click', event => {
  if (!current) return;
  const bounds = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - bounds.left) * current.width / bounds.width);
  const y = Math.floor((event.clientY - bounds.top) * current.height / bounds.height);
  if (x < 0 || y < 0 || x >= current.width || y >= current.height) return;
  get('sample').textContent = current.attenuation(x + y * current.width) + ' source intensity';
});
start();

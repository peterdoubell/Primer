import {sha, decode, verified} from './transport.js';
const $ = id => document.getElementById(id);
const C = SPLNativeCoordinates, cache = new Map();
const planes = ['axial', 'coronal', 'sagittal'];
let config, generation = 0, currentPoint = null;

for (const plane of planes) {
  const section = document.createElement('section');
  section.innerHTML = `<h3>${plane}</h3><label>${plane} slice <input id="slice-${plane}" type="range" min="0" step="1" disabled><output id="slice-value-${plane}"></output></label><p>Unmarked native MRI</p><div class="source-plane"><canvas id="plain-${plane}" role="img" aria-label="${plane} unmarked original MRI"></canvas><canvas id="plain-cross-${plane}" class="crosshair" aria-hidden="true"></canvas></div><p>Selected source labels</p><div class="source-plane"><canvas id="labels-${plane}" role="img" aria-label="${plane} original MRI with selected source labels"></canvas><canvas id="labels-cross-${plane}" class="crosshair" aria-hidden="true"></canvas></div><p id="edges-${plane}"></p>`;
  $('planes').append(section);
  $('slice-' + plane).addEventListener('input', () => {
    if (!currentPoint || !config) return;
    const row = config.volumes[$('contrast').value], spec = C.planeSpec(row, plane, 0);
    currentPoint.voxel[spec.fixed] = Number($('slice-' + plane).value);
    render();
  });
}
const returnButton = document.createElement('button');
returnButton.id = 'return-to-contact';
returnButton.type = 'button';
returnButton.textContent = 'Return to selected contact point';
returnButton.disabled = true;
returnButton.onclick = () => render(true);
$('planes').before(returnButton);

function clear() {
  delete document.body.dataset.mriReady;
  window.ContactMRIState = null;
  for (const canvas of $('planes').querySelectorAll('canvas')) {
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
  }
}
async function load(key, row) {
  if (cache.has(key)) return cache.get(key);
  const pending = (async () => {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 45000);
    try {
      const response = await fetch('/app/anatomy/spl-nac-limbic/' + row.file, {credentials: 'same-origin', signal: controller.signal});
      if (!response.ok) throw Error('Source MRI unavailable');
      const packed = new Uint8Array(await response.arrayBuffer());
      const identity = await sha(packed);
      if (identity !== row.gzipSHA256 && identity !== row.decodedSHA256) throw Error('Source MRI payload identity differs');
      const raw = identity === row.decodedSHA256
        ? await verified(packed, row.byteLength, row.decodedSHA256)
        : await decode(packed, row.byteLength, row.decodedSHA256);
      return key === 'labels' ? new Int16Array(raw.buffer) : new Float32Array(raw.buffer);
    } finally { clearTimeout(timer); }
  })();
  cache.set(key, pending);
  try { return await pending; } catch (error) { cache.delete(key); throw error; }
}
function paint(plane, row, image, labels, selection, point, inverse, low, high) {
  let spec = C.planeSpec(row, plane, 0);
  spec = C.planeSpec(row, plane, point[spec.fixed]);
  const plain = new Uint8ClampedArray(spec.width * spec.height * 4), marked = new Uint8ClampedArray(plain.length);
  for (let y = 0; y < spec.height; y++) for (let x = 0; x < spec.width; x++) {
    const voxel = C.pixelVoxel(spec, x, y), value = image[C.offset(row.shape, voxel)];
    const world = C.transform(row.voxelToRAS, voxel), cell = C.nearestVoxel(inverse, world, config.labelVolume.shape);
    const code = cell ? labels[C.offset(config.labelVolume.shape, cell)] : 0;
    const grey = Math.max(0, Math.min(255, Math.floor(255 * (value - low) / (high - low))));
    const i = 4 * (x + spec.width * y);
    const color = code === selection.whiteCode ? [100, 160, 240] : code === selection.corticalCode ? [255, 128, 0] : null;
    for (let c = 0; c < 3; c++) {
      plain[i + c] = grey;
      marked[i + c] = color ? Math.round(.55 * grey + .45 * color[c]) : grey;
    }
    plain[i + 3] = marked[i + 3] = 255;
  }
  for (const [mode, pixels] of [['plain', plain], ['labels', marked]]) {
    const canvas = $(mode + '-' + plane);
    canvas.width = spec.width; canvas.height = spec.height;
    canvas.getContext('2d').putImageData(new ImageData(pixels, spec.width, spec.height), 0, 0);
  }
  const x = spec.flipHorizontal ? spec.width - 1 - point[spec.horizontal] : point[spec.horizontal];
  const y = spec.flipVertical ? spec.height - 1 - point[spec.vertical] : point[spec.vertical];
  for (const mode of ['plain', 'labels']) {
    const canvas = $(mode + '-cross-' + plane);
    canvas.width = spec.width; canvas.height = spec.height;
    const ctx = canvas.getContext('2d');
    ctx.strokeStyle = '#59e3ff'; ctx.lineWidth = 1; ctx.beginPath();
    ctx.moveTo(x + .5, 0); ctx.lineTo(x + .5, spec.height);
    ctx.moveTo(0, y + .5); ctx.lineTo(spec.width, y + .5); ctx.stroke();
    canvas.dataset.crosshair = JSON.stringify([x, y]);
  }
  $('edges-' + plane).textContent = 'Edges left/right/top/bottom: ' + spec.edgeLabels.join('/') + '. Original 0.75 mm source samples.';
  return spec;
}
async function render(reset = false) {
  const epoch = ++generation;
  clear();
  if (!config) return;
  const pair = $('pair').value, selection = config.pairs.find(p => p.whiteCode + ':' + p.corticalCode === pair);
  for (const plane of planes) $('slice-' + plane).disabled = !selection;
  returnButton.disabled = !selection;
  if (!selection) {
    currentPoint = null;
    for (const plane of planes) $('slice-value-' + plane).textContent = '';
    $('mri-status').textContent = 'Choose a source-label pair to inspect original MRI.';
    return;
  }
  const contrast = $('contrast').value, side = $('side').value, row = config.volumes[contrast];
  const anchor = selection.anchors[side].nativeMRI[contrast], key = pair + '/' + contrast + '/' + side;
  if (reset || currentPoint?.key !== key) currentPoint = {key, voxel: [...anchor.sourceIJK]};
  const inspectionVoxel = [...currentPoint.voxel];
  const atSourceAnchor = inspectionVoxel.every((value, i) => value === anchor.sourceIJK[i]);
  for (const plane of planes) {
    const spec = C.planeSpec(row, plane, 0), control = $('slice-' + plane);
    control.max = row.shape[spec.fixed] - 1;
    control.value = inspectionVoxel[spec.fixed];
    $('slice-value-' + plane).textContent = ' ' + control.value + ' / ' + control.max;
  }
  $('mri-status').textContent = 'Loading verified native source arrays…';
  try {
    const [image, labels] = await Promise.all([load(contrast, row), load('labels', config.labelVolume)]);
    if (epoch !== generation) return;
    const inverse = C.inverse(config.labelVolume.voxelToRAS), [low, high] = row.defaultWindow;
    const states = planes.map(plane => {
      const spec = paint(plane, row, image, labels, selection, inspectionVoxel, inverse, low, high);
      return {plane, slice: spec.slice, contrast, side, pair, spec, low, high};
    });
    const probe = C.probe(row, image, config.labelVolume, labels, inspectionVoxel);
    if (atSourceAnchor && probe.label !== selection.anchors[side].sourceLabelCode) throw Error('Source-anchor label differs');
    window.ContactMRIState = {contrast, side, pair, states, anchor, inspectionVoxel, atSourceAnchor, probe};
    document.body.dataset.mriReady = pair;
    $('mri-status').textContent = contrast + ' native voxel (' + inspectionVoxel.join(', ') + '); source label ' + probe.label + '. ' +
      (atSourceAnchor ? 'Selected contact point. ' : 'Exploring source MRI; use Return to selected contact point to restore the anchor. ') +
      'Blue: selected white class; orange: selected cortical class. Source labels do not establish biological boundary accuracy.';
  } catch (error) {
    if (epoch === generation) { clear(); $('mri-status').textContent = error.message; }
  }
}
for (const id of ['pair', 'contrast', 'side']) $(id).addEventListener('change', () => render(true));
try {
  const response = await fetch('mri-source.json'), raw = new Uint8Array(await response.arrayBuffer());
  if (await sha(raw) !== '09a1f6f40628741b4339ce69020bf615ba29c63ebb9f3bd0ab8c19dd202d2c6e') throw Error('MRI metadata differs');
  config = JSON.parse(new TextDecoder().decode(raw));
  render();
} catch (error) { $('mri-status').textContent = error.message; }

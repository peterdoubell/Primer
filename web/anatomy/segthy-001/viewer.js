import { fingerprint, nativeReader, FetchPool, planes } from './native-volume.mjs';
import { meshView } from './mesh-view.mjs';
import { sourceSelection } from './source-selection.mjs';

const byId = id => document.getElementById(id);
const inputs = ['i', 'j', 'k'].map(byId);
const canvas = byId('ultrasound');
const context = canvas.getContext('2d', { willReadFrequently: true });
const overlay = byId('image-locator');
const frameElement = byId('image-frame');
const pool = new FetchPool(3);
const surface = meshView(byId('surface'), byId('mesh-locator'), byId('mesh-status'), {
  yaw: byId('yaw'), pitch: byId('pitch'), zoom: byId('zoom'),
  yawValue: byId('yaw-value'), pitchValue: byId('pitch-value'),
  reset: byId('reset-orbit'), retry: byId('retry-mesh'),
});
let manifest;
let record;
let selected;
let reader;
let position = [0, 0, 0];
let frame;
let pending;
let generation = 0;
const names = ['I', 'J', 'K'];
const namespace = 'http://www.w3.org/2000/svg';

function shape(tag, attributes, text) {
  const node = document.createElementNS(namespace, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function controls() {
  const axes = planes[byId('plane').value];
  inputs.forEach((input, axis) => {
    input.max = record.shape[axis] - 1;
    input.value = position[axis];
  });
  const slice = byId('slice');
  slice.max = record.shape[axes.normal] - 1;
  slice.value = position[axes.normal];
  byId('slice-label').textContent = axes.fixedName + ' section';
  byId('slice-value').textContent = position[axes.normal] + ' / ' + slice.max;
  surface.locator({ axes, position: [...position], spacing: record.spacingMm });
}

function resizeFrame() {
  if (!frame) return;
  frameElement.style.aspectRatio = (frame.width * frame.spacing[0]) / (frame.height * frame.spacing[1]);
  frameElement.style.width = byId('image-scale').value === 'native' ? frame.width + 'px' : '100%';
}

function locator() {
  if (!frame) return;
  const { axes, width, height } = frame;
  const x = position[axes.horizontal] + .5;
  const y = height - position[axes.vertical] - .5;
  overlay.setAttribute('viewBox', `0 0 ${width} ${height}`);
  overlay.replaceChildren();
  // A screen-legible locator is separate from the unchanged native raster.
  const unit = width / Math.max(1, canvas.clientWidth);
  const stroke = 1.5 * unit;
  overlay.append(shape('path', { d: `M${x - 9 * unit},${y}h${6 * unit}m${6 * unit},0h${6 * unit}M${x},${y - 9 * unit}v${6 * unit}m0,${6 * unit}v${6 * unit}`,
    stroke: '#ffce79', 'stroke-width': stroke, fill: 'none' }));
  const targetMm = width * frame.spacing[0] / 5;
  const power = 10 ** Math.floor(Math.log10(targetMm));
  const mm = [1, 2, 5, 10].map(value => value * power).filter(value => value <= targetMm).at(-1);
  const length = mm / frame.spacing[0];
  const left = 15 * unit, bottom = height - 20 * unit;
  overlay.append(shape('rect', { x: 9 * unit, y: bottom - 23 * unit,
    width: Math.max(length + 12 * unit, 75 * unit), height: 35 * unit, fill: '#07131c', 'fill-opacity': .8 }));
  overlay.append(shape('path', { d: `M${left},${bottom - 3 * unit}v${6 * unit}m0,${-3 * unit}h${length}m0,${-3 * unit}v${6 * unit}`,
    stroke: '#ffffff', 'stroke-width': 2 * unit, fill: 'none' }));
  overlay.append(shape('text', { x: left, y: bottom - 9 * unit, fill: '#ffffff', 'font-size': 12 * unit },
    Number(mm.toPrecision(5)) + ' mm'));
  overlay.append(shape('text', { x: 12 * unit, y: 20 * unit, fill: '#ffffff', 'font-size': 12 * unit,
    stroke: '#07131c', 'stroke-width': 3 * unit, 'paint-order': 'stroke' },
    '+' + names[axes.vertical] + ' ↑   +' + names[axes.horizontal] + ' →'));
}

function sample() {
  if (!frame) return;
  const { axes, width, height } = frame;
  const index = (height - 1 - position[axes.vertical]) * width + position[axes.horizontal];
  const code = frame.labels[index];
  const label = record.labels.find(value => value.code === code);
  const labelText = code === 0 ? 'unlabelled' : label?.name || 'unrecognised source label';
  byId('sample').textContent = `I ${position[0]}, J ${position[1]}, K ${position[2]} · stored intensity ${frame.image[index]} / 255 · source label ${code}: ${labelText}.`;
  locator();
}

function render() {
  if (!frame) return;
  const black = byId('black').valueAsNumber, white = byId('white').valueAsNumber;
  if (!Number.isInteger(black) || !Number.isInteger(white) || black < 0 || white > 255 || black >= white) {
    byId('black').setCustomValidity('Use integer points from 0 to 255, with black below white.');
    byId('black').reportValidity();
    return;
  }
  byId('black').setCustomValidity('');
  const mode = byId('mask-mode').value;
  const all = byId('mask-scope').value === 'all';
  const colors = new Map(record.labels.map(label => [label.code, label.color]));
  const pixels = context.createImageData(frame.width, frame.height);
  let selectedPixels = 0;
  for (let index = 0; index < frame.image.length; index += 1) {
    const code = frame.labels[index];
    if (code === selected.code) selectedPixels += 1;
    const gray = Math.max(0, Math.min(255, Math.round((frame.image[index] - black) * 255 / (white - black))));
    const offset = index * 4;
    pixels.data[offset] = pixels.data[offset + 1] = pixels.data[offset + 2] = gray;
    pixels.data[offset + 3] = 255;
    if (!code || mode === 'off' || (!all && code !== selected.code)) continue;
    const color = colors.get(code);
    if (!color) throw Error('The section contains an unregistered source label.');
    const column = index % frame.width;
    const border = !column || column === frame.width - 1 || index < frame.width
      || index >= frame.labels.length - frame.width
      || frame.labels[index - 1] !== code || frame.labels[index + 1] !== code
      || frame.labels[index - frame.width] !== code || frame.labels[index + frame.width] !== code;
    if (mode === 'outline' && !border) continue;
    const alpha = mode === 'fill' ? .5 : 1;
    color.forEach((component, axis) => { pixels.data[offset + axis] = Math.round(gray * (1 - alpha) + component * alpha); });
  }
  canvas.width = frame.width; canvas.height = frame.height;
  context.putImageData(pixels, 0, 0);
  const area = selectedPixels * frame.spacing[0] * frame.spacing[1];
  byId('frame-meta').textContent = `${frame.width} × ${frame.height} native pixels · ${frame.spacing.map(value => value.toFixed(2)).join(' × ')} mm per pixel. Selected mask in this section: ${selectedPixels.toLocaleString()} pixels · ${area.toFixed(2)} mm².`;
  resizeFrame();
  frameElement.hidden = false;
  sample();
}

async function loadSection() {
  if (!reader) return;
  const attempt = ++generation;
  pending?.abort();
  pending = new AbortController();
  frame = null;
  frameElement.hidden = true;
  byId('frame-meta').textContent = '';
  byId('sample').textContent = '';
  byId('retry-image').hidden = true;
  byId('image-status').textContent = 'Verifying the native ultrasound and label section…';
  controls();
  try {
    const next = await reader.section(byId('plane').value, [...position], pending.signal);
    if (attempt !== generation) return;
    const knownCodes = new Set([0, ...record.labels.map(label => label.code)]);
    if (next.labels.some(code => !knownCodes.has(code))) throw Error('The section contains an unregistered source label.');
    frame = next;
    render();
    byId('image-status').textContent = `${record.side} source sweep · ${next.axes.name} · ${next.axes.fixedName} = ${next.fixed}. Source files verified.`;
    canvas.setAttribute('aria-label', `${record.side} native ultrasound, ${next.axes.name} section at ${next.axes.fixedName} ${next.fixed}. Left and right arrow keys change sections.`);
    byId('slice').disabled = false;
  } catch (error) {
    if (attempt !== generation || pending.signal.aborted) return;
    frame = null;
    frameElement.hidden = true;
    byId('image-status').textContent = 'This source section could not be verified. Retry the ultrasound view.';
    byId('retry-image').hidden = false;
  }
}

function focusLabel() {
  position = [...selected.focus];
  loadSection();
}

function chooseLabel() {
  selected = record.labels.find(label => label.code === Number(byId('structure').value));
  const voxelMm3 = record.spacingMm.reduce((product, value) => product * value, 1);
  const volumeMl = selected.voxelCount * voxelMm3 / 1000;
  byId('source-meta').textContent = `${record.id} · ${record.shape.join(' × ')} native voxels at ${record.spacingMm.map(value => value.toFixed(2)).join(' × ')} mm. Label ${selected.code}: ${selected.voxelCount.toLocaleString()} voxels · ${volumeMl.toFixed(3)} mL. Manual segmentation measurement of this sweep only.`;
  surface.load(record, selected);
  focusLabel();
}

function chooseVolume() {
  pending?.abort();
  record = manifest.cases.find(value => value.id === byId('volume').value);
  reader = nativeReader(record, pool);
  byId('structure').replaceChildren(...record.labels.map(label => {
    const option = document.createElement('option');
    option.value = label.code;
    option.textContent = `${label.name} · code ${label.code}`;
    return option;
  }));
  byId('geometry').textContent = `${manifest.acquisition} ${manifest.registration} Source shape ${record.shape.join(' × ')}; grid pitch ${record.spacingMm.map(value => value.toFixed(8)).join(' × ')} mm. The centered affines do not establish registration between sweeps.`;
  chooseLabel();
}

function move(next) {
  if (!record) return;
  const axes = planes[byId('plane').value];
  const fixedChanged = next[axes.normal] !== position[axes.normal];
  position = next.map((value, axis) => Math.max(0, Math.min(record.shape[axis] - 1, Math.round(value))));
  controls();
  if (fixedChanged || !frame) loadSection();
  else sample();
}

inputs.forEach((input, axis) => input.addEventListener('change', () => {
  if (!Number.isInteger(input.valueAsNumber)) { controls(); return; }
  const next = [...position]; next[axis] = input.valueAsNumber; move(next);
}));
byId('slice').addEventListener('input', () => {
  const next = [...position]; next[planes[byId('plane').value].normal] = byId('slice').valueAsNumber; move(next);
});
byId('plane').addEventListener('change', loadSection);
byId('volume').addEventListener('change', chooseVolume);
byId('structure').addEventListener('change', chooseLabel);
byId('focus').addEventListener('click', focusLabel);
byId('retry-image').addEventListener('click', loadSection);
for (const id of ['mask-mode', 'mask-scope', 'black', 'white']) byId(id).addEventListener('change', render);
byId('image-scale').addEventListener('change', () => { resizeFrame(); locator(); });
new ResizeObserver(locator).observe(frameElement);
canvas.addEventListener('click', event => {
  if (!frame) return;
  const bounds = canvas.getBoundingClientRect();
  const column = Math.max(0, Math.min(frame.width - 1, Math.floor((event.clientX - bounds.left) * frame.width / bounds.width)));
  const row = Math.max(0, Math.min(frame.height - 1, Math.floor((event.clientY - bounds.top) * frame.height / bounds.height)));
  const next = [...position];
  next[frame.axes.horizontal] = column;
  next[frame.axes.vertical] = frame.height - 1 - row;
  move(next);
});
canvas.addEventListener('keydown', event => {
  if (!record || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  event.preventDefault();
  const next = [...position];
  next[planes[byId('plane').value].normal] += event.key === 'ArrowRight' ? 1 : -1;
  move(next);
});

async function boot() {
  try {
    const response = await fetch(new URL('manifest.json', import.meta.url));
    if (!response.ok) throw Error('The source inventory is unavailable.');
    const bytes = await response.arrayBuffer();
    // Pin the package tested with this reader. A source update also updates this receipt.
    if (await fingerprint(bytes) !== 'd054557d2c5e6230c49659c23812a4f91d2d044ffc43d4f4b31aca88b0f5e440') {
      throw Error('The source inventory identity differs.');
    }
    manifest = JSON.parse(new TextDecoder().decode(bytes));
    if (!Array.isArray(manifest.cases) || manifest.cases.length !== 2
        || new Set(manifest.cases.map(value => value.id)).size !== 2) throw Error('The separate sweep inventory is invalid.');
    const requested = sourceSelection(location.search, manifest.cases);
    byId('volume').replaceChildren(...manifest.cases.map(value => {
      const option = document.createElement('option'); option.value = value.id;
      option.textContent = value.side + ' native sweep'; return option;
    }));
    byId('label-key').textContent = manifest.labelKey;
    const credit = byId('credit');
    const link = document.createElement('a'); link.href = manifest.source; link.textContent = 'SegThy dataset, Technical University of Munich';
    credit.replaceChildren(link, document.createTextNode('. ' + manifest.license + '. ' + manifest.surfaces));
    if (requested) {
      byId('volume').value = requested.volume;
      if (requested.representation === 'clinical_image') byId('mask-mode').value = 'off';
      document.body.dataset.sourceRepresentation = requested.representation || 'source';
    }
    byId('selection').disabled = false;
    chooseVolume();
    if (requested && Number(byId('structure').value) !== requested.label) {
      byId('structure').value = String(requested.label);
      chooseLabel();
    }
  } catch (error) {
    byId('image-status').textContent = error.name === 'SourceSelectionError'
      ? error.message + ' Open the reader without selectors to choose a source.'
      : 'The source inventory could not be verified. Reload to retry.';
    document.body.dataset.sourceLinkError = error.name === 'SourceSelectionError' ? 'true' : 'false';
  }
}
boot();

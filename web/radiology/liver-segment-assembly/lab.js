import {
  fingerprint,
  FetchPool,
  nativeReader,
  planes,
  verifiedBytes
} from '../../anatomy/segthy-001/native-volume.mjs';
import { gridBounds, patientPosition, sectionData } from './geometry.mjs';
import { surfaceScene } from './scene.mjs';
import { samplingLab } from './sampling.mjs';

const $ = (id) => document.getElementById(id);
const base = new URL('/app/anatomy/medseg-liver-001/viewer.js', import.meta.url).href;
const read = (row, signal) => verifiedBytes(row, signal, base);
const knownExams = new Set([
  'ct.liver-mass',
  'ct.liver-lirads',
  'ct.liver-lirads-calculated',
  'ct.chest-abdomen-pelvis'
]);
const format = (x, places = 1) => x.toLocaleString('en-US', { maximumFractionDigits: places });
const params = new URLSearchParams(location.search);
const referring = params.getAll('exam');
const exam = referring.length === 1 && knownExams.has(referring[0]) ? referring[0] : null;
if (exam) {
  $('return').href = '/app/#/radiology/' + exam;
  $('return').textContent = 'Return to the referring CT report';
}
if (!exam && !params.has('segment')) {
  $('return').hidden = true;
  $('math-links').hidden = false;
  $('study-title').textContent = 'Volume by systematic section sampling';
  $('introduction').textContent =
    'Use 47 original CT sections to test how well a smaller set estimates volume. Inspect each sampled area in the same 3D scan.';
  $('controls').before($('sampling'));
}
const orbit = { yaw: $('yaw'), pitch: $('pitch'), zoom: $('zoom') };
let record,
  reader,
  bounds,
  scene,
  selected,
  position,
  visible,
  rows = new Map(),
  frame = null,
  rendered = null;
let sectionRequest,
  version = 0,
  starting = false,
  meshesLoaded = false,
  profileLoaded = false;
const failures = new Set();
function markFailure(resource, failed) {
  if (failed) failures.add(resource);
  else failures.delete(resource);
  $('retry').hidden = failures.size === 0;
}

function linkToNative() {
  const query = new URLSearchParams({
    plane: $('plane').value,
    display: $('display').value,
    focus: 'label'
  });
  if (selected) query.set('segment', selected.segment);
  if (exam) query.set('exam', exam);
  $('single').href = '/app/anatomy/medseg-liver-001/index.html?' + query;
  $('single').hidden = !selected;
}

function tableState() {
  for (const [code, row] of rows) {
    row.box.checked = visible.has(code);
    row.focus.setAttribute('aria-pressed', String(code === selected?.code));
    row.area.textContent = rendered ? format(rendered.counts[code] * rendered.pixelArea) : '—';
  }
  $('isolate').disabled = !selected;
  linkToNative();
}

function updateSectionLabels() {
  const key = $('plane').value,
    axes = planes[key];
  const index = position[axes.normal];
  $('index').textContent = axes.fixedName + ' ' + index;
  $('slice').min = 0;
  $('slice').max = record.shape[axes.normal] - 1;
  $('slice').value = index;
  $('left').textContent = key === 'jk' ? 'A' : 'R';
  $('top').textContent = key === 'ij' ? 'A' : 'S';
  const choices = $('cut').options;
  choices[1].textContent = {
    ij: 'Keep inferior side',
    ik: 'Keep posterior side',
    jk: 'Keep left side'
  }[key];
  choices[2].textContent = {
    ij: 'Keep superior side',
    ik: 'Keep anterior side',
    jk: 'Keep right side'
  }[key];
}

function render() {
  if (!record) return;
  rendered = null;
  const cut = Number($('cut').value);
  if (frame) {
    rendered = sectionData(frame, bounds, record.labels, record.spacingMm, visible, $('display').value);
    const scan = $('scan');
    scan.width = rendered.width;
    scan.height = rendered.height;
    const context = scan.getContext('2d');
    context.putImageData(new ImageData(rendered.raster, rendered.width, rendered.height), 0, 0);
    scan.style.aspectRatio =
      rendered.width * frame.spacing[0] + ' / ' + rendered.height * frame.spacing[1];
    $('section-frame').hidden = false;
    const occupied = rendered.counts.reduce((a, b) => a + b, 0);
    $('section-status').textContent =
      frame.axes.fixedName +
      ' ' +
      frame.fixed +
      ' · ' +
      format(occupied) +
      ' labelled cells · ' +
      format(occupied * rendered.pixelArea) +
      ' mm² across all source regions on this section.';
  }
  scene?.update(rendered, frame?.axes, frame?.fixed, visible, cut);
  tableState();
}

async function loadSection() {
  sectionRequest?.abort();
  const controller = new AbortController();
  sectionRequest = controller;
  const ticket = ++version;
  frame = null;
  rendered = null;
  $('section-frame').hidden = true;
  $('voxel').textContent = '';
  $('section-status').textContent = 'Loading the native CT section…';
  markFailure('section', false);
  updateSectionLabels();
  render();
  try {
    const next = await reader.section($('plane').value, [...position], controller.signal);
    if (ticket !== version) return;
    frame = next;
    render();
  } catch (error) {
    if (ticket !== version || controller.signal.aborted) return;
    $('section-status').textContent = 'The source section could not be verified.';
    markFailure('section', true);
  }
}

function select(row, focus) {
  selected = row;
  if (row && focus) {
    position = [...row.focus];
    visible.add(row.code);
    loadSection();
  } else {
    render();
  }
}

function buildTable() {
  const body = $('regions');
  body.replaceChildren();
  rows = new Map();
  for (const row of record.labels) {
    const tr = document.createElement('tr');
    const box = document.createElement('input');
    box.type = 'checkbox';
    box.checked = true;
    box.setAttribute('aria-label', 'Show ' + row.sourceName);
    box.addEventListener('change', () => {
      if (box.checked) visible.add(row.code);
      else visible.delete(row.code);
      render();
    });
    const focus = document.createElement('button');
    focus.type = 'button';
    const swatch = document.createElement('span');
    swatch.className = 'swatch';
    swatch.style.backgroundColor = 'rgb(' + row.color.join(',') + ')';
    focus.append(swatch, row.sourceName);
    focus.addEventListener('click', () => select(row, true));
    const volume = document.createElement('td'),
      area = document.createElement('td');
    volume.textContent = format((row.voxelCount * record.spacingMm.reduce((a, b) => a * b)) / 1000);
    const toggle = document.createElement('td'),
      header = document.createElement('th');
    header.scope = 'row';
    toggle.append(box);
    header.append(focus);
    tr.append(toggle, header, volume, area);
    body.append(tr);
    rows.set(row.code, { box, focus, area });
  }
}

async function loadMeshes() {
  if (!scene || meshesLoaded) return;
  markFailure('meshes', false);
  $('model-status').textContent = 'Verifying nine source surfaces…';
  const controller = new AbortController(),
    items = Array(record.labels.length);
  let next = 0;
  async function worker() {
    while (next < items.length && !controller.signal.aborted) {
      const idx = next++,
        row = record.labels[idx],
        raw = await read(row.mesh, controller.signal);
      const offset = 12 * row.mesh.vertices;
      if (raw.byteLength !== offset + 12 * row.mesh.triangles) throw Error('Mesh layout differs.');
      items[idx] = {
        row,
        positions: new Float32Array(raw, 0, row.mesh.vertices * 3),
        indices: new Uint32Array(raw, offset, row.mesh.triangles * 3)
      };
    }
  }
  try {
    await Promise.all([worker(), worker(), worker()]);
    scene.setMeshes(items);
    meshesLoaded = true;
    render();
  } catch {
    controller.abort();
    $('model-status').textContent = 'The source surfaces could not be verified.';
    markFailure('meshes', true);
  }
}

async function initialiseSampling() {
  const response = await fetch('axial-profile.json', { redirect: 'error' });
  if (!response.ok) throw Error('Sampling profile unavailable.');
  const bytes = await response.arrayBuffer();
  if ((await fingerprint(bytes)) !== '3443f73cca3703ba7b862ff047633d97dd425ce19c9454a6e5a44b92e2a0c536')
    throw Error('Sampling profile differs.');
  const profile = JSON.parse(new TextDecoder().decode(bytes));
  if (
    profile.case !== record.id ||
    profile.sourceLabelSampleSHA256 !== record.originalLabelSampleSHA256
  )
    throw Error('CT source differs.');
  samplingLab(profile, record, (k, code) => {
    selected = record.labels.find((row) => row.code === code) || null;
    visible = new Set(selected ? [selected.code] : record.labels.map((row) => row.code));
    $('plane').value = 'ij';
    position[2] = k;
    $('cut').value = '1';
    loadSection();
    $('controls').scrollIntoView({ block: 'start' });
  });
}

async function loadSampling() {
  markFailure('profile', false);
  try {
    await initialiseSampling();
    profileLoaded = true;
  } catch {
    $('sample-result').textContent =
      'The axial measurement profile could not be verified. Retry the source study.';
    markFailure('profile', true);
  }
}

async function start() {
  if (starting) return;
  starting = true;
  markFailure('inventory', false);
  try {
    if (!record) {
      const response = await fetch('/app/anatomy/medseg-liver-001/manifest.json', {
        credentials: 'same-origin',
        redirect: 'error'
      });
      if (!response.ok) throw Error('Source inventory unavailable.');
      const buf = await response.arrayBuffer();
      if (
        (await fingerprint(buf)) !== 'acd937199d16170d8aaf707e744212774a2d5131003590ee8083c055a32273a8'
      )
        throw Error('Source inventory changed.');
      const data = JSON.parse(new TextDecoder().decode(buf));
      if (data.id !== 'medseg-liver-001' || data.labels.length !== 9)
        throw Error('Unexpected source study.');
      record = data;
      reader = nativeReader(record, new FetchPool(3), read, 36 * 1024 * 1024);
      visible = new Set(record.labels.map((r) => r.code));
      bounds = gridBounds(record.labels, record.shape, 2);
      const tokens = params.getAll('segment');
      selected = tokens.length === 1 ? record.labels.find((r) => r.segment === tokens[0]) : null;
      position = selected
        ? [...selected.focus]
        : bounds[0].map((n, i) => Math.round((n + bounds[1][i]) / 2));
      $('status').textContent =
        tokens.length && !selected ? 'The region in this link is unknown. Select a region below.' : '';
      $('extent').textContent =
        'The nine masks contain ' +
        format(record.labelledVoxels) +
        ' cells. Volumes use the original voxel spacing and areas use the current section.';
      buildTable();
      $('controls').disabled = false;
      try {
        scene = surfaceScene($('model'), $('model-status'), orbit, bounds, record.spacingMm);
      } catch {
        $('model-status').textContent = 'The 3D view could not initialise. CT inspection is available.';
        scene = null;
      }
    }
    const sampling = profileLoaded ? null : loadSampling();
    await Promise.all([loadSection(), loadMeshes(), sampling]);
  } catch {
    $('status').textContent = 'The source study could not be verified.';
    markFailure('inventory', true);
  } finally {
    starting = false;
  }
}

$('retry').onclick = start;
$('plane').onchange = () => loadSection();
$('slice').oninput = () => {
  position[planes[$('plane').value].normal] = $('slice').valueAsNumber;
  loadSection();
};
$('cut').onchange = render;
$('display').onchange = render;
$('all').onclick = () => {
  if (record) {
    visible = new Set(record.labels.map((r) => r.code));
    render();
  }
};
$('isolate').onclick = () => {
  if (selected) {
    visible = new Set([selected.code]);
    render();
  }
};
$('scan').onclick = (e) => {
  if (!frame || !rendered) return;
  const rect = $('scan').getBoundingClientRect(),
    { horizontal: h, vertical: v, normal: n } = frame.axes;
  const x = Math.min(
    rendered.width - 1,
    Math.max(0, Math.floor(((e.clientX - rect.left) * rendered.width) / rect.width))
  );
  const y = Math.min(
    rendered.height - 1,
    Math.max(0, Math.floor(((e.clientY - rect.top) * rendered.height) / rect.height))
  );
  const point = [0, 0, 0];
  point[h] = bounds[1][h] - x;
  point[v] = bounds[1][v] - y;
  point[n] = frame.fixed;
  const i = (frame.height - 1 - point[v]) * frame.width + point[h],
    code = frame.labels[i],
    row = record.labels.find((r) => r.code === code);
  $('voxel').textContent =
    'I, J, K = ' +
    point.join(', ') +
    ' · stored CT ' +
    frame.image[i] +
    ' · ' +
    (row?.sourceName || 'background') +
    ' · source RAS (mm) ' +
    patientPosition(record.affine, point)
      .map((v) => format(v, 2))
      .join(', ') +
    '.';
  if (row) select(row, false);
};
$('scan').onkeydown = (e) => {
  if (!frame || !['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
  e.preventDefault();
  const n = frame.axes.normal;
  position[n] = Math.max(
    0,
    Math.min(record.shape[n] - 1, position[n] + (e.key === 'ArrowRight' ? 1 : -1))
  );
  loadSection();
};
function updateOrbit() {
  $('orientation').textContent =
    'Rotation ' +
    orbit.yaw.value +
    '° · tilt ' +
    orbit.pitch.value +
    '°. At 0° the view is anterior, with superior up.';
  scene?.draw();
}
for (const input of Object.values(orbit)) input.oninput = updateOrbit;
function resetOrbit() {
  for (const input of Object.values(orbit)) input.value = input.defaultValue;
  updateOrbit();
}
$('reset').onclick = resetOrbit;
const model = $('model');
let drag = null;
model.onpointerdown = (e) => {
  drag = { x: e.clientX, y: e.clientY, yaw: orbit.yaw.valueAsNumber, pitch: orbit.pitch.valueAsNumber };
  model.setPointerCapture(e.pointerId);
};
model.onpointermove = (e) => {
  if (drag) {
    orbit.yaw.value = ((drag.yaw + (e.clientX - drag.x) * 0.5 + 540) % 360) - 180;
    orbit.pitch.value = Math.max(-89, Math.min(89, drag.pitch + (e.clientY - drag.y) * 0.5));
    updateOrbit();
  }
};
model.onpointerup = model.onpointercancel = () => {
  drag = null;
};
model.onkeydown = (e) => {
  const steps = {
    ArrowLeft: ['yaw', -5],
    ArrowRight: ['yaw', 5],
    ArrowUp: ['pitch', 5],
    ArrowDown: ['pitch', -5],
    '+': ['zoom', 0.1],
    '=': ['zoom', 0.1],
    '-': ['zoom', -0.1]
  };
  if (e.key === 'Home') {
    e.preventDefault();
    resetOrbit();
    return;
  }
  if (!Object.hasOwn(steps, e.key)) return;
  e.preventDefault();
  const [id, delta] = steps[e.key];
  orbit[id].value = orbit[id].valueAsNumber + delta;
  updateOrbit();
};
updateOrbit();
start();

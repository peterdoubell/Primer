import { crossSection, estimate, openMesh } from './geometry.mjs';
import { surfaceView } from './surface.mjs';
import { sectionPlot, profilePlot } from './plots.mjs';

const get = (id) => document.getElementById(id);
const media = '/source-media/reference-media/lesson-sources/bennu/';
const fmt = (x, d = 0) => x.toLocaleString('en-US', { maximumFractionDigits: d });
const manifestSHA = '03fe652abc28eaaf4132ef6a63dd7639a80dae112fbf469859eaff8f2b11685e';
const cache = new Map();
let source, model, mesh, slice, sample, pending, radius;
let view;
try {
  view = surfaceView(get('solid'));
} catch {
  view = null;
}
if (!view) {
  get('webgl-note').textContent =
    'This browser can display the section and area graph. A WebGL 2 browser also displays the 3D surface.';
}
function row(values) {
  const tr = document.createElement('tr');
  values.forEach((v, i) => {
    const cell = document.createElement(i ? 'td' : 'th');
    if (!i) cell.scope = 'row';
    cell.textContent = v;
    tr.append(cell);
  });
  return tr;
}
function heightM() {
  const a = Number(get('axis').value);
  return (
    model.bounds[0][a] +
    ((model.bounds[1][a] - model.bounds[0][a]) * get('height').valueAsNumber) / source.steps
  );
}
function orbit() {
  if (!model || !mesh) return;
  view?.draw({
    bounds: model.bounds,
    radius,
    yaw: get('yaw').valueAsNumber,
    pitch: get('pitch').valueAsNumber,
    axis: Number(get('axis').value),
    height: heightM(),
    cut: get('cutaway').checked
  });
}
function diagrams() {
  if (!model || !slice || !sample) return;
  const a = Number(get('axis').value);
  sectionPlot(get('slice'), model, a, slice);
  profilePlot(get('profile'), model, a, sample, get('rule').value, get('height').valueAsNumber);
}
function updateSlice() {
  if (!model || !mesh) return;
  const a = Number(get('axis').value),
    z = heightM();
  slice = crossSection(mesh.positions, mesh.indices, a, z);
  const reference = model.profiles[a][get('height').valueAsNumber];
  if (Math.abs(slice.area - reference) > 0.01) throw Error('Section does not match its source profile.');
  get('height-value').textContent = fmt(z, 1) + ' m';
  get('height').setAttribute('aria-valuetext', 'XYZ'[a] + ' = ' + fmt(z, 1) + ' metres');
  get('slice-reading').textContent =
    'XYZ'[a] + ' = ' + fmt(z, 1) + ' m · ' + fmt(slice.area, 1) + ' m² of section area.';
  view?.setSection(slice.segments);
  orbit();
  diagrams();
}
function updateSlabs() {
  if (!model || !mesh) return;
  const a = Number(get('axis').value),
    n = Number(get('slabs').value);
  sample = estimate(model, a, n, get('rule').value);
  const relative = (100 * sample.error) / model.volumeM3;
  get('results').replaceChildren(
    ...[
      ['Thickness of one slab', fmt(sample.thickness, 2) + ' m'],
      ['Sum of slab volumes', fmt(sample.volume) + ' m³'],
      ['Volume enclosed by the mesh', fmt(model.volumeM3) + ' m³'],
      [
        'Estimate minus mesh volume',
        (sample.error > 0 ? '+' : '') +
          fmt(sample.error) +
          ' m³ (' +
          (relative > 0 ? '+' : '') +
          fmt(relative, 3) +
          '%)'
      ]
    ].map(row)
  );
  const low = model.bounds[0][a];
  get('slab-data').replaceChildren(
    ...sample.slabs.map((s, i) =>
      row([
        String(i + 1),
        fmt(low + i * sample.thickness, 1) + ' to ' + fmt(low + (i + 1) * sample.thickness, 1),
        fmt(s.sample, 1),
        fmt(s.sample * sample.thickness)
      ])
    )
  );
  diagrams();
}
async function load() {
  const chosen = source.models.find((r) => r.code === get('resolution').value);
  if (!chosen) return;
  pending?.abort();
  const controller = new AbortController();
  pending = controller;
  mesh = null;
  slice = null;
  sample = null;
  model = null;
  view?.setMesh(null);
  view?.draw();
  get('controls').disabled = true;
  get('controls').hidden = true;
  get('retry').hidden = true;
  get('status').textContent = 'Verifying the ' + chosen.resolutionM + ' m shape model…';
  get('mesh-info').textContent = '';
  try {
    const loaded =
      cache.get(chosen.code) || (await openMesh(chosen, media + chosen.mesh, controller.signal));
    controller.signal.throwIfAborted();
    cache.set(chosen.code, loaded);
    model = chosen;
    mesh = loaded;
    const center = chosen.bounds[0].map((v, i) => (v + chosen.bounds[1][i]) / 2);
    let squared = 0;
    for (let i = 0; i < mesh.positions.length; i += 3) {
      squared = Math.max(
        squared,
        (mesh.positions[i] - center[0]) ** 2 +
          (mesh.positions[i + 1] - center[1]) ** 2 +
          (mesh.positions[i + 2] - center[2]) ** 2
      );
    }
    radius = 1.08 * Math.sqrt(squared);
    view?.setMesh(mesh);
    get('controls').hidden = false;
    get('controls').disabled = false;
    get('mesh-info').textContent =
      fmt(model.triangles) + ' faces · ' + fmt(model.areaM2) + ' m² total surface area.';
    get('label-link').href = model.label;
    updateSlice();
    updateSlabs();
    get('status').textContent =
      'Showing all ' + fmt(model.triangles) + ' faces of the ' + model.resolutionM + ' m PDS model.';
  } catch (e) {
    if (controller.signal.aborted) return;
    mesh = null;
    model = null;
    sample = null;
    slice = null;
    view?.setMesh(null);
    view?.draw();
    get('controls').hidden = true;
    get('status').textContent = 'This model could not be verified. Retry the download.';
    get('retry').hidden = false;
  }
}
get('axis').addEventListener('change', () => {
  sample = null;
  updateSlice();
  updateSlabs();
});
get('height').addEventListener('input', updateSlice);
for (const id of ['slabs', 'rule']) get(id).addEventListener('change', updateSlabs);
for (const id of ['yaw', 'pitch', 'cutaway']) get(id).addEventListener('input', orbit);
function clearAnswer() {
  get('feedback').textContent = '';
}
for (const id of ['target', 'axis', 'rule', 'resolution'])
  get(id).addEventListener('change', clearAnswer);
get('check-answer').addEventListener('click', () => {
  if (!model || !mesh) return;
  const axis = Number(get('axis').value),
    method = get('rule').value,
    target = Number(get('target').value);
  const counts = [2, 4, 8, 16, 32, 64];
  const score = (n) => Math.abs(estimate(model, axis, n, method).error / model.volumeM3) * 100;
  const first = counts.find((n) => score(n) <= target);
  const guess = Number(get('guess').value);
  get('feedback').textContent =
    guess === (first || 0)
      ? first
        ? 'Correct. ' +
          first +
          ' slabs give ' +
          fmt(score(first), 4) +
          '% relative error, the first tested count within ' +
          target +
          '%.'
        : 'Correct. No listed count reaches this target.'
      : guess
        ? 'At ' +
          guess +
          ' slabs the error is ' +
          fmt(score(guess), 4) +
          '%. Compare it with the target and check the smaller counts.'
        : 'At least one of these counts reaches the target. Compare the estimates.';
});
get('retry').addEventListener('click', load);
get('resolution').addEventListener('change', load);
let drag;
const solid = get('solid');
solid.addEventListener('pointerdown', (e) => {
  drag = { x: e.clientX, y: e.clientY, a: get('yaw').valueAsNumber, b: get('pitch').valueAsNumber };
  solid.setPointerCapture(e.pointerId);
});
solid.addEventListener('pointermove', (e) => {
  if (!drag) return;
  get('yaw').value = ((drag.a + (e.clientX - drag.x) * 0.6 + 540) % 360) - 180;
  get('pitch').value = Math.max(-88, Math.min(88, drag.b - (e.clientY - drag.y) * 0.6));
  orbit();
});
for (const evt of ['pointerup', 'pointercancel', 'lostpointercapture'])
  solid.addEventListener(evt, () => {
    drag = null;
  });
solid.addEventListener('keydown', (e) => {
  const delta = { ArrowLeft: [-5, 0], ArrowRight: [5, 0], ArrowUp: [0, 5], ArrowDown: [0, -5] }[e.key];
  if (!delta) return;
  e.preventDefault();
  get('yaw').value = ((get('yaw').valueAsNumber + delta[0] + 540) % 360) - 180;
  get('pitch').value = Math.max(-88, Math.min(88, get('pitch').valueAsNumber + delta[1]));
  orbit();
});
new ResizeObserver(diagrams).observe(get('slice'));
new ResizeObserver(diagrams).observe(get('profile'));
async function start() {
  const response = await fetch('source.json');
  if (!response.ok) throw Error('Missing archive metadata');
  const bytes = await response.arrayBuffer(),
    hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (b) =>
      b.toString(16).padStart(2, '0')
    ).join('');
  if (hash !== manifestSHA) throw Error('Archive metadata differs');
  source = JSON.parse(new TextDecoder().decode(bytes));
  get('resolution').replaceChildren(
    ...source.models.map(
      (r) => new Option(r.resolutionM + ' m · ' + fmt(r.triangles) + ' triangles', r.code)
    )
  );
  get('resolution').disabled = false;
  get('models').replaceChildren(
    ...source.models.map((r) =>
      row([r.resolutionM + ' m', fmt(r.triangles), fmt(r.areaM2), fmt(r.volumeM3)])
    )
  );
  await load();
}
start().catch(() => {
  get('controls').hidden = true;
  get('status').textContent = 'The archive metadata could not be verified. Reload to try again.';
});

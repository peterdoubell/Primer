import { nativeSectionReader } from './native-sections.mjs';
import { maskNamesAt, paintMaskMap } from './mask-map.mjs';

const get = id => document.getElementById(id);
const canvas = get('ct');
const context = canvas.getContext('2d');
const selector = get('node');
const plane = get('plane');
const slider = get('section');
const axis = { axial: 2, coronal: 1, sagittal: 0 };
const displayAxes = { axial: [0, 1], coronal: [0, 2], sagittal: [1, 2] };
let source;
let reader;
let labels;
let anatomy;
let controller;
let currentSection;
let displayed;

function selectedNode() {
  return labels.get(Number(selector.value));
}

function draw() {
  if (!currentSection) return;
  const { ct, nodes, nearby, nearbyLabel, landmarks } = currentSection;
  const grid = ct || nodes;
  const black = get('black').valueAsNumber;
  const white = get('white').valueAsNumber;
  get('pixel').textContent = '';
  if (ct && !(white > black)) {
    displayed = null;
    get('image-wrap').hidden = true;
    get('status').textContent = 'Set a white point above the black point.';
    return;
  }

  const [horizontal, vertical] = displayAxes[plane.value];
  const [dx, dy] = grid.spacingMm;
  const centre = selectedNode().displayIndexXYZ;
  const detail = get('view-size').value === 'detail';
  const width = detail ? Math.min(grid.width, Math.round(100 / dx)) : grid.width;
  const height = detail ? Math.min(grid.height, Math.round(100 / dy)) : grid.height;
  const x0 = Math.max(0, Math.min(grid.width - width, centre[horizontal] - Math.floor(width / 2)));
  const y0 = Math.max(0, Math.min(grid.height - height, grid.height - 1 - centre[vertical] - Math.floor(height / 2)));
  canvas.width = width;
  canvas.height = height;
  canvas.style.aspectRatio = (width * dx) + ' / ' + (height * dy);
  function sample(volume, x, y) {
    if (!volume || x < 0 || x >= grid.width || y < 0 || y >= grid.height) return 0;
    return volume.pixels[x + y * grid.width];
  }
  function edge(volume, x, y, value) {
    return sample(volume, x - 1, y) !== value || sample(volume, x + 1, y) !== value
      || sample(volume, x, y - 1) !== value || sample(volume, x, y + 1) !== value;
  }
  const raster = context.createImageData(width, height);
  const mode = get('nodes').value;
  const selected = selectedNode().label;
  let visibleMaskSamples = 0;
  if (landmarks) {
    const result = paintMaskMap(raster.data, { width, height, x0, y0 }, nodes, landmarks, labels);
    visibleMaskSamples = result.occupied;
    showMapKey(result, dx * dy);
  } else {
    for (let row = 0; row < height; row += 1) {
      const y = y0 + row;
      for (let column = 0; column < width; column += 1) {
        const x = x0 + column;
        const value = sample(nodes, x, y);
        const node = value && (mode === 'all' || value === selected) ? labels.get(value) : null;
        const anatomyValue = sample(nearby, x, y);
        const gray = 255 * (sample(ct, x, y) - black) / (white - black);
        let colour;
        if (anatomyValue && edge(nearby, x, y, anatomyValue)) colour = nearbyLabel.color;
        if (node && edge(nodes, x, y, value)) colour = node.color;
        if (node || anatomyValue) visibleMaskSamples += 1;
        const offset = 4 * (column + row * width);
        raster.data[offset] = colour?.[0] ?? gray;
        raster.data[offset + 1] = colour?.[1] ?? gray;
        raster.data[offset + 2] = colour?.[2] ?? gray;
        raster.data[offset + 3] = 255;
      }
    }
  }
  context.putImageData(raster, 0, 0);
  displayed = { width, height, x0, y0, sample };
  ['top', 'bottom', 'left', 'right'].forEach((side, i) => {
    get('direction-' + side).textContent = grid.directions[i];
  });
  canvas.setAttribute('aria-label', plane.value + (landmarks ? ' anatomical mask map. ' : ' CT. ') + grid.directions[0] + ' at top, '
    + grid.directions[2] + ' at left.');
  get('status').textContent = 'Verified ' + plane.value + ' section · ' + visibleMaskSamples.toLocaleString()
    + ' samples in displayed masks' + (landmarks ? ' · anatomical mask map' : '');
  get('image-wrap').hidden = false;
}

function showMapKey(result, pixelArea) {
  const rows = [];
  for (const annotation of [...labels.values(), ...anatomy.values()]) {
    const count = result.counts.get(annotation);
    if (!count) continue;
    const row = document.createElement('tr');
    row.dataset.source = annotation.transportRole || String(annotation.label);
    const heading = document.createElement('th');
    heading.scope = 'row';
    const swatch = document.createElement('span');
    swatch.className = 'mask-swatch';
    swatch.setAttribute('aria-hidden', 'true');
    swatch.style.backgroundColor = 'rgb(' + annotation.color.join(',') + ')';
    heading.append(swatch, annotation.name);
    const station = document.createElement('td');
    station.textContent = annotation.primaryStationLiteral || '—';
    const area = document.createElement('td');
    area.className = 'map-count';
    area.textContent = (count * pixelArea).toFixed(2);
    row.append(heading, station, area);
    rows.push(row);
  }
  get('map-rows').replaceChildren(...rows);
  get('map-overlap').textContent = result.overlaps + ' shared cells in view. Areas count each source mask independently.';
}

async function loadSection() {
  if (!reader) return;
  controller?.abort();
  controller = new AbortController();
  const { signal } = controller;
  const orientation = plane.value;
  const fixed = slider.valueAsNumber;
  const { sections } = reader.dimensions(orientation);
  const anatomyKey = get('anatomy').value;
  const schematic = get('display-mode').value === 'map';
  const nearbyLabel = schematic ? null : anatomy.get(anatomyKey);
  get('mask-key').hidden = true;
  for (const id of ['nodes', 'anatomy', 'black', 'white']) get(id).disabled = schematic;
  displayed = null;
  currentSection = null;
  if (document.activeElement === canvas) context.clearRect(0, 0, canvas.width, canvas.height);
  else get('image-wrap').hidden = true;
  get('retry').hidden = true;
  get('section-value').textContent = (fixed + 1) + ' / ' + sections;
  get('status').textContent = 'Verifying the ' + orientation + ' section…';
  try {
    const read = role => reader.section(role, orientation, fixed, signal);
    const [ct, nodes, nearby, landmarks] = await Promise.all([
      schematic ? null : read('ct'),
      schematic || get('nodes').value !== 'off' ? read('nodes') : null,
      nearbyLabel ? read(anatomyKey) : null,
      schematic ? Promise.all([...anatomy.values()].map(async annotation => ({
        annotation, section: await read(annotation.transportRole),
      }))) : null,
    ]);
    if (signal.aborted) return;
    currentSection = { ct, nodes, nearby, nearbyLabel, landmarks };
    get('mask-key').hidden = !schematic;
    draw();
  } catch {
    if (signal.aborted) return;
    controller.abort();
    get('status').textContent = 'The source section could not be verified.';
    get('retry').hidden = false;
  }
}

function centreOnNode() {
  const node = selectedNode();
  const fields = [
    ['Primary', node.primaryStationLiteral], ['Secondary', node.secondaryStationLiteral],
    ['Tertiary', node.tertiaryStationLiteral],
  ];
  const list = document.createElement('dl');
  for (const [label, value] of fields) {
    if (!value) continue;
    const name = document.createElement('dt');
    const text = document.createElement('dd');
    name.textContent = label;
    text.textContent = value;
    list.append(name, text);
  }
  if (node.label === 19) {
    const note = document.createElement('p');
    note.textContent = 'The publisher pairs code 11L with a right-sided description for this node.';
    get('assignments').replaceChildren(list, note);
  } else {
    get('assignments').replaceChildren(list);
  }
  get('surface-link').href = 'surfaces.html?node=' + node.label;
  slider.max = reader.dimensions(plane.value).sections - 1;
  slider.value = node.displayIndexXYZ[axis[plane.value]];
  loadSection();
}

async function start() {
  get('retry').hidden = true;
  try {
    const response = await fetch('source.json');
    if (!response.ok) throw Error('Source manifest unavailable.');
    const bytes = await response.arrayBuffer();
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
      value => value.toString(16).padStart(2, '0')).join('');
    if (digest !== '48fd9096b243730377c26595edd23347f14301bbc4838e629df859430c9d1af6') {
      throw Error('Source manifest differs.');
    }
    source = JSON.parse(new TextDecoder().decode(bytes));
    reader = nativeSectionReader(source);
    labels = new Map(source.nodalLabels.map(node => [node.label, node]));
    anatomy = new Map(source.nearbyAnnotations.map(row => [row.transportRole, row]));
    selector.replaceChildren(...source.nodalLabels.map(node => new Option(node.name, node.label)));
    get('anatomy').replaceChildren(new Option('No nearby structure', ''),
      ...source.nearbyAnnotations.map(row => new Option(row.name, row.transportRole)));
    const requested = Number(new URLSearchParams(location.search).get('node'));
    selector.value = labels.has(requested) ? requested : 1;
    get('controls').disabled = false;
    centreOnNode();
  } catch {
    reader = null;
    get('status').textContent = 'The original case could not be verified.';
    get('retry').hidden = false;
  }
}

selector.addEventListener('change', centreOnNode);
plane.addEventListener('change', centreOnNode);
for (const id of ['section', 'nodes', 'anatomy', 'display-mode']) get(id).addEventListener('input', loadSection);
for (const id of ['view-size', 'black', 'white']) get(id).addEventListener('input', draw);
get('retry').addEventListener('click', () => reader ? loadSection() : start());
canvas.addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'ArrowLeft') slider.stepDown();
  else slider.stepUp();
  loadSection();
});
canvas.addEventListener('click', event => {
  if (!displayed) return;
  const bounds = canvas.getBoundingClientRect();
  const { width, height, x0, y0, sample } = displayed;
  const x = x0 + Math.floor((event.clientX - bounds.left) * width / bounds.width);
  const y = y0 + Math.floor((event.clientY - bounds.top) * height / bounds.height);
  if (x < x0 || y < y0 || x >= x0 + width || y >= y0 + height) return;
  if (currentSection.landmarks) {
    const memberships = maskNamesAt(currentSection, x, y, labels);
    get('pixel').textContent = memberships.join(' · ') || 'Unlabelled cell';
    return;
  }
  const node = labels.get(sample(currentSection.nodes, x, y));
  get('pixel').textContent = 'Stored value ' + sample(currentSection.ct, x, y)
    + (node ? ' · ' + node.name : '');
});
start();

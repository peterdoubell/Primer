import { axes, sectionSegments } from './planes.mjs';

const get = (id) => document.getElementById(id);
const layers = [...document.querySelectorAll('input.layer')];
const section = get('section');
let rows = [],
  sourceMeshes = [],
  limits;
const hash = async (bytes) =>
  Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (n) =>
    n.toString(16).padStart(2, '0')
  ).join('');

function setPlane(focus = true) {
  if (!rows.length) return;
  const n = axes[get('plane').value][2];
  const slider = get('position');
  slider.min = Math.floor(limits[0][n]);
  slider.max = Math.ceil(limits[1][n]);
  if (focus) {
    const row = rows.find((item) => item.label === get('focus').value);
    slider.value = (row.bounds[0][n] + row.bounds[1][n]) / 2;
    const link = get('object-link');
    link.href = 'index.html?structure=' + encodeURIComponent(row.label);
    link.textContent = 'Open ' + row.name.toLowerCase() + ' on its own';
    link.hidden = false;
  }
  render();
}

function render() {
  if (sourceMeshes.length !== rows.length || !rows.length) return;
  const plane = get('plane').value,
    [h, v, n] = axes[plane];
  const position = get('position').valueAsNumber;
  const ratio = window.devicePixelRatio || 1;
  const width = section.clientWidth,
    height = section.clientHeight;
  section.width = Math.round(width * ratio);
  section.height = Math.round(height * ratio);
  const ctx = section.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.fillStyle = '#101b24';
  ctx.fillRect(0, 0, width, height);
  const curves = [];
  rows.forEach((row, i) => {
    if (!layers[i].checked || position < row.bounds[0][n] || position > row.bounds[1][n]) return;
    const segments = sectionSegments(sourceMeshes[i].points, sourceMeshes[i].faces, plane, position);
    if (segments.length) curves.push({ row, segments });
  });
  let xMin = limits[0][h],
    xMax = limits[1][h],
    yMin = limits[0][v],
    yMax = limits[1][v];
  if (get('field').value === 'contours' && curves.length) {
    xMin = Infinity;
    xMax = -Infinity;
    yMin = Infinity;
    yMax = -Infinity;
    for (const { segments } of curves)
      for (const segment of segments)
        for (const [x, y] of segment) {
          xMin = Math.min(xMin, x);
          xMax = Math.max(xMax, x);
          yMin = Math.min(yMin, y);
          yMax = Math.max(yMax, y);
        }
  }
  const scale = Math.min(
    (width - 42) / Math.max(xMax - xMin, 2),
    (height - 65) / Math.max(yMax - yMin, 2)
  );
  const X = (x) => width / 2 + (x - (xMin + xMax) / 2) * scale;
  const Y = (y) => height / 2 - (y - (yMin + yMax) / 2) * scale;
  ctx.fillStyle = '#f3f6f7';
  ctx.font = '14px system-ui, sans-serif';
  ctx.fillText('+' + 'XYZ'[v] + ' ↑   +' + 'XYZ'[h] + ' →', 9, 19);
  const mm =
    [0.1, 0.2, 0.5, 1, 2, 5, 10, 20].filter((value) => value * scale <= width * 0.18).pop() || 0.1;
  ctx.fillRect(12, height - 13, mm * scale, 2);
  ctx.fillText(mm + ' mm', 12, height - 20);
  const results = [];
  let count = 0;
  for (const { row, segments } of curves) {
    count += segments.length;
    ctx.strokeStyle = 'rgb(' + row.color.join(',') + ')';
    ctx.lineWidth = row.group === 'duct' ? 2.5 : 1.7;
    ctx.beginPath();
    for (const [a, b] of segments) {
      ctx.moveTo(X(a[0]), Y(a[1]));
      ctx.lineTo(X(b[0]), Y(b[1]));
    }
    ctx.stroke();
    const li = document.createElement('li'),
      swatch = document.createElement('i');
    swatch.style.background = ctx.strokeStyle;
    li.append(swatch, row.name);
    results.push(li);
  }
  get('cut-key').replaceChildren(...results);
  get('position-out').textContent = 'XYZ'[n] + ' = ' + position.toFixed(1) + ' mm';
  get('cut-status').textContent = results.length
    ? results.length + ' selected structures intersect this plane.'
    : 'This plane misses all selected structures. Move the section or select another structure.';
  section.dataset.segments = count;
}

function choose(preset) {
  if (preset === 'left' || preset === 'right') {
    get('rotation').value = preset === 'left' ? 105 : -105;
    get('tilt').value = 12;
  }
  rows.forEach((row, i) => {
    layers[i].checked =
      preset === 'all' ||
      (preset === 'glands' ? row.group === 'gland' : row.side === preset && row.group !== 'landmark');
  });
  layers[0].dispatchEvent(new Event('input'));
}

async function read(url) {
  const response = await fetch(url);
  if (!response.ok) throw Error('Source unavailable.');
  return response.arrayBuffer();
}
async function load() {
  get('retry-sections').hidden = true;
  try {
    const packedRows = await read('surfaces.json');
    if ((await hash(packedRows)) !== document.querySelector('main').dataset.surfacesSha256)
      throw Error('Inventory differs.');
    rows = JSON.parse(new TextDecoder().decode(packedRows));
    if (rows.length !== layers.length || rows.some((row, i) => row.label !== layers[i].value))
      throw Error('Object order differs.');
    sourceMeshes = await Promise.all(
      rows.map(async (row) => {
        const packed = await read(row.file);
        if ((await hash(packed)) !== row.packedSHA256) throw Error('Packed mesh differs.');
        const raw = await new Response(
          new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'))
        ).arrayBuffer();
        if (raw.byteLength !== 12 * (row.vertices + row.triangles) || (await hash(raw)) !== row.sha256)
          throw Error('Decoded mesh differs.');
        return {
          points: new Float32Array(raw, 0, row.vertices * 3),
          faces: new Uint32Array(raw, row.vertices * 12)
        };
      })
    );
    limits = [0, 1].map((k) =>
      [0, 1, 2].map((j) => (k ? Math.max : Math.min)(...rows.map((row) => row.bounds[k][j])))
    );
    get('focus').replaceChildren(...rows.map((row) => new Option(row.name, row.label)));
    const requested = new URLSearchParams(location.search).getAll('structure');
    if (requested.length) {
      const link =
        requested.length === 1 && rows.some((r) => r.label === requested[0]) ? requested[0] : null;
      if (link) get('focus').value = link;
      else {
        get('link-note').textContent =
          'The link does not identify a source object. Choose a group or individual structure.';
        get('link-note').hidden = false;
      }
      layers.forEach((layer) => {
        layer.checked = layer.value === link;
      });
      layers[0].dispatchEvent(new Event('input'));
    }
    get('section-controls').disabled = false;
    get('presets').disabled = false;
    setPlane();
  } catch {
    rows = [];
    sourceMeshes = [];
    get('section-controls').disabled = true;
    get('cut-status').textContent = 'The source geometry could not be verified.';
    get('retry-sections').hidden = false;
  }
}
get('retry-sections').addEventListener('click', load);
get('plane').addEventListener('change', () => setPlane());
get('position').addEventListener('input', render);
get('field').addEventListener('change', render);
get('focus').addEventListener('change', () => {
  const ix = rows.findIndex((r) => r.label === get('focus').value);
  if (ix >= 0) {
    layers[ix].checked = true;
    layers[ix].dispatchEvent(new Event('input'));
  }
  setPlane();
});
for (const btn of get('presets').querySelectorAll('button'))
  btn.addEventListener('click', () => choose(btn.value));
for (const input of layers) input.addEventListener('input', render);
new ResizeObserver(render).observe(section);
load();

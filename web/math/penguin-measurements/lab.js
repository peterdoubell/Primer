import { bins, displayName, domain, fit, readObservations, species, summary, traits } from './data.mjs';
import { plot } from './plot.mjs';

const get = (id) => document.getElementById(id);
const fmt = (value, digits = 2) =>
  value == null ? '—' : value.toLocaleString('en-US', { maximumFractionDigits: digits });
const option = (text, value) => new Option(text, value);
let all = [],
  filtered = [],
  complete = [],
  picks = [],
  sample = [],
  selected = null;
const mode = () => get('mode').value;
function rowTable(id, rows) {
  const body = typeof id === 'string' ? get(id) : id;
  body.replaceChildren(
    ...rows.map(([heading, ...cells]) => {
      const tr = document.createElement('tr'),
        th = document.createElement('th');
      th.scope = 'row';
      th.textContent = heading;
      tr.append(th);
      for (const cell of cells) {
        const td = document.createElement('td');
        td.textContent = cell;
        tr.append(td);
      }
      return tr;
    })
  );
}
function configureAxes(changed) {
  const ids = ['x', 'y', 'z'];
  if (changed && ids.includes(changed)) {
    // Exchange a duplicate axis for the former trait of the edited one.
    for (const id of ids)
      if (id !== changed && get(id).value === get(changed).value) {
        get(id).value = get(changed).dataset.previous;
      }
  }
  for (const id of ids) get(id).dataset.previous = get(id).value;
}
function renderChart() {
  if (!all.length) return;
  get('yaw-value').textContent = get('yaw').value + '°';
  get('pitch-value').textContent = get('pitch').value + '°';
  picks = plot(get('chart'), all, complete, {
    mode: mode(),
    x: get('x').value,
    y: get('y').value,
    z: get('z').value,
    yaw: get('yaw').valueAsNumber,
    pitch: get('pitch').valueAsNumber,
    selected
  });
}
function showRecord() {
  const r = filtered.find((row) => row.row === selected);
  const values = r
    ? [
        ['Source row', String(r.row)],
        ['Species', displayName(r.species)],
        ['Island and year', r.island + ' · ' + r.year],
        ...Object.entries(traits).map(([key, t]) => [
          t.name,
          r[key] == null ? 'Unrecorded' : fmt(r[key]) + ' ' + t.unit
        ]),
        ['Sex as recorded', r.sex || 'Unrecorded']
      ]
    : [];
  rowTable('observations', values);
  const focus = get('selected-point');
  focus.hidden = mode() === 'hist' || !r;
  if (!focus.hidden) {
    const keys = mode() === 'xyz' ? ['x', 'y', 'z'] : ['x', 'y'];
    focus.textContent =
      'Record ' +
      r.row +
      ' · ' +
      displayName(r.species) +
      ' · ' +
      keys
        .map((id) => {
          const key = get(id).value,
            value = r[key];
          return (
            traits[key].name + ' ' + (value == null ? 'unrecorded' : fmt(value) + ' ' + traits[key].unit)
          );
        })
        .join(' · ');
  }
}
function newQuestion() {
  sample = [];
  const x = get('x').value;
  const available = filtered.filter((row) => Number.isFinite(row[x]));
  for (let i = 0; i < 3 && available.length; i++) {
    const at = Math.floor(Math.random() * available.length);
    sample.push(available.splice(at, 1)[0]);
  }
  const ready = sample.length === 3;
  const unit = traits[x].unit;
  get('question').textContent = ready
    ? 'Records ' +
      sample.map((r) => r.row).join(', ') +
      ' have measurements of ' +
      sample.map((r) => fmt(r[x])).join(', ') +
      ' ' +
      unit +
      '. What is their median?'
    : 'This selection needs at least three measured records.';
  get('answer-unit').textContent = '(' + unit + ')';
  for (const id of ['check', 'another', 'answer']) get(id).disabled = !ready;
  get('answer').value = '';
  get('feedback').textContent = '';
}
function groupResults() {
  const target = get('group-summary');
  target.replaceChildren();
  const title = document.createElement('h2');
  const table = document.createElement('table'),
    body = document.createElement('tbody');
  const x = get('x').value,
    y = get('y').value;
  if (mode() === 'hist') {
    title.textContent = 'Median by species (' + traits[x].unit + ')';
    rowTable(
      body,
      species.map((sp) => {
        const subset = filtered.filter((row) => row.species === sp),
          s = summary(subset, x);
        return [displayName(sp), fmt(s?.median), (s?.n ?? 0) + ' measured'];
      })
    );
  } else {
    title.textContent = 'Correlation of X and Y';
    const groups = [['Selected records', complete]];
    if (!get('group').value)
      species.forEach((sp) => groups.push([displayName(sp), complete.filter((r) => r.species === sp)]));
    rowTable(
      body,
      groups.map(([name, rows]) => [name, fmt(fit(rows, x, y)?.r, 3), rows.length + ' paired'])
    );
  }
  table.append(body);
  target.append(title, table);
  if (mode() !== 'hist' && !get('group').value) {
    const pooled = fit(complete, x, y)?.r;
    const within = species.map(
      (sp) =>
        fit(
          complete.filter((row) => row.species === sp),
          x,
          y
        )?.r
    );
    if (Number.isFinite(pooled) && within.every((r) => Number.isFinite(r) && r * pooled < 0)) {
      const note = document.createElement('p');
      note.textContent =
        'The direction reverses when these species are combined. Select each species to see how the groups occupy different parts of the plot.';
      target.append(note);
    }
  }
}
function update(changed) {
  if (!all.length) return;
  configureAxes(changed);
  const m = mode(),
    x = get('x').value,
    y = get('y').value,
    z = get('z').value;
  const keys = m === 'hist' ? [x] : m === 'xy' ? [x, y] : [x, y, z];
  filtered = all.filter(
    (row) =>
      (!get('group').value || get('group').value === row.species) &&
      (!get('island').value || get('island').value === row.island) &&
      (!get('year').value || get('year').value === row.year)
  );
  complete = filtered.filter((row) => keys.every((key) => Number.isFinite(row[key])));
  if (!filtered.some((row) => row.row === selected)) selected = filtered[0]?.row ?? null;
  get('y-field').hidden = m === 'hist';
  get('z-field').hidden = m !== 'xyz';
  get('rotations').hidden = m !== 'xyz';
  get('x-label').textContent = m === 'hist' ? 'Measurement' : 'Horizontal axis (X)';
  get('chart').classList.toggle('orbit', m === 'xyz');
  get('record').replaceChildren(
    ...filtered.map((r) => option(r.row + ' · ' + displayName(r.species) + ' · ' + r.island, r.row))
  );
  get('record').value = selected ?? '';
  get('record').disabled = !filtered.length;
  const missing = filtered.length - complete.length;
  get('status').textContent = filtered.length
    ? complete.length +
      ' of ' +
      filtered.length +
      ' selected birds have all measurements for this view.' +
      (missing
        ? ' Missing measurements exclude ' +
          missing +
          ' from the plot. Their records are available below.'
        : '')
    : 'No observations match these filters.';
  const xStats = summary(filtered, x);
  get('summary-heading').textContent = traits[x].name + ' (' + traits[x].unit + ')';
  rowTable(
    'summary',
    xStats
      ? [
          ['Measured records', xStats.n],
          ['Mean', fmt(xStats.mean)],
          ['Median', fmt(xStats.median)],
          ['Middle half (Q1–Q3)', fmt(xStats.q1) + '–' + fmt(xStats.q3)],
          ['Range', fmt(xStats.min) + '–' + fmt(xStats.max)],
          ['Sample standard deviation', fmt(xStats.sd)]
        ]
      : [['Measured records', 0]]
  );
  const caption = get('caption');
  if (m === 'hist') {
    caption.textContent =
      'Each bar spans ' +
      traits[x].bin +
      ' ' +
      traits[x].unit +
      '. The colours count birds of each species.';
  } else if (m === 'xy') {
    const f = fit(complete, x, y);
    caption.textContent =
      'Each point is one bird. ' +
      (f
        ? 'The least-squares line changes by ' +
          fmt(f.slope, 4) +
          ' ' +
          traits[y].unit +
          ' on Y per ' +
          traits[x].unit +
          ' on X over the observed range. '
        : '') +
      'Select a point to inspect its record.';
  } else {
    caption.textContent =
      keys
        .map(
          (k, i) =>
            ['X', 'Y', 'Z'][i] +
            ' = ' +
            traits[k].name +
            ' (' +
            domain(all, k)
              .map((n) => fmt(n))
              .join('–') +
            ' ' +
            traits[k].unit +
            ')'
        )
        .join(' · ') + '. Drag or use the arrow keys to turn the plot. Select a point for its record.';
  }
  groupResults();
  const histogram = get('bins');
  histogram.hidden = m !== 'hist';
  if (m === 'hist')
    rowTable(
      'bin-counts',
      bins(complete, x, domain(all, x)).map((b) => [
        fmt(b.start) + ' to <' + fmt(b.end),
        ...b.counts,
        b.total
      ])
    );
  showRecord();
  renderChart();
  newQuestion();
}
get('record').addEventListener('change', () => {
  selected = Number(get('record').value);
  showRecord();
  renderChart();
});
for (const id of ['group', 'island', 'year', 'mode', 'x', 'y', 'z'])
  get(id).addEventListener('change', () => update(id));
for (const id of ['yaw', 'pitch']) get(id).addEventListener('input', renderChart);
const chart = get('chart');
let drag = null;
chart.addEventListener('pointerdown', (e) => {
  drag = {
    x: e.clientX,
    y: e.clientY,
    yaw: get('yaw').valueAsNumber,
    pitch: get('pitch').valueAsNumber,
    moved: false
  };
  if (mode() === 'xyz') chart.setPointerCapture(e.pointerId);
});
chart.addEventListener('pointermove', (e) => {
  if (!drag || mode() !== 'xyz') return;
  const dx = e.clientX - drag.x,
    dy = e.clientY - drag.y;
  if (Math.hypot(dx, dy) < 4 && !drag.moved) return;
  drag.moved = true;
  get('yaw').value = ((drag.yaw + dx * 0.55 + 540) % 360) - 180;
  get('pitch').value = Math.max(-75, Math.min(75, drag.pitch - dy * 0.55));
  renderChart();
});
chart.addEventListener('pointercancel', () => {
  drag = null;
});
chart.addEventListener('pointerup', (e) => {
  if (!drag) return;
  const moved = drag.moved;
  drag = null;
  if (moved || !picks.length) return;
  const box = chart.getBoundingClientRect(),
    x = e.clientX - box.left,
    y = e.clientY - box.top;
  let closest = null,
    dist = 14;
  for (const p of picks) {
    const d = Math.hypot(p.px - x, p.py - y);
    if (d <= dist) {
      closest = p;
      dist = d;
    }
  }
  if (closest) {
    selected = closest.row;
    get('record').value = selected;
    get('record').closest('details').open = true;
    showRecord();
    renderChart();
  }
});
chart.addEventListener('keydown', (e) => {
  if (mode() !== 'xyz' || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) return;
  e.preventDefault();
  if (['ArrowLeft', 'ArrowRight'].includes(e.key))
    get('yaw').value =
      ((get('yaw').valueAsNumber + (e.key === 'ArrowRight' ? 5 : -5) + 540) % 360) - 180;
  else
    get('pitch').value = Math.max(
      -75,
      Math.min(75, get('pitch').valueAsNumber + (e.key === 'ArrowUp' ? 5 : -5))
    );
  renderChart();
});
get('bills').addEventListener('click', () => {
  get('mode').value = 'xy';
  get('x').value = 'bill_length_mm';
  get('y').value = 'bill_depth_mm';
  get('z').value = 'body_mass_g';
  update();
});
get('another').addEventListener('click', newQuestion);
get('practice').addEventListener('submit', (e) => {
  e.preventDefault();
  if (sample.length !== 3) return;
  const key = get('x').value,
    sorted = sample.map((r) => r[key]).sort((a, b) => a - b);
  get('feedback').textContent =
    Math.abs(get('answer').valueAsNumber - sorted[1]) < 1e-7
      ? 'Correct. The ordered measurements are ' +
        sorted.map((v) => fmt(v)).join(', ') +
        '. The middle measurement is ' +
        fmt(sorted[1]) +
        ' ' +
        traits[key].unit +
        '.'
      : 'Arrange the three measurements from smallest to largest, then enter the second one.';
});
async function start() {
  const response = await fetch('penguins.csv');
  if (!response.ok) throw Error('Field records unavailable.');
  const bytes = await response.arrayBuffer();
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (b) =>
    b.toString(16).padStart(2, '0')
  ).join('');
  if (hash !== 'f204db2c753b0937caac3cb35258562c14f073e4bbc76be24b4c51ce22767a93')
    throw Error('Field data checksum changed.');
  all = readObservations(new TextDecoder().decode(bytes));
  for (const id of ['x', 'y', 'z'])
    get(id).replaceChildren(
      ...Object.entries(traits).map(([k, t]) => option(t.name + ' (' + t.unit + ')', k))
    );
  get('x').value = 'body_mass_g';
  get('y').value = 'bill_depth_mm';
  get('z').value = 'flipper_length_mm';
  get('explore').disabled = false;
  update();
  new ResizeObserver(renderChart).observe(chart);
}
start().catch((e) => {
  get('status').textContent = 'The field records could not be verified. Reload to try again.';
});

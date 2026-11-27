export function estimates(cellCounts, spacingMm, step) {
  if (!Number.isInteger(step) || step < 1 || step > cellCounts.length)
    throw RangeError('Invalid sampling step');
  const mlPerCell = (spacingMm[0] * spacingMm[1] * spacingMm[2]) / 1000;
  const totals = Array(step).fill(0);
  cellCounts.forEach((count, k) => {
    totals[k % step] += count;
  });
  const exact = totals.reduce((a, b) => a + b, 0) * mlPerCell;
  const volumes = totals.map((n) => n * step * mlPerCell);
  const mean = volumes.reduce((a, b) => a + b, 0) / step;
  const sd = Math.sqrt(volumes.reduce((sum, v) => sum + (v - mean) ** 2, 0) / step);
  return { exact, volumes, mean, sd };
}

const fmt = (x, n = 2) => x.toLocaleString('en-US', { maximumFractionDigits: n });
const $ = (id) => document.getElementById(id);
const svgNS = 'http://www.w3.org/2000/svg';
function mark(tag, attributes, text) {
  const node = document.createElementNS(svgNS, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  if (text !== undefined) node.textContent = text;
  return node;
}
function randomStart(stride) {
  const threshold = 0x100000000 - (0x100000000 % stride),
    word = new Uint32Array(1);
  do {
    crypto.getRandomValues(word);
  } while (word[0] >= threshold);
  return word[0] % stride;
}
export function samplingLab(profile, record, inspect) {
  const target = $('sample-target'),
    step = $('sample-step'),
    start = $('sample-start');
  for (const row of record.labels) target.append(new Option(row.sourceName, String(row.code)));
  let data, counts, stride, offset;
  function changeStart(index) {
    start.value = String(index);
    draw();
  }
  function draw() {
    $('score').textContent = '';
    stride = Number(step.value);
    offset = Number(start.value);
    const code = Number(target.value);
    counts = profile.countsByAxialSection.map((row) =>
      code ? row[code - 1] : row.reduce((a, b) => a + b, 0)
    );
    data = estimates(counts, profile.spacingMm, stride);
    const spacing = profile.spacingMm,
      areaFactor = (spacing[0] * spacing[1]) / 100;
    const sampled = counts.map((_, i) => i).filter((k) => k % stride === offset);
    const sumAreas = sampled.reduce((sum, k) => sum + counts[k], 0) * areaFactor;
    const estimate = data.volumes[offset];
    $('sample-result').textContent =
      fmt(estimate) + ' mL estimated · ' + fmt(data.exact) + ' mL measured across all 47 sections.';
    $('sample-formula').textContent =
      'Sum of sampled areas ' +
      fmt(sumAreas) +
      ' cm² × ' +
      fmt((stride * spacing[2]) / 10) +
      ' cm between samples = ' +
      fmt(estimate) +
      ' mL.';
    $('spread').textContent =
      'Across ' +
      stride +
      (stride === 1 ? ' possible start' : ' possible starts') +
      ', the mean is ' +
      fmt(data.mean) +
      ' mL and the standard deviation is ' +
      fmt(data.sd) +
      ' mL.';
    $('sample-summary').textContent = 'Source indices ' + sampled.join(', ') + '.';
    const chart = $('profile-chart');
    chart.replaceChildren();
    const left = 72,
      top = 12,
      bottom = 157,
      w = 705 - left,
      bar = w / counts.length;
    const peak = Math.max(...counts) * areaFactor;
    const scale = (bottom - top) / peak;
    for (const ratio of [0, 0.5, 1]) {
      const y = bottom - ratio * (bottom - top);
      chart.append(
        mark('line', { x1: left, x2: 710, y1: y, y2: y, stroke: '#45565f' }),
        mark('text', { x: left - 8, y: y + 4, 'text-anchor': 'end' }, fmt(ratio * peak, 1))
      );
    }
    chart.append(mark('text', { x: 6, y: 24 }, 'cm²'));
    for (let k = 0; k < counts.length; k++) {
      const area = counts[k] * areaFactor,
        height = area * scale;
      const r = mark('rect', {
        x: left + k * bar + 1,
        y: bottom - height,
        width: Math.max(1, bar - 2),
        height,
        fill: k % stride === offset ? '#ffc76a' : '#6ca2ac'
      });
      r.append(mark('title', {}, 'K ' + k + ' · ' + fmt(area) + ' cm²'));
      chart.append(r);
    }
    for (const k of [0, 10, 20, 30, 40, 46])
      chart.append(mark('text', { x: left + (k + 0.5) * bar, y: 177, 'text-anchor': 'middle' }, k));
    chart.append(mark('text', { x: 390, y: 198, 'text-anchor': 'middle' }, 'Axial section index K'));
    const areas = $('sample-areas');
    areas.replaceChildren();
    for (const k of sampled) {
      const tr = document.createElement('tr'),
        heading = document.createElement('th');
      heading.scope = 'row';
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = 'Inspect K ' + k;
      button.onclick = () => inspect(k, code);
      heading.append(button);
      const cm2 = counts[k] * areaFactor,
        area = document.createElement('td'),
        slab = document.createElement('td');
      area.textContent = fmt(cm2);
      slab.textContent = fmt((cm2 * stride * spacing[2]) / 10);
      tr.append(heading, area, slab);
      areas.append(tr);
    }
    const rows = $('offset-table');
    rows.replaceChildren();
    data.volumes.forEach((v, i) => {
      const tr = document.createElement('tr'),
        heading = document.createElement('th');
      heading.scope = 'row';
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = 'Start ' + i;
      b.setAttribute('aria-pressed', String(i === offset));
      b.onclick = () => changeStart(i);
      heading.append(b);
      tr.append(heading);
      for (const value of [Math.ceil((counts.length - i) / stride), fmt(v), fmt(v - data.exact)]) {
        const td = document.createElement('td');
        td.textContent = value;
        tr.append(td);
      }
      rows.append(tr);
    });
    $('sample-section').replaceChildren(
      ...sampled.map((k) => new Option('K ' + k + (counts[k] ? '' : ' · empty'), k))
    );
    const inside = sampled.find((k) => counts[k]);
    if (inside !== undefined) $('sample-section').value = inside;
  }
  function resetStarts() {
    start.replaceChildren(...Array.from({ length: Number(step.value) }, (_, i) => new Option(i, i)));
    draw();
  }
  step.onchange = resetStarts;
  start.onchange = target.onchange = draw;
  $('random-start').onclick = () => changeStart(randomStart(Number(step.value)));
  $('closest').onclick = () => {
    const errors = data.volumes.map((v) => Math.abs(v - data.exact));
    const best = Math.min(...errors);
    $('score').textContent =
      errors[offset] <= best + 1e-9
        ? 'This start is closest. Its absolute error is ' + fmt(best) + ' mL.'
        : 'This start differs by ' + fmt(errors[offset]) + ' mL. Compare the other starting sections.';
  };
  $('inspect-sample').onclick = () => inspect(Number($('sample-section').value), Number(target.value));
  resetStarts();
  $('sampling-controls').disabled = false;
}

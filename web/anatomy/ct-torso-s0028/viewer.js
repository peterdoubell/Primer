import {
  FetchPool,
  fingerprint,
  nativeReader,
  planes,
  verifiedBytes
} from '../segthy-001/native-volume.mjs';
import { meshView } from '../segthy-001/mesh-view.mjs';

const get = (id) => document.getElementById(id);
const svgNS = 'http://www.w3.org/2000/svg';
const axesNames = ['I', 'J', 'K'];
const coords = ['i', 'j', 'k'].map(get);
const read = (row, signal) => verifiedBytes(row, signal, import.meta.url);
const mesh = meshView(
  get('surface'),
  get('mesh-locator'),
  get('mesh-status'),
  {
    yaw: get('yaw'),
    pitch: get('pitch'),
    zoom: get('zoom'),
    yawValue: get('yaw-value'),
    pitchValue: get('pitch-value'),
    reset: get('reset-orbit'),
    retry: get('retry-mesh')
  },
  read
);
const image = get('ct'),
  ctx = image.getContext('2d');
let record,
  reader,
  label,
  position,
  frame,
  crop,
  controller,
  serial = 0;
let byName, byCode, areas, exam, reportGuide;
const representationModes = new Map([
  ['clinical_image', 'raw'], ['schematic', 'selected-map'], ['model', 'outline']
]);
const guideFingerprint = 'e846bceb6fa33fd431f8b0da9fec3e73d043d0038bc51ec3467b3ff88185b359';
const presets = { soft: [-125, 225], lung: [-1350, 150], bone: [-300, 1200] };
const format = (value) => value.toLocaleString('en-US', { maximumFractionDigits: 2 });
function selectOptions(rows) {
  const groups = new Map();
  for (const row of rows) {
    if (!groups.has(row.group)) {
      const group = document.createElement('optgroup');
      group.label = row.group;
      groups.set(row.group, group);
    }
    groups
      .get(row.group)
      .append(new Option(row.name + (row.voxelCount ? '' : ' · empty mask'), row.sourceLabel));
  }
  get('structure').replaceChildren(...groups.values());
}
function currentArea() {
  return areas.find((a) => a.id === get('region').value);
}
function areaLabels(area, labels) {
  if (!area) return labels;
  const included = new Set(area.sourceLabels);
  return labels.filter((item) => included.has(item.sourceLabel));
}
function guideTargets() {
  return reportGuide?.[currentArea()?.id]?.targets || [];
}
function showTarget(target) {
  const state = {
    labelled: 'This case includes a source label for this structure.',
    reaches_edge: 'The source label reaches the scan boundary. Its visible extent ends there.',
    empty: 'The publisher supplied an empty mask. This case has no delineated example.',
    unlabelled: 'This case has no separate source label for this structure.'
  };
  get('target-status').textContent = target ? state[target.state] : '';
  const links = get('target-views');
  links.replaceChildren();
  const sourceViews = [
    [target?.links.clinical_image, 'Unmarked CT'], [target?.links.schematic, 'Section map'],
    [target?.links.model, '3D surface']
  ];
  for (const region of target?.separateCT || []) {
    const name = 'Separate CT · ' + region.name;
    sourceViews.push([region.views.clinical_image, name + ' on CT', true],
      [region.views.schematic, name + ' map', true], [region.views.model, name + ' in 3D', true]);
  }
  sourceViews.push([target?.separateMRI?.schematic, 'Separate MRI · segment map', true],
    [target?.separateMRI?.model, 'Separate MRI · 3D surface', true]);
  for (const [href, title, separateCase] of sourceViews) {
    if (!href) continue;
    const link = document.createElement('a');
    link.href = href;
    link.textContent = title;
    if (separateCase) {
      link.target = '_blank';
      link.rel = 'noopener';
      link.title = 'Open the comparison study in a new tab';
    }
    link.setAttribute('aria-label', title + ' · ' + target.name + (link.target ? ' (opens in a new tab)' : ''));
    links.append(link);
  }
  links.hidden = !links.childElementCount;
}
function showGuide(area) {
  const entry = reportGuide?.[area?.id];
  get('report-guide').hidden = !entry;
  if (!entry) return;
  get('guide-note').textContent = entry.note;
  const guidance = get('guide-guidance');
  guidance.replaceChildren(...(entry.guidance || []).map(source => {
    const link = document.createElement('a');
    link.href = source.url;
    link.textContent = source.title;
    link.target = '_blank';
    link.rel = 'noopener';
    return link;
  }));
  guidance.hidden = !guidance.childElementCount;
  const control = get('report-target');
  control.replaceChildren(new Option('Choose a report structure', ''),
    ...entry.targets.map((t, i) => new Option(t.name, String(i))));
  get('target-control').hidden = !entry.targets.length;
  get('comparison').hidden = !entry.comparison;
  if (entry.comparison) {
    const link = get('comparison').querySelector('a');
    link.href = entry.comparison.href;
    link.textContent = entry.comparison.title;
    link.setAttribute('aria-label', entry.comparison.title + ' (opens in a new tab)');
  }
  showTarget(null);
}
function syncGuide(row) {
  if (!reportGuide || get('report-guide').hidden) return;
  const targets = guideTargets();
  const index = row ? targets.findIndex(t => t.sourceLabel === row.sourceLabel) : -1;
  get('report-target').value = index < 0 ? '' : String(index);
  showTarget(targets[index]);
}
get('report-target').addEventListener('change', () => {
  const value = get('report-target').value;
  const target = value === '' ? undefined : guideTargets()[Number(value)];
  selectLabel(target?.sourceLabel ? byName.get(target.sourceLabel) : null, true);
  // Unlabelled report structures have no matching option in the source inventory.
  get('report-target').value = value;
  showTarget(target);
});
function setArea(area, requested, focus) {
  showGuide(area);
  get('search').value = '';
  get('matches').hidden = true;
  const subset = areaLabels(area, record.labels);
  selectOptions(subset);
  const match =
    requested === undefined
      ? subset.find((row) => row.voxelCount) || subset[0]
      : subset.find((r) => r.sourceLabel === requested);
  get('scope').textContent = area
    ? area.note
    : 'All 117 publisher classes are listed, including the empty masks.';
  if (!subset.length) get('structure').append(new Option('No independently labelled structure', ''));
  get('structure').disabled = !subset.length;
  selectLabel(match || null, focus);
}
function selectLabel(row, focus) {
  label = row;
  syncGuide(row);
  get('structure').value = row?.sourceLabel ?? '';
  get('focus').disabled = !row?.voxelCount;
  get('link').hidden = !row;
  if (row)
    get('link').href =
      'index.html?exam=' + encodeURIComponent(exam) + '&label=' + encodeURIComponent(row.sourceLabel);
  get('evidence').textContent = row
    ? row.sourceLabel +
      ' · ' +
      format(row.voxelCount) +
      ' source mask cells' +
      (row.voxelCount
        ? ' · ' +
          format((row.voxelCount * record.spacingMm.reduce((a, b) => a * b)) / 1000) +
          ' mL in this segmentation.'
        : '. No surface can be derived from this empty mask.') +
      (row.touchesGridEdge ? ' This label reaches the edge of the scan.' : '')
    : 'Plain CT and the source section map remain available for this report area.';
  mesh.load(record, row || { voxelCount: 0 });
  if (row?.voxelCount && focus) position = [...row.focus];
  controls();
  loadSection();
}
function controls() {
  const ax = planes[get('plane').value];
  get('slice').max = record.shape[ax.normal] - 1;
  get('slice').value = position[ax.normal];
  get('slice-value').textContent =
    axesNames[ax.normal] + ' ' + position[ax.normal] + ' / ' + (record.shape[ax.normal] - 1);
  coords.forEach((el, k) => {
    el.min = 0;
    el.max = record.shape[k] - 1;
    el.value = position[k];
  });
  mesh.locator({ axes: ax, position: [...position], spacing: record.spacingMm });
}
function sampleNames(index) {
  return [frame.labels[index], frame.overlap[index]]
    .filter(Boolean)
    .map((code) => byCode.get(code).name);
}
function describeVoxel() {
  if (!frame || !crop) return;
  const { horizontal: h, vertical: v } = frame.axes;
  const x = position[h],
    y = frame.height - 1 - position[v],
    index = y * frame.width + x;
  const labels = sampleNames(index);
  const world = record.affine
    .slice(0, 3)
    .map((row) => row[3] + position.reduce((sum, value, k) => sum + value * row[k], 0));

  get('voxel').textContent =
    'I, J, K = ' +
    position.join(', ') +
    ' · stored CT ' +
    frame.image[index] +
    ' · ' +
    (labels.length ? labels.join(' and ') : 'no source mask at this voxel') +
    '. Source sform RAS (mm): ' +
    world.map((v) => format(v)).join(', ') +
    '.';
  const overlay = get('cursor');
  overlay.replaceChildren();
  overlay.setAttribute('viewBox', '0 0 ' + crop.width + ' ' + crop.height);
  const px =
      (get('orientation').value === 'radiology' ? crop.width - 1 - (x - crop.x) : x - crop.x) + 0.5,
    py = y - crop.y + 0.5;
  if (px >= 0 && px < crop.width && py >= 0 && py < crop.height) {
    const cross = document.createElementNS(svgNS, 'path');
    cross.setAttribute('d', `M${px - 5} ${py}h3 m4 0h3 M${px} ${py - 5}v3 m0 4v3`);
    cross.setAttribute('stroke', '#ffdb79');
    cross.setAttribute('fill', 'none');
    cross.setAttribute('stroke-width', '1');
    overlay.append(cross);
  }
}
function regionOfInterest() {
  if (get('field').value !== 'detail' || !label?.voxelCount)
    return { x: 0, y: 0, width: frame.width, height: frame.height };
  const [lo, hi] = label.boundsIndex,
    { horizontal: h, vertical: v } = frame.axes;
  const margin = 12,
    x = Math.max(0, lo[h] - margin),
    y = Math.max(0, frame.height - 1 - hi[v] - margin);
  return {
    x,
    y,
    width: Math.min(frame.width, hi[h] + margin + 1) - x,
    height: Math.min(frame.height, frame.height - lo[v] + margin) - y
  };
}
function contains(index, code) {
  return frame.labels[index] === code || frame.overlap[index] === code;
}
function render() {
  if (!frame) return;
  const black = get('low').valueAsNumber,
    white = get('high').valueAsNumber,
    mode = get('mode').value;
  if (!['map', 'selected-map'].includes(mode) && !(white > black)) {
    crop = null;
    get('image-frame').hidden = true;
    get('voxel').textContent = '';
    get('section-status').textContent = 'Set the white point above the black point.';
    return;
  }
  crop = regionOfInterest();
  image.width = crop.width;
  image.height = crop.height;
  const raster = ctx.createImageData(crop.width, crop.height),
    counts = new Map();
  let shared = 0;
  const code = label?.code,
    w = frame.width;
  for (let y = 0; y < crop.height; y++)
    for (let x = 0; x < crop.width; x++) {
      const sx = crop.x + (get('orientation').value === 'radiology' ? crop.width - 1 - x : x),
        sy = y + crop.y,
        i = sx + w * sy,
        dst = (x + crop.width * y) * 4;
      const first = frame.labels[i],
        second = frame.overlap[i];
      if (first) counts.set(first, (counts.get(first) || 0) + 1);
      if (second) {
        shared++;
        counts.set(second, (counts.get(second) || 0) + 1);
      }
      let colour = null;
      if (mode === 'selected-map') {
        colour = code && contains(i, code) ? (second ? [255, 255, 255] : label.color) : [13, 20, 27];
      } else if (mode === 'map')
        colour = second ? [255, 255, 255] : first ? byCode.get(first).color : [13, 20, 27];
      else if (
        mode === 'outline' &&
        code &&
        contains(i, code) &&
        (sx === 0 ||
          sy === 0 ||
          sx === w - 1 ||
          sy === frame.height - 1 ||
          !contains(i - 1, code) ||
          !contains(i + 1, code) ||
          !contains(i - w, code) ||
          !contains(i + w, code))
      )
        colour = label.color;
      if (colour) {
        raster.data[dst] = colour[0];
        raster.data[dst + 1] = colour[1];
        raster.data[dst + 2] = colour[2];
      } else
        raster.data[dst] =
          raster.data[dst + 1] =
          raster.data[dst + 2] =
            (255 * (frame.image[i] - black)) / (white - black);
      raster.data[dst + 3] = 255;
    }
  ctx.putImageData(raster, 0, 0);
  get('image-frame').style.aspectRatio =
    crop.width * frame.spacing[0] + ' / ' + crop.height * frame.spacing[1];
  const letters =
    get('orientation').value === 'radiology'
      ? { ij: ['A', 'R', 'P', 'L'], ik: ['S', 'R', 'I', 'L'], jk: ['S', 'A', 'I', 'P'] }[
          get('plane').value
        ]
      : [
          '+' + axesNames[frame.axes.vertical],
          '−' + axesNames[frame.axes.horizontal],
          '−' + axesNames[frame.axes.vertical],
          '+' + axesNames[frame.axes.horizontal]
        ];
  ['top-edge', 'left-edge', 'bottom-edge', 'right-edge'].forEach((id, i) => {
    get(id).textContent = letters[i];
  });
  get('image-frame').hidden = false;
  get('section-status').textContent =
    crop.width +
    ' × ' +
    crop.height +
    ' native pixels in view · ' +
    shared +
    ' shared mask cells · ' +
    (label
      ? format((counts.get(label.code) || 0) * frame.spacing[0] * frame.spacing[1]) +
        ' mm² of ' +
        label.name.toLowerCase() +
        ' in view.'
      : 'No structure selected.');
  const rows = [];
  for (const [id, n] of [...counts].sort((a, b) => b[1] - a[1])) {
    const part = byCode.get(id),
      tr = document.createElement('tr'),
      th = document.createElement('th'),
      td = document.createElement('td'),
      btn = document.createElement('button');
    th.scope = 'row';
    btn.type = 'button';
    btn.textContent = part.name;
    btn.addEventListener('click', () => {
      get('region').value = '';
      setArea(undefined, part.sourceLabel, false);
    });
    th.append(btn);
    td.textContent = format(n * frame.spacing[0] * frame.spacing[1]);
    tr.append(th, td);
    rows.push(tr);
  }
  get('key').replaceChildren(...rows);
  describeVoxel();
}
async function loadSection() {
  if (!reader) return;
  controller?.abort();
  controller = new AbortController();
  const ticket = ++serial;
  const { signal } = controller;
  get('retry').hidden = true;
  if (
    frame &&
    frame.axes === planes[get('plane').value] &&
    frame.fixed === position[frame.axes.normal]
  ) {
    render();
    return;
  }
  frame = null;
  crop = null;
  get('image-frame').hidden = true;
  get('key').replaceChildren();
  get('voxel').textContent = '';
  get('section-status').textContent = 'Verifying the source section…';
  try {
    const next = await reader.section(get('plane').value, position, signal);
    if (ticket !== serial || signal.aborted) return;
    frame = next;
    render();
  } catch {
    if (ticket !== serial || signal.aborted) return;
    get('retry').hidden = false;
    get('section-status').textContent = 'This source section could not be verified. Retry the section.';
  }
}
function go(next) {
  position = next;
  controls();
  loadSection();
}
get('go').addEventListener('click', () => {
  const next = coords.map((el) => el.valueAsNumber);
  if (!next.every((x, k) => Number.isInteger(x) && x >= 0 && x < record.shape[k])) {
    get('voxel').textContent = 'Enter a source index within each displayed range.';
    return;
  }
  go(next);
});
get('search').addEventListener('input', () => {
  if (!record) return;
  const words = get('search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const all = areaLabels(currentArea(), record.labels);
  const matches = all.filter((row) => {
    const text = (row.name + ' ' + row.sourceLabel + ' ' + row.group).toLowerCase();
    return words.every((word) => text.includes(word));
  });
  selectOptions(matches);
  get('structure').disabled = !matches.length;
  if (matches.some((row) => row === label)) get('structure').value = label.sourceLabel;
  else {
    get('structure').add(
      new Option(
        matches.length ? 'Choose a matching structure' : 'No matching structure',
        '',
        true,
        true
      ),
      0
    );
    get('structure').options[0].disabled = true;
  }
  get('matches').hidden = !words.length;
  get('matches').textContent = matches.length + ' of ' + all.length + ' source classes match.';
});
get('region').addEventListener('change', () => setArea(currentArea(), undefined, true));
get('structure').addEventListener('change', () => selectLabel(byName.get(get('structure').value), true));
get('focus').addEventListener('click', () => {
  if (label?.focus) go([...label.focus]);
});
get('plane').addEventListener('change', () => go([...position]));
get('slice').addEventListener('input', () => {
  const p = [...position];
  p[planes[get('plane').value].normal] = get('slice').valueAsNumber;
  go(p);
});
get('retry').addEventListener('click', loadSection);
for (const id of ['low', 'high'])
  get(id).addEventListener('input', () => {
    get('window').value = 'custom';
    render();
  });
for (const id of ['field', 'mode', 'orientation']) get(id).addEventListener('change', render);
get('window').addEventListener('change', () => {
  const range = presets[get('window').value];
  if (range) {
    get('low').value = range[0];
    get('high').value = range[1];
    render();
  }
});
image.addEventListener('click', (e) => {
  if (!frame || !crop) return;
  const b = image.getBoundingClientRect(),
    h = frame.axes.horizontal,
    v = frame.axes.vertical;
  const x = Math.min(
    crop.width - 1,
    Math.max(0, Math.floor(((e.clientX - b.left) * crop.width) / b.width))
  );
  const y = Math.min(
    crop.height - 1,
    Math.max(0, Math.floor(((e.clientY - b.top) * crop.height) / b.height))
  );
  position[h] = crop.x + (get('orientation').value === 'radiology' ? crop.width - 1 - x : x);
  position[v] = frame.height - 1 - crop.y - y;
  controls();
  describeVoxel();
});
image.addEventListener('keydown', (e) => {
  if (!frame || !['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
  e.preventDefault();
  const n = frame.axes.normal;
  const next = [...position];
  next[n] = Math.min(record.shape[n] - 1, Math.max(0, next[n] + (e.key === 'ArrowRight' ? 1 : -1)));
  go(next);
});
async function start() {
  const res = await fetch('manifest.json');
  if (!res.ok) throw Error('Missing inventory');
  const bytes = await res.arrayBuffer();
  if ((await fingerprint(bytes)) !== '046d813e59dd34ff06e83398ef3f323b76b2f6d404e20e649a7267fb380046cd')
    throw Error('Inventory changed');
  record = JSON.parse(new TextDecoder().decode(bytes));
  reader = nativeReader(record, new FetchPool(3), read, 36 * 1024 * 1024);
  byName = new Map(record.labels.map((row) => [row.sourceLabel, row]));
  byCode = new Map(record.labels.map((row) => [row.code, row]));
  const query = new URLSearchParams(location.search);
  const referrals = query.getAll('from');
  if (referrals.length === 1 && ['ct.liver-mass', 'ct.liver-lirads', 'ct.liver-lirads-calculated'].includes(referrals[0])) {
    get('referring-report').hidden = false;
    get('referring-report').querySelector('a').href = '/app/#/radiology/' + referrals[0];
  }
  const exams = query.getAll('exam');
  const badExam =
    exams.length > 1 ||
    (exams.length && !['ct.trauma-panscan', 'ct.chest-abdomen-pelvis'].includes(exams[0]));
  exam = exams[0] === 'ct.trauma-panscan' ? 'ct.trauma-panscan' : 'ct.chest-abdomen-pelvis';
  const areaResponse = await fetch('report-areas.json');
  if (!areaResponse.ok) throw Error('Missing report-area index.');
  const areaBytes = await areaResponse.arrayBuffer();
  if (
    (await fingerprint(areaBytes)) !== '85dd872264ebf95e9aaae41aa1018ada97c635077661e33845a7c4a087848773'
  )
    throw Error('Report-area index differs.');
  areas = JSON.parse(new TextDecoder().decode(areaBytes))[exam];
  get('region').replaceChildren(
    new Option('All source classes', ''),
    ...areas.map((a) => new Option(a.name, a.id))
  );
  position = record.shape.map((n) => Math.floor(n / 2));
  get('selection').disabled = false;
  get('workspace').inert = false;
  const groups = query.getAll('row'),
    labels = query.getAll('label');
  const area = areas.find((a) => a.id === groups[0]);
  const requestedViews = query.getAll('representation');
  const view = requestedViews[0];
  const invalid =
    requestedViews.length > 1 ||
    (requestedViews.length && (!representationModes.has(view) || !byName.get(labels[0])?.voxelCount)) ||
    badExam ||
    groups.length > 1 ||
    labels.length > 1 ||
    (groups.length && !area) ||
    (labels.length && !areaLabels(area, record.labels).some((r) => r.sourceLabel === labels[0]));
  get('region').value = area?.id || '';
  get('setup').textContent = invalid
    ? 'This link does not identify a source structure in the requested report area. Choose a class.'
    : '';
  if (!invalid && view) {
    get('mode').value = representationModes.get(view);
    const preset = area?.id === 'bones' ? 'bone' : area?.id === 'lungs-and-airways' ? 'lung' : 'soft';
    get('window').value = preset;
    [get('low').value, get('high').value] = presets[preset];
  }
  setArea(area, invalid ? null : (labels[0] ?? (area ? undefined : 'liver')), true);
  if (exam === 'ct.chest-abdomen-pelvis') {
    try {
      const response = await fetch('report-guide.json');
      if (!response.ok) throw Error();
      const raw = await response.arrayBuffer();
      if ((await fingerprint(raw)) !== guideFingerprint) throw Error();
      reportGuide = JSON.parse(new TextDecoder().decode(raw));
      showGuide(currentArea());
      syncGuide(label);
    } catch {
      get('setup').textContent += ' The report structure guide could not be loaded.';
    }
  }
}
start().catch(() => {
  get('setup').textContent = 'The case inventory could not be verified. Reload to retry.';
});

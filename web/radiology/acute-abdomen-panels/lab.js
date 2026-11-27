const DATA_SHA = '560bb2d9263a50a83eae16729056f97453f4a3fe63c42ebb840500b9a52b29e0';
const get = id => document.getElementById(id);
const make = (tag, text) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; return node; };
let data, figures, targets, examples = [], shown = [], current, reportContext, generation = 0, whole = false;
const checkedImages = new Map();
const initial = new URLSearchParams(location.search);

async function sha(bytes) {
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(hash)].map(value => value.toString(16).padStart(2, '0')).join('');
}
function sourceName(example) {
  if (example.kind === 'model') return targets.get(example.target_id).label + ' · native CT and 3D';
  const figure = figures.get(example.figure_id);
  return 'Figure ' + figure.figure_number + ' · panel ' + example.source_panel + ' · ' + example.modality
    + ' · ' + figure.source_url.match(/PMC\d+/)?.[0];
}
function updateAddress() {
  const url = new URL(location.href);
  for (const key of ['target', 'panel', 'figure', 'report']) url.searchParams.delete(key);
  if (get('target').value) url.searchParams.set('target', get('target').value);
  if (current) url.searchParams.set('panel', current.id);
  if (reportContext) url.searchParams.set('report', reportContext.id);
  history.replaceState(null, '', url);
}
function drawView() {
  if (!current || current.kind === 'model') return;
  const figure = figures.get(current.figure_id), z = Number(get('zoom').value);
  const [x, y, w, h] = whole ? [0, 0, figure.width, figure.height] : current.panel_bounds;
  const box = [x + w * (1 - 1/z)/2, y + h * (1 - 1/z)/2, w/z, h/z];
  get('picture').setAttribute('viewBox', box.join(' '));
  ['x','y','width','height'].forEach((key, index) => get('panel-crop').setAttribute(key, box[index]));
  get('whole').textContent = whole ? 'Focus selected panel' : 'Show complete figure';
  get('whole').disabled = current.panel_bounds.join() === [0,0,figure.width,figure.height].join();
  get('zoom').setAttribute('aria-valuetext', z + ' times the panel view');
}
function inspectTarget(identifier, panel) {
  reportContext = null; get('report-context').hidden = true;
  get('target').value = identifier;
  get('modality').value = '';
  filter(panel);
}
function targetList() {
  const matched = get('matched'); matched.replaceChildren();
  const bindings = current.kind === 'model'
    ? [{target_id: current.target_id, basis: current.limits}]
    : current.bindings;
  for (const entry of bindings) {
    const target = targets.get(entry.target_id), item = make('li');
    const link = make('a', target.label); link.href = '?target=' + encodeURIComponent(target.id) + '&panel=' + encodeURIComponent(current.id);
    link.addEventListener('click', event => { event.preventDefault(); inspectTarget(target.id, current.id); });
    const details = make('details'); details.append(make('summary', 'Partial source correspondence'), make('p', entry.basis));
    item.append(link, details); matched.append(item);
  }
  if (!bindings.length) matched.append(make('li', 'Contextual source panel; no requirement coverage is recorded for this panel.'));
}
function links(entries) {
  get('links').replaceChildren();
  entries.forEach(([label, href], index) => {
    if (index) get('links').append(' · ');
    const link = make('a', label); link.href = href; link.target = '_blank'; link.rel = 'noopener noreferrer';
    get('links').append(link);
  });
}
async function verifyImage(figure) {
  if (!checkedImages.has(figure.id)) checkedImages.set(figure.id, (async () => {
    if (!/^\/app\/reference-media\/radiology-open\/[a-z0-9.-]+$/.test(figure.src)) throw Error('Source image URL differs');
    const response = await fetch(figure.src, {cache:'force-cache'});
    if (!response.ok || await sha(await response.arrayBuffer()) !== figure.sha256) throw Error('Source image fingerprint differs');
    const picture = new Image(); picture.src = figure.src; await picture.decode();
    if (picture.naturalWidth !== figure.width || picture.naturalHeight !== figure.height) throw Error('Source image dimensions differ');
  })());
  return checkedImages.get(figure.id);
}
async function select(identifier) {
  const token = ++generation;
  current = shown.find(example => example.id === identifier) || shown[0];
  get('image-view').hidden = true; get('native-view').hidden = true;
  get('empty').hidden = !!current;
  get('matched').replaceChildren();
  get('previous').disabled = !current || shown.indexOf(current) === 0;
  get('next').disabled = !current || shown.indexOf(current) === shown.length - 1;
  if (!current) {
    for (const id of ['selection','observation','caption','limits','credit','case-context','coverage']) get(id).textContent = '';
    get('links').replaceChildren(); get('status').textContent = 'No mapped source examples match these filters.'; updateAddress(); return;
  }
  get('panel').value = current.id;
  get('selection').textContent = (shown.indexOf(current)+1) + ' of ' + shown.length + ' · ' + sourceName(current);
  get('caption-section').hidden = current.kind === 'model';
  get('zoom').value = '1'; whole = false;
  targetList(); updateAddress();
  if (current.kind === 'model') {
    get('view-heading').textContent = 'Separate native vessel reference';
    get('observation').textContent = current.name;
    get('native-scope').textContent = current.limits;
    get('limits').textContent = current.limits;
    get('credit').textContent = current.attribution;
    get('coverage').textContent = 'Partial source-labelled lumen. Clinical, full branch-tree, vessel-wall and viability validation remain open.';
    get('case-context').textContent = 'ColonVessels case pat_012 is a separate source case. It is not registered to any of the published figure patients.';
    links([['Original dataset',current.source_url],[current.license,current.license_url]]);
    get('native-view').hidden = false; get('status').textContent = 'Native source reference selected. Open its reader to inspect the original CT and model.';
    const valid = /^\/app\/anatomy\/colonvessels-pat012\/(?:arterial|venous)\/index\.html\?segment=\d+:\d+$/.test(current.reader_url);
    get('open-native').hidden = !valid;
    if (valid) get('open-native').href = current.reader_url;
    return;
  }
  const figure = figures.get(current.figure_id);
  get('view-heading').textContent = 'Original Figure ' + figure.figure_number + ' · panel ' + current.source_panel;
  get('observation').textContent = current.observation;
  get('caption').textContent = figure.caption_full;
  get('limits').textContent = figure.limits;
  get('credit').textContent = figure.attribution;
  get('coverage').textContent = current.bindings.length
    ? 'Partial source correspondence only. A selected panel does not complete the named anatomy or examination.'
    : 'Context only. No requirement coverage is recorded for this panel.';
  get('case-context').textContent = figure.case_group === 'PMC12463306-published-case'
    ? 'The T2 MRI and MRCP come from the same published case. They are selected images, not a supplied registered native duct volume.'
    : 'Preserve this figure’s own source case and acquisition. Separate figures are not assumed to be the same patient or examination.';
  links([['Source article',figure.source_url],['Original figure',figure.figure_url],[figure.license,figure.license_url]]);
  get('status').textContent = 'Checking the original source image…';
  try {
    await verifyImage(figure);
    if (token !== generation) return;
    const original = get('original');
    original.setAttribute('href', figure.src); original.setAttribute('width', figure.width); original.setAttribute('height', figure.height);
    get('picture').setAttribute('aria-label', sourceName(current) + '. ' + current.observation);
    get('image-file').href = figure.src;
    drawView(); get('image-view').hidden = false;
    get('status').textContent = 'Original source image loaded · ' + current.modality + ' · ' + (current.bindings.length ? 'partial source correspondence' : 'context only') + '.';
  } catch {
    if (token === generation) get('status').textContent = 'The source image did not match its reviewed file or could not be loaded.';
  }
}
function filter(preferred) {
  const target = get('target').value, modality = get('modality').value;
  shown = examples.filter(example => (!target || (example.kind === 'model' ? example.target_id === target
    : example.bindings.some(binding => binding.target_id === target) || example.context_targets.includes(target)))
    && (!reportContext || reportContext.panels.includes(example.id))
    && (!modality || (example.kind === 'model' ? modality === 'native' : example.modality === modality)));
  get('panel').replaceChildren(...shown.map(example => new Option(sourceName(example), example.id)));
  select(preferred);
}
function move(step) { const at = shown.indexOf(current) + step; if (shown[at]) select(shown[at].id); }
async function load() {
  try {
    const response = await fetch('data.json'); if (!response.ok) throw Error('Source map unavailable');
    const bytes = await response.arrayBuffer(); if (await sha(bytes) !== DATA_SHA) throw Error('Source map fingerprint differs');
    data = JSON.parse(new TextDecoder().decode(bytes));
    if (data.schema_version !== 1 || data.clinical_approval !== false || data.requirement_completion_granted !== false
        || data.figures.length !== 12 || data.panels.length !== 17 || data.native_references.length !== 2) throw Error('Source scope differs');
    figures = new Map(data.figures.map(figure => [figure.id, figure]));
    targets = new Map(data.targets.map(target => [target.id,target]));
    examples = [...data.panels.map(panel => ({...panel,kind:'clinical_image'})), ...data.native_references];
    get('target').replaceChildren(new Option('All mapped source examples',''), ...data.targets.map(target => new Option(target.label,target.id)));
    get('scope-limits').replaceChildren(...data.limits.map(limit => make('li', limit)));
    get('denominator').textContent = data.targets.length + ' targets have selected partial examples. The inventory retains '
      + data.inventory_counts.parent_structures + ' parent structures and ' + data.inventory_counts.required_leaves
      + ' required leaves. No requirement is marked clinically complete by this reader.';
    get('choices').disabled = false;
    if (targets.has(initial.get('target'))) get('target').value = initial.get('target');
    else if (initial.get('target')) {
      get('target').append(new Option('Requested target has no mapped source','__unmapped__'));
      get('target').value = '__unmapped__';
    }
    reportContext = data.report_rows.find(row => row.id === initial.get('report'));
    if (reportContext) {
      get('target').value = reportContext.target_id;
      get('report-context').hidden = false;
      get('report-row').textContent = 'Report row: ' + reportContext.label + '. ' + reportContext.scope;
    }
    let preferred = initial.get('panel');
    const figure = figures.get(initial.get('figure'));
    if (!preferred && figure) preferred = data.panels.find(panel => panel.figure_id === figure.id && panel.source_panel === figure.default_panel)?.id;
    filter(preferred);
  } catch { get('status').textContent = 'The reviewed source map could not be verified or loaded.'; }
}
get('target').addEventListener('change', () => { reportContext = null; get('report-context').hidden = true; filter(); });
get('modality').addEventListener('change', () => filter());
get('panel').addEventListener('change', event => select(event.target.value));
get('all-targets').addEventListener('click', () => { reportContext = null; get('report-context').hidden = true; get('target').value = ''; get('modality').value = ''; filter(); });
get('previous').addEventListener('click', () => move(-1)); get('next').addEventListener('click', () => move(1));
get('whole').addEventListener('click', () => { whole = !whole; get('zoom').value = '1'; drawView(); });
get('reset').addEventListener('click', () => { whole = false; get('zoom').value = '1'; drawView(); });
get('zoom').addEventListener('input', drawView);
get('picture').addEventListener('keydown', event => {
  if (!['ArrowLeft','ArrowRight','+','=','-','Home'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') move(event.key === 'ArrowRight' ? 1 : -1);
  else if (event.key === 'Home') { whole = false; get('zoom').value = '1'; drawView(); }
  else { get('zoom').value = Math.max(1,Math.min(4,Number(get('zoom').value)+(event.key === '-' ? -.25 : .25))); drawView(); }
});
load();

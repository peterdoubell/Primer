const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');

class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.attributes = {}; this.dataset = {}; this.textContent = ''; this.hidden = false; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  getAttribute(key) { return this.attributes[key]; }
}
function descendants(node) { return [node, ...node.children.flatMap(descendants)]; }
function load() {
  const context = {window: {}, document: {createElement: tag => new Element(tag)}, navigator: {clipboard: {writeText: async text => { context.copied = text; }}}, console};
  global.window = context.window;
  global.document = context.document;
  Object.defineProperty(global, 'navigator', {value: context.navigator, configurable: true});
  delete require.cache[require.resolve('../web/radiology-structured.js')];
  require('../web/radiology-structured.js');
  return {...context.window.PrimerStructuredReporting, context};
}
const catalogue = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/radiology/descriptor-reporting.json'), 'utf8'));
const form = id => catalogue.forms[id];
const clone = value => JSON.parse(JSON.stringify(value));
function chosen(inv, row, fields) { return {findings: Object.fromEntries(Object.entries(fields).map(([key, value]) => [inv + ':' + row + ':' + key, value]))}; }
function prostate(dwi = '3', dce = 'negative', zone = 'peripheral zone') {
  return chosen('ra.mri-prostate', 'prostate-lesion', {
    lesion: {'slot-1': 'right', 'slot-2': 'mid gland', 'slot-3': 'anterior'},
    zone: {'slot-1': zone}, treatment: {'slot-1': 'treatment-naive prostate'},
    't2-adequate': {}, 'dwi-adequate': {}, 't2-score': {'slot-1': '3'},
    'dwi-score': {'slot-1': dwi}, dce: {'slot-1': dce},
  });
}
function thyroid(composition = 'solid or almost completely solid', foci = 'punctate echogenic foci only') {
  return chosen('ra.ultrasound-thyroid', 'thyroid-nodule', {
    nodule: {'slot-1': 'right upper pole'},
    composition: {'slot-1': composition}, echogenicity: {'slot-1': 'hypoechoic'},
    shape: {'slot-1': 'wider-than-tall'}, margin: {'slot-1': 'smooth'},
    'echogenic-foci': {'slot-1': foci}, dimensions: {'slot-1': 11, 'slot-2': 17, 'slot-3': 13},
  });
}
const prostateState = () => ({investigation_id: 'ra.mri-prostate', selections: {'anatomy-prostate-lesion': {instances: [prostate('3', 'positive'), prostate('2')]}}});
const thyroidState = () => ({investigation_id: 'ra.ultrasound-thyroid', selections: {
  'anatomy-patient-group': chosen('ra.ultrasound-thyroid', 'patient-group', {adult: {}}),
  'anatomy-thyroid-nodule': {instances: [thyroid('spongiform'), thyroid()]},
}});
function pythonJobs(schema, states) {
  // The constant Python program imports the pure resolver. Clinical data goes via
  // JSON stdin, never executable code; the interpreter is fixed, not environment-selected.
  // The shared browser module uses require.
  const result = spawnSync('python3', ['-c',
    'import json,sys; from primer.descriptor_calculations import descriptor_calculation_jobs; payload=json.load(sys.stdin); print(json.dumps([descriptor_calculation_jobs(payload["form"], state) for state in payload["states"]]))'], {
    cwd: path.join(__dirname, '..'), input: JSON.stringify({form: schema, states}), encoding: 'utf8', maxBuffer: 4 * 1024 * 1024,
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

test('real prostate records resolve independently with exact Python parity and stable identity', () => {
  const api = load(), schema = form('rad.5.prostate-mri'), state = prostateState(), before = clone(state);
  assert.equal(api.compose(schema, state).complete, true);
  const jobs = api.descriptorCalculationJobs(schema, state);
  assert.deepEqual(jobs, pythonJobs(schema, [state])[0]);
  assert.deepEqual(state, before);
  assert.deepEqual(jobs.map(j => j.inputs.dwi_score), [3, 2]);
  assert.deepEqual(jobs.map(j => j.binding_id), ['anatomy-prostate-lesion:1:pirads_v2_1', 'anatomy-prostate-lesion:2:pirads_v2_1']);
  assert.deepEqual(jobs.map(j => j.context_label), ['Lesion 1', 'Lesion 2']);
});

test('real thyroid mappings include all explicitly selected foci and only the current nodule dimensions', () => {
  const api = load(), schema = form('rad.5.thyroid-tirads'), state = thyroidState();
  state.selections['anatomy-thyroid-nodule'].instances[1] = thyroid('mixed cystic and solid', 'macrocalcification and peripheral rim calcification and punctate echogenic foci');
  state.selections['anatomy-thyroid-nodule'].instances[1].findings['ra.ultrasound-thyroid:thyroid-nodule:dimensions'] = {'slot-1': 21, 'slot-2': 8, 'slot-3': 9};
  const jobs = api.descriptorCalculationJobs(schema, state);
  assert.deepEqual(jobs, pythonJobs(schema, [state])[0]);
  assert.deepEqual(jobs.map(j => j.inputs.size_mm), [17, 21]);
  assert.deepEqual(jobs[1].inputs.echogenic_foci, ['macrocalcifications', 'peripheral_rim', 'punctate']);
  assert.deepEqual(jobs.map(j => j.inputs.adult_applicability_confirmed), [true, true]);
  assert.equal(api.compose(schema, state).text.includes('The patient is an adult.'), false);
});

test('missing observations stay missing, including global applicability and incomplete maximum dimensions', () => {
  const api = load(), schema = form('rad.5.thyroid-tirads'), state = thyroidState();
  delete state.selections['anatomy-patient-group'];
  const nodule = state.selections['anatomy-thyroid-nodule'].instances[1];
  delete nodule.findings['ra.ultrasound-thyroid:thyroid-nodule:dimensions']['slot-2'];
  delete nodule.findings['ra.ultrasound-thyroid:thyroid-nodule:echogenicity'];
  const jobs = api.descriptorCalculationJobs(schema, state);
  assert.deepEqual(jobs, pythonJobs(schema, [state])[0]);
  assert.equal('adult_applicability_confirmed' in jobs[0].inputs, false);
  assert.equal('size_mm' in jobs[1].inputs, false);
  assert.equal('echogenicity' in jobs[1].inputs, false);
  assert.equal(api.compose(schema, state).complete, false);
});

test('contradictory explicit quality cannot silently pick one score pathway', () => {
  const api = load(), schema = form('rad.5.prostate-mri'), state = prostateState();
  state.selections['anatomy-prostate-lesion'].instances[0].findings['ra.mri-prostate:prostate-lesion:t2-inadequate'] = {};
  const jobs = api.descriptorCalculationJobs(schema, state);
  assert.deepEqual(jobs, pythonJobs(schema, [state])[0]);
  assert.equal('t2_adequate' in jobs[0].inputs, false);
  assert.deepEqual(jobs[0].input_issues, [{code: 'conflicting_calculation_inputs', input: 't2_adequate'}]);
  assert.equal(api.compose(schema, state).complete, false);
});

test('explicit out-of-scope choices produce not-applicable jobs without an inferred category', () => {
  const api = load(), prostateSchema = form('rad.5.prostate-mri'), thyroidSchema = form('rad.5.thyroid-tirads');
  const central = {investigation_id: 'ra.mri-prostate', selections: {'anatomy-prostate-lesion': {instances: [prostate('3', 'positive', 'central zone')]}}};
  const child = thyroidState();
  child.selections['anatomy-patient-group'] = chosen('ra.ultrasound-thyroid', 'patient-group', {child: {}});
  const jobs = api.descriptorCalculationJobs(prostateSchema, central);
  assert.deepEqual(jobs, pythonJobs(prostateSchema, [central])[0]);
  assert.equal(jobs[0].not_applicable, true);
  assert.equal(jobs[0].inputs.zone, 'CZ');
  const childJobs = api.descriptorCalculationJobs(thyroidSchema, child);
  assert.deepEqual(childJobs, pythonJobs(thyroidSchema, [child])[0]);
  assert.equal(childJobs[0].not_applicable, true);
  assert.equal(childJobs[0].inputs.adult_applicability_confirmed, false);
  assert.equal('category' in childJobs[0], false);
});

test('volume units scale exactly and supplied PSA zero is retained without a default', () => {
  const api = load(), schema = form('rad.5.prostate-mri');
  const state = {investigation_id: 'ra.mri-prostate', selections: {'anatomy-prostate-dimensions': chosen('ra.mri-prostate', 'prostate-dimensions', {
    dimensions: {'slot-1': 40, 'slot-2': 30, 'slot-3': 50},
  })}};
  const without = api.descriptorCalculationJobs(schema, state);
  state.selections['anatomy-prostate-dimensions'].findings['ra.mri-prostate:prostate-dimensions:psa'] = {'slot-1': 0};
  const withZero = api.descriptorCalculationJobs(schema, state);
  assert.deepEqual(withZero, pythonJobs(schema, [state])[0]);
  assert.deepEqual(without[0].inputs, {transverse_cm: 4, ap_cm: 3, longitudinal_cm: 5});
  assert.deepEqual(withZero[0].inputs, {...without[0].inputs, psa_ng_ml: 0});
  assert.equal(withZero[0].binding_id, 'anatomy-prostate-dimensions:single:prostate_volume_psad');
});

test('unselected, cleared, unassessed and frozen unbound sections never create jobs', () => {
  const api = load(), schema = form('rad.5.prostate-mri');
  const states = [{investigation_id: 'ra.mri-prostate'}, {investigation_id: 'ra.mri-prostate', selections: {}},
    {investigation_id: 'ra.mri-prostate', selections: {'anatomy-prostate-lesion': {not_assessed: true}}}];
  assert.deepEqual(states.map(state => api.descriptorCalculationJobs(schema, state)), pythonJobs(schema, states));
  assert.ok(states.every(state => api.descriptorCalculationJobs(schema, state).length === 0));
  const unbound = clone(schema);
  for (const investigation of unbound.investigations) for (const section of investigation.sections) delete section.calculations;
  assert.deepEqual(api.descriptorCalculationJobs(unbound, prostateState()), []);
});

const tick = () => new Promise(resolve => setImmediate(resolve));
function find(root, text) {
  const node = descendants(root).find(item => item.tagName === 'BUTTON' && item.textContent === text);
  assert.ok(node, `Button ${text} exists`); return node;
}
function focusButton(root, key) {
  const node = descendants(root).find(item => item.tagName === 'BUTTON' && item.dataset.radFocus === key);
  assert.ok(node, `Choice ${key} exists`); return node;
}
function responseFor(inputs) {
  if ('zone' in inputs) {
    if (!('treatment_naive' in inputs)) return {status: 'incomplete', missing_inputs: ['treatment_naive'], version: '2.1 (2019)'};
    const category = inputs.dwi_score === 2 ? 'PI-RADS 2' : inputs.dce === 'positive' ? 'PI-RADS 4' : 'PI-RADS 3';
    return {status: 'complete', category, summary: category, version: '2.1 (2019)', sources: []};
  }
  if (!('adult_applicability_confirmed' in inputs)) return {status: 'incomplete', missing_inputs: ['adult_applicability_confirmed'], version: '2017'};
  const category = inputs.composition === 'spongiform' ? 'TR1' : 'TR5';
  return {status: 'complete', category, summary: category, version: '2017', sources: []};
}
function deferredService() {
  const calls = [];
  return {calls, request: (url, payload) => {
    assert.ok(!url.startsWith('/'), 'Calculator paths use the established relative adapter contract');
    assert.ok(payload && url.endsWith('/calculate'), 'Bound inputs do not request a parallel manual calculator form');
    return new Promise((resolve, reject) => calls.push({url, inputs: clone(payload.inputs), resolve, reject}));
  }};
}
function disposePending(root, service) {
  root.dispose();
  for (const call of service.calls) call.resolve(responseFor(call.inputs));
}

test('the one-page UI scores each record automatically and has no duplicated manual controls', async () => {
  const api = load(), service = deferredService();
  const root = api.render(form('rad.5.thyroid-tirads'), {initialState: {descriptor_state: thyroidState()}, request: service.request});
  try {
    assert.equal(find(root, 'Copy report').disabled, true);
    await tick(); assert.equal(service.calls.length, 2);
    assert.deepEqual(service.calls.map(c => c.inputs.composition), ['spongiform', 'solid_or_almost_solid']);
    service.calls.forEach(call => call.resolve(responseFor(call.inputs)));
    await root.flush();
    assert.equal(find(root, 'Copy report').disabled, false);
    assert.ok(root.getReport().includes('CALCULATED ASSESSMENT\nNodule 1: TR1 (2017)'));
    assert.ok(root.getReport().includes('CALCULATED ASSESSMENT\nNodule 2: TR5 (2017)'));
    assert.equal(descendants(root).some(node => node.className === 'rad-structured-calculator'), false);
    assert.deepEqual(root.getState().calculations, []);
    assert.equal(descendants(root).some(node => ['INPUT', 'TEXTAREA'].includes(node.tagName)), false);
  } finally { disposePending(root, service); }
});

test('changed selections remove the previous category immediately and late responses cannot restore it', async () => {
  const api = load(), service = deferredService(), state = prostateState();
  state.selections['anatomy-prostate-lesion'].instances.length = 1;
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: state}, request: service.request});
  try {
    await tick(); assert.equal(service.calls.length, 1);
    focusButton(root, 'slot:anatomy-prostate-lesion@0:ra.mri-prostate:prostate-lesion:dce:slot-1:negative').onclick();
    assert.equal(find(root, 'Copy report').disabled, true);
    assert.equal(root.getReport().includes('CALCULATED ASSESSMENT'), false);
    await tick(); assert.equal(service.calls.length, 2);
    service.calls[1].resolve(responseFor(service.calls[1].inputs)); await tick();
    assert.ok(root.getReport().includes('Lesion 1: PI-RADS 3'));
    service.calls[0].resolve(responseFor(service.calls[0].inputs)); await root.flush();
    assert.ok(root.getReport().includes('Lesion 1: PI-RADS 3'));
    assert.equal(root.getReport().includes('PI-RADS 4'), false);
  } finally { disposePending(root, service); }
});

test('removing a record recomputes the remaining identity without waiting for obsolete requests', async () => {
  const api = load(), service = deferredService();
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: prostateState()}, request: service.request});
  try {
    await tick(); assert.equal(service.calls.length, 2);
    find(root, 'Remove Lesion 1').onclick(); await tick();
    const current = service.calls.at(-1);
    assert.equal(current.inputs.dwi_score, 2);
    current.resolve(responseFor(current.inputs)); await tick();
    assert.ok(root.getReport().includes('Lesion 1: PI-RADS 2'));
    assert.equal(root.getReport().includes('Lesion 2:'), false);
    let flushed = false;
    const flushing = root.flush().then(() => {flushed = true;});
    await tick();
    assert.equal(flushed, true, 'The current report must not wait for removed or replaced jobs');
    service.calls.slice(0, 2).forEach(call => call.resolve(responseFor(call.inputs)));
    await flushing;
    assert.equal(root.getReport().includes('PI-RADS 4'), false);
  } finally { disposePending(root, service); }
});

test('clear removes all derived results and late network completions cannot revive them', async () => {
  const api = load(), service = deferredService();
  const root = api.render(form('rad.5.thyroid-tirads'), {initialState: {descriptor_state: thyroidState()}, request: service.request});
  try {
    await tick(); find(root, 'Clear').onclick();
    assert.equal(root.getReport(), '');
    assert.deepEqual(root.getState().descriptor_state.selections, {});
    service.calls.forEach(call => call.resolve(responseFor(call.inputs)));
    await root.flush();
    assert.equal(root.getReport(), '');
    assert.equal(find(root, 'Copy report').disabled, true);
  } finally { disposePending(root, service); }
});

test('non-applicable records permit descriptive copy without calling a scoring algorithm', async () => {
  const api = load(), state = prostateState(), calls = [];
  state.selections['anatomy-prostate-lesion'].instances = [prostate('3', 'positive', 'central zone')];
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: state}, request: async (...args) => {calls.push(args); return {};}});
  try {
    await root.flush();
    assert.equal(calls.length, 0);
    assert.equal(find(root, 'Copy report').disabled, false);
    assert.equal(root.getReport().includes('CALCULATED ASSESSMENT'), false);
    assert.ok(descendants(root).some(node => String(node.textContent).includes('no category is assigned')));
  } finally { root.dispose(); }
});

test('a failed bound request blocks copy, exposes retry and recovers without duplicate manual inputs', async () => {
  const api = load(), service = deferredService(), state = prostateState();
  state.selections['anatomy-prostate-lesion'].instances.length = 1;
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: state}, request: service.request});
  try {
    await tick(); service.calls[0].reject(Error('Temporary calculation outage')); await root.flush();
    assert.equal(find(root, 'Copy report').disabled, true);
    assert.ok(descendants(root).some(node => String(node.textContent).includes('Temporary calculation outage')));
    find(root, 'Retry calculation').onclick(); await tick();
    assert.equal(service.calls.length, 2);
    service.calls[1].resolve(responseFor(service.calls[1].inputs)); await root.flush();
    assert.equal(find(root, 'Copy report').disabled, false);
    assert.ok(root.getReport().includes('Lesion 1: PI-RADS 4'));
    assert.deepEqual(root.getState().calculations, []);
  } finally { disposePending(root, service); }
});

test('structurally incomplete records do not call the scoring algorithm before required descriptors are complete', async () => {
  const api = load(), state = prostateState(), calls = [];
  state.selections['anatomy-prostate-lesion'].instances.length = 1;
  delete state.selections['anatomy-prostate-lesion'].instances[0].findings['ra.mri-prostate:prostate-lesion:lesion']['slot-2'];
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: state}, request: async (...args) => {calls.push(args); return responseFor(args[1].inputs);}});
  try {
    await root.flush();
    assert.equal(find(root, 'Copy report').disabled, true);
    assert.equal(calls.length, 0);
    assert.equal(root.getReport().includes('CALCULATED ASSESSMENT'), false);
  } finally { root.dispose(); }
});

test('a saved standalone input must be explicitly cleared before the bound report can be copied', async () => {
  const api = load(), state = prostateState();
  state.selections['anatomy-prostate-lesion'].instances.length = 1;
  const manual = {treatment_naive: true, zone: 'PZ', t2_adequate: true, t2_score: 3, dwi_adequate: true, dwi_score: 2, dce: 'negative'};
  const request = async (url, payload) => payload ? responseFor(payload.inputs) : {title: 'PI-RADS', version: '2.1 (2019)', input_schema: {properties: {}}, sources: []};
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: state, calculations: [{calculator_id: 'pirads_v2_1', inputs: manual}]}, request});
  try {
    await root.flush();
    assert.equal(find(root, 'Copy report').disabled, true);
    assert.ok(root.getReportResult().missing.some(item => item.label.startsWith('Clear the separate')));
    assert.equal(root.getState().calculations.length, 1);
    find(root, 'Clear calculation').onclick(); await root.flush();
    assert.deepEqual(root.getState().calculations, []);
    assert.equal(find(root, 'Copy report').disabled, false);
    assert.equal(root.getReport().includes('PI-RADS 2'), false);
    assert.ok(root.getReport().includes('Lesion 1: PI-RADS 4'));
  } finally { root.dispose(); }
});

test('unscoped linked context cannot overwrite every repeated lesion or diverge from saved inputs', async () => {
  const api = load(), state = prostateState(), calls = [];
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: state},
    contextValues: {'ra.mri-prostate:prostate-lesion:dwi-score.slot-1': '5'},
    request: async (url, payload) => {calls.push(payload.inputs); return responseFor(payload.inputs);}});
  try {
    await root.flush();
    assert.deepEqual(calls.map(input => input.dwi_score), [3, 2]);
    const report = root.getReport();
    assert.ok(report.includes('DWI sequence score is 3.'));
    assert.ok(report.includes('DWI sequence score is 2.'));
    assert.equal(report.includes('DWI sequence score is 5.'), false);
    assert.equal(root.getState().descriptor_state.selections['anatomy-prostate-lesion'].instances[0].findings['ra.mri-prostate:prostate-lesion:dwi-score']['slot-1'], '3');
  } finally { root.dispose(); }
});

test('explicit no-nodule normal reports absence without launching a score or inferring patient applicability', async () => {
  const api = load(), calls = [];
  const root = api.render(form('rad.5.thyroid-tirads'), {request: async (...args) => {calls.push(args); return {};}});
  try {
    assert.equal(root.getReport(), '');
    find(root, 'Use normal findings').onclick();
    await root.flush();
    assert.ok(root.getReport().includes('No thyroid nodules are identified.'));
    assert.equal(find(root, 'Copy report').disabled, false);
    assert.deepEqual(calls, []);
    assert.equal('anatomy-patient-group' in root.getState().descriptor_state.selections, false);
  } finally { root.dispose(); }
});

test('current thyroid location choices enumerate only anatomically valid lobe and isthmus sites', () => {
  const schema = form('rad.5.thyroid-tirads');
  const exam = schema.investigations.find(item => item.id === 'ra.ultrasound-thyroid');
  const row = exam.sections.find(item => item.anatomy_id === 'thyroid-nodule');
  const location = row.findings.find(item => item.id.endsWith(':nodule'));
  assert.equal(location.slots.length, 1);
  assert.deepEqual(location.slots[0].options.map(item => item.value), [
    'right upper pole', 'right mid portion', 'right lower pole', 'left upper pole', 'left mid portion',
    'left lower pole', 'isthmus centrally', 'isthmus-right lobe junction', 'isthmus-left lobe junction',
  ]);
});

test('explicit negative focal prostate assessment is mutually exclusive with lesions and does not infer PI-RADS', async () => {
  const api = load(), calls = [];
  const state = {investigation_id: 'ra.mri-prostate', selections: {'anatomy-prostate-lesion': {normal: true}}};
  const root = api.render(form('rad.5.prostate-mri'), {initialState: {descriptor_state: state}, request: async (...args) => {calls.push(args); return {};}});
  try {
    await root.flush();
    assert.ok(root.getReport().includes('No suspicious focal prostatic lesion is identified on the acquired MRI sequences.'));
    assert.equal(find(root, 'Copy report').disabled, false);
    assert.equal(root.getReport().includes('PI-RADS'), false);
    assert.deepEqual(calls, []);
    const conflicting = clone(state);
    conflicting.selections['anatomy-prostate-lesion'].instances = [prostate()];
    assert.equal(api.compose(form('rad.5.prostate-mri'), conflicting).complete, false);
  } finally { root.dispose(); }
});

test('new O-RADS records have Python parity, independent inputs and direct bound requests', async () => {
  const schema=form('rad.5.ovarian-orads'),iid='us.adnexal-orads';
  const record=(location,morphology)=>chosen(iid,'adnexal-lesion',{lesion:{'slot-1':location},[morphology]:{},size:{'slot-1':50},...(morphology==='solid'?{contour:{'slot-1':'irregular'}}:{})});
  const state={investigation_id:iid,selections:{
    'anatomy-applicability':chosen(iid,'applicability',{assessment:{'slot-1':'adnexal lesion appropriate for O-RADS assessment'}}),
    'anatomy-quality':chosen(iid,'quality',{assessment:{'slot-1':'adequate for risk stratification'}}),
    'anatomy-extraovarian':chosen(iid,'extraovarian',{assessment:{'slot-1':'no suspicious extraovarian findings'}}),
    'anatomy-adnexal-lesion':{instances:[record('right ovary','simple'),record('left ovary','solid')]}
  }};
  const api=load(),jobs=api.descriptorCalculationJobs(schema,state);
  assert.deepEqual(jobs,pythonJobs(schema,[state])[0]);
  assert.deepEqual(jobs.map(job=>job.inputs.morphology),['simple_cyst','solid']);
  const calls=[];
  const root=api.render(schema,{investigationId:iid,initialState:state,request:async(path,{inputs})=>{
    calls.push({path,inputs});assert.equal(path,'calculators/orads_us_2022/calculate');
    const score=inputs.morphology==='solid'?5:2;return {status:'complete',calculator_id:'orads_us_2022',version:'2022',category:'O-RADS US '+score,summary:'O-RADS US '+score};
  }});
  await root.flush();
  assert.equal(calls.length,2);assert.match(root.getReport(),/Lesion 1: O-RADS US 2/);assert.match(root.getReport(),/Lesion 2: O-RADS US 5/);
  assert.equal(descendants(root).filter(node=>['INPUT','TEXTAREA'].includes(node.tagName)).length,0);
  assert.equal(root.getReportResult().complete,true);
});

test('an unselected examination does not display empty calculators bound elsewhere in its guide', async () => {
  const api=load(),calls=[],schema=form('rad.5.ovarian-orads');
  const root=api.render(schema,{investigationId:'ra.ovarian-cysts',request:async path=>{calls.push(path);throw Error('Should not request an empty unrelated calculator');}});
  await root.flush();assert.deepEqual(calls,[]);assert.equal(root.getReport(),'');
});

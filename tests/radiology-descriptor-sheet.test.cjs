const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');

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
  vm.runInNewContext(fs.readFileSync('web/radiology-structured.js', 'utf8'), context);
  return {...context.window.PrimerStructuredReporting, context};
}
function find(root, text) {
  const node = descendants(root).find(node => node.tagName === 'BUTTON' && node.textContent === text);
  assert.ok(node, `Button ${text} exists`); return node;
}
function select(root, label, value) {
  const node = descendants(root).find(node => node.tagName === 'SELECT' && node.getAttribute('aria-label') === label);
  assert.ok(node, `Selector ${label} exists`); node.value = String(value); node.onchange();
}
const plain = (id, text) => ({id, label: text, text, segments: [{text}], slots: []});
const form = {
  guide_id: 'shoulder', schema_hash: 'frozen-schema', calculator_ids: [],
  investigations: [{id: 'mri', title: 'MRI shoulder', sections: [
    {id: 'cuff', label: 'Rotator cuff', report_section_id: 'findings', report_section_label: 'FINDINGS', normal: plain('cuff-normal', 'Rotator cuff intact.'), findings: [
      {id: 'tear', label: 'Partial-thickness tear', segments: [{text: 'Partial-thickness '}, {slot: 'surface'}, {text: ' tear.'}], slots: [{id: 'surface', kind: 'choice', label: 'Surface', required: true, options: [{value: 'articular-sided', label: 'Articular'}, {value: 'bursal-sided', label: 'Bursal'}]}]},
      {id: 'size', label: 'Tear width', segments: [{text: 'Tear measures '}, {slot: 'width'}, {text: ' mm.'}], slots: [{id: 'width', kind: 'number', label: 'Width', minimum: 0, unit: 'mm', required: true}]},
      {id: 'context', label: 'Associated finding', segments: [{slot: 'detail'}, {text: '.'}], slots: [{id: 'detail', kind: 'context', label: 'Associated finding', context_key: 'linked-detail', required: true}]}
    ]},
    {id: 'biceps', label: 'Biceps', report_section_id: 'findings', report_section_label: 'FINDINGS', normal: plain('biceps-normal', 'Biceps intact.'), findings: []}
  ]}]
};

test('the sheet has no typing controls or inferred normal findings', () => {
  const api = load(), root = api.render(form);
  assert.equal(root.getReport(), '');
  assert.equal(find(root, 'Copy report').disabled, true);
  assert.equal(descendants(root).filter(node => ['INPUT', 'TEXTAREA'].includes(node.tagName)).length, 0);
  assert.equal(root.getState().descriptor_version, 'frozen-schema');
  find(root, 'Use normal findings').onclick();
  assert.equal(root.getReport(), 'FINDINGS\nRotator cuff intact.\nBiceps intact.');
  assert.equal(find(root, 'Copy report').disabled, false);
});

test('abnormal findings replace normal and show only their required follow-up choices', () => {
  const api = load(), root = api.render(form);
  find(root, 'Use normal findings').onclick(); find(root, 'Partial-thickness tear').onclick();
  assert.equal(root.getState().descriptor_state.selections.cuff.normal, false);
  assert.equal(find(root, 'Copy report').disabled, true);
  find(root, 'Articular').onclick();
  assert.equal(root.getReport(), 'FINDINGS\nPartial-thickness articular-sided tear.\nBiceps intact.');
  assert.equal(find(root, 'Copy report').disabled, false);
  find(root, 'Partial-thickness tear').onclick();
  assert.equal(descendants(root).some(node => node.textContent === 'Articular'), false);
  assert.equal(root.getReport(), 'FINDINGS\nBiceps intact.');
});

test('numbers have blank defaults, accept explicit zero and exact values without typing', () => {
  const api = load(), root = api.render(form);
  find(root, 'Tear width').onclick();
  assert.equal(root.getReportResult().complete, false);
  select(root, 'Width', 0);
  assert.equal(root.getReport(), 'FINDINGS\nTear measures 0 mm.');
  select(root, 'Width', 'exact');
  select(root, 'Width whole digit 1', 7);
  find(root, '+ decimal digit').onclick();
  assert.equal(root.getReportResult().complete, false);
  select(root, 'Width decimal digit 1', 3);
  assert.equal(root.getReport(), 'FINDINGS\nTear measures 7.3 mm.');
  assert.equal(descendants(root).filter(node => ['INPUT', 'TEXTAREA'].includes(node.tagName)).length, 0);
});

test('linked context is materialized into the canonical state and unresolved prose cannot be copied', async () => {
  const api = load(), root = api.render(form);
  find(root, 'Associated finding').onclick();
  assert.equal(root.getReportResult().complete, false);
  root.updateContext({'linked-detail': 'Associated effusion'});
  assert.equal(root.getReport(), 'FINDINGS\nAssociated effusion.');
  assert.equal(root.getState().descriptor_state.selections.cuff.findings.context.detail, 'Associated effusion');
  await find(root, 'Copy report').onclick();
  assert.equal(api.context.copied, 'FINDINGS\nAssociated effusion.');
  root.updateContext({'linked-detail': '[unresolved]'});
  assert.equal(root.getReportResult().complete, false);
});

test('pinned investigations cannot be switched and context does not leak to another modality', () => {
  const api = load(), two = {...form, investigations: [...form.investigations, {id: 'us', title: 'Ultrasound shoulder', sections: [{id: 'us-cuff', label: 'Cuff', normal: plain('us-normal', 'Cuff intact on ultrasound.'), findings: []}]}]};
  const root = api.render(two);
  assert.equal(root.getState().investigation_id, '');
  find(root, 'MRI shoulder').onclick(); find(root, 'Use normal findings').onclick();
  find(root, 'Ultrasound shoulder').onclick();
  assert.equal(root.getReport(), '');
  assert.equal(Object.keys(root.getState().selections).length, 0);
  const pinned = api.render(two, {investigationId: 'us'});
  assert.equal(descendants(pinned).some(node => node.tagName === 'BUTTON' && node.textContent === 'MRI shoulder'), false);
});

test('canonical snapshots hydrate and custom copy persists before touching the clipboard', async () => {
  const api = load(); let copied;
  const root = api.render(form, {initialState: {descriptor_state: {investigation_id: 'mri', selections: {cuff: {normal: true}}}, calculations: []}, onCopy: async (snapshot, text) => { copied = {snapshot, text}; }});
  await find(root, 'Copy report').onclick();
  assert.equal(copied.text, 'FINDINGS\nRotator cuff intact.');
  assert.equal(copied.snapshot.descriptor_state.selections.cuff.normal, true);
  assert.equal(api.context.copied, undefined);
});

const calculatorConfig = {title: 'ACR TI-RADS', version: '2017', sources: [], input_schema: {properties: {
  adult_applicability_confirmed: {type: 'boolean'},
  composition: {enum: ['spongiform', 'solid_or_almost_solid']},
  echogenicity: {enum: ['hypoechoic', 'very_hypoechoic']},
  shape: {enum: ['wider_than_tall', 'taller_than_wide']},
  margin: {enum: ['smooth', 'lobulated_or_irregular']},
  echogenic_foci: {type: 'array', items: {enum: ['none', 'punctate']}}
}}};

test('automatic calculations need explicit inputs, block partial copy and remove stale results immediately', async () => {
  const api = load(); const requests = [], resolver = [];
  const send = async (path, payload) => {
    if (!payload) return calculatorConfig;
    requests.push(payload.inputs);
    if (payload.inputs.composition === 'spongiform' && payload.inputs.adult_applicability_confirmed) return {status: 'complete', summary: 'ACR TI-RADS TR1: 0 points.', version: '2017'};
    if (payload.inputs.composition === 'solid_or_almost_solid') return new Promise(resolve => resolver.push(resolve));
    return {status: 'incomplete'};
  };
  const root = api.render({...form, calculator_ids: ['acr_tirads_2017']}, {request: send}); await root.flush();
  assert.equal(root.getState().calculations.length, 0);
  assert.equal(root.getReport(), '');
  find(root, 'Yes').onclick(); await root.flush();
  assert.equal(root.getReportResult().complete, false);
  find(root, 'Spongiform').onclick(); await root.flush();
  assert.match(root.getReport(), /TR1: 0 points/);
  assert.equal(root.getReportResult().complete, true);
  assert.equal(descendants(root).some(node => node.textContent === 'Hypoechoic'), false);
  find(root, 'Solid or almost solid').onclick();
  assert.doesNotMatch(root.getReport(), /TR1/);
  assert.equal(root.getReportResult().complete, false);
  find(root, 'Clear calculation').onclick();
  resolver[0]({status: 'complete', summary: 'STALE result', version: '2017'});
  await root.flush();
  assert.doesNotMatch(root.getReport(), /STALE/);
  assert.equal(root.getState().calculations.length, 0);
});

test('changing calculator context invalidates in-flight results from the old context', async () => {
  const api = load(); let resolveOld;
  const send = async (path, payload) => {
    if (!payload) return calculatorConfig;
    if (payload.inputs.composition === 'spongiform') return new Promise(resolve => { resolveOld = resolve; });
    return {status: 'incomplete'};
  };
  const root = api.render({...form, calculator_ids: ['acr_tirads_2017']}, {request: send}); await root.flush();
  find(root, 'Spongiform').onclick(); root.updateContext({});
  resolveOld({status: 'complete', summary: 'OLD PATIENT', version: '2017'});
  // The current sheet retained selections, so clear them explicitly before flushing.
  find(root, 'Clear calculation').onclick();
  await root.flush();
  assert.doesNotMatch(root.getReport(), /OLD PATIENT/);
});

test('a multi-digit exact measurement stays open until 12.5 is fully selected', () => {
  const api = load(), root = api.render(form);
  find(root, 'Tear width').onclick(); select(root, 'Width', 'exact');
  select(root, 'Width whole digit 1', 2); find(root, '+ whole digit').onclick();
  assert.equal(root.getReportResult().complete, false);
  select(root, 'Width whole digit 1', 1); find(root, '+ decimal digit').onclick();
  select(root, 'Width decimal digit 1', 5);
  assert.equal(root.getReport(), 'FINDINGS\nTear measures 12.5 mm.');
  const exact = descendants(root).find(node => node.className === 'rad-number-exact');
  assert.equal(exact.hidden, false);
});

test('native selected investigation is honoured and conflicting hydrated selections block copy', () => {
  const api = load();
  const root = api.render({...form, selected_investigation_id: 'mri'}, {initialState: {descriptor_state: {selections: {cuff: {normal: true, findings: {tear: {surface: 'articular-sided'}}}}}}});
  assert.equal(root.getState().investigation_id, 'mri');
  assert.equal(root.getReportResult().complete, false);
  assert.equal(find(root, 'Copy report').disabled, true);
});

test('clearing the last echogenic-foci chip returns to unreviewed, not an implicit none', async () => {
  const api = load();
  const send = async (path, payload) => payload ? {status: 'incomplete'} : calculatorConfig;
  const root = api.render({...form, calculator_ids: ['acr_tirads_2017']}, {request: send}); await root.flush();
  find(root, 'Punctate').onclick(); await root.flush();
  assert.equal(root.getState().calculator_inputs.acr_tirads_2017.echogenic_foci[0], 'punctate');
  find(root, 'Punctate').onclick(); await root.flush();
  assert.equal(root.getState().calculator_inputs.acr_tirads_2017.echogenic_foci, undefined);
});

test('the actual MRI shoulder source produces a complete selectable partial-tear report', async () => {
  const api = load(), source = JSON.parse(fs.readFileSync('data/radiology/descriptor-reporting.json', 'utf8')).forms['rad.5.shoulder'];
  const root = api.render(source, {investigationId: 'ra.mri-shoulder'});
  const finding = source.investigations.find(item => item.id === 'ra.mri-shoulder').sections.flatMap(section => section.findings).find(item => item.text.startsWith('Partial-thickness'));
  find(root, finding.label).onclick(); find(root, 'articular-sided').onclick(); find(root, 'Supraspinatus').onclick();
  const measurements = finding.slots.filter(slot => slot.kind === 'number');
  select(root, measurements[0].label, 40); select(root, measurements[1].label, 12);
  assert.match(root.getReport(), /Partial-thickness articular-sided supraspinatus tear involving approximately 40% of tendon thickness, 12 mm long\./);
  assert.equal(root.getReportResult().complete, true);
  assert.equal(descendants(root).filter(node => ['INPUT', 'TEXTAREA'].includes(node.tagName)).length, 0);
  await find(root, 'Copy report').onclick();
  assert.equal(api.context.copied, root.getReport());
  assert.equal(Object.keys(root.getState().descriptor_state.selections).length, 1);
});

test('snapshot uses the API catalogue version before the form digest and calculated text matches canonical output', async () => {
  const api = load();
  const source = {...form, version: 'catalogue-version', schema_hash: 'per-form-digest'};
  const root = api.render({descriptor_form: source, descriptor_version: 'api-catalogue-version', calculator_ids: ['acr_tirads_2017']}, {
    initialState: {descriptor_state: {investigation_id: 'mri', selections: {}}, calculations: [{calculator_id: 'acr_tirads_2017', inputs: {adult_applicability_confirmed: true, composition: 'spongiform'}}]},
    request: async (path, payload) => payload ? {status: 'complete', summary: 'ACR TI-RADS TR1: 0 points.', version: '2017'} : calculatorConfig
  });
  await root.flush();
  assert.equal(root.getState().descriptor_version, 'api-catalogue-version');
  assert.equal(root.getReport(), 'CALCULATED ASSESSMENT\nACR TI-RADS TR1: 0 points. (2017)');
  assert.equal(api.render(source).getState().descriptor_version, 'catalogue-version');
});

test('unknown hydrated sections, findings or slots prevent copying instead of silently disappearing', () => {
  const api = load();
  for (const selections of [
    {cuff: {normal: true}, unsupported: {normal: true}},
    {cuff: {findings: {unsupported: {}}}},
    {cuff: {findings: {tear: {surface: 'articular-sided', unsupported: 'value'}}}},
    {cuff: {normal: true, unsupported: 'value'}}
  ]) {
    const root = api.render(form, {initialState: {descriptor_state: {investigation_id: 'mri', selections}}});
    assert.equal(root.getReportResult().complete, false);
    assert.equal(find(root, 'Copy report').disabled, true);
  }
});

test('exact numeric selectors preserve signed measurements when the source sets no lower bound', () => {
  const api = load(), source = JSON.parse(JSON.stringify(form));
  const number = source.investigations[0].sections[0].findings.find(finding => finding.id === 'size').slots[0];
  delete number.minimum; number.label = 'Attenuation'; number.unit = 'HU';
  const root = api.render(source); find(root, 'Tear width').onclick(); select(root, 'Attenuation', 'exact');
  select(root, 'Attenuation whole digit 1', 5); find(root, '+ whole digit').onclick();
  select(root, 'Attenuation whole digit 1', 3); select(root, 'Attenuation sign', true);
  assert.equal(root.getState().descriptor_state.selections.cuff.findings.size.width, -35);
  assert.equal(root.getReportResult().complete, true);
});

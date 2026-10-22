const assert = require('node:assert/strict');
const test = require('node:test');

function element(tag) {
  return {tag, nodeType: 1, className: '', attrs: {}, dataset: {}, children: [],
    append(...values) { this.children.push(...values.filter(value => value != null)); },
    setAttribute(key, value) { this.attrs[key] = value; },
    addEventListener() {},
    querySelectorAll() { return []; },
  };
}
function descendants(node) {
  if (!node || typeof node !== 'object') return [];
  return [node, ...(node.children || []).flatMap(descendants)];
}
global.window = {addEventListener() {}};
global.document = {
  createElement: element,
  createTextNode: text => ({nodeType: 3, textContent: String(text)}),
  addEventListener() {},
};
global.location = {href: 'https://primer.example/app/'};
const {renderRadiologyReference} = require('../web/app.js');

function render({withForm = true, withComponent = true} = {}) {
  const marker = element('section');
  marker.className = 'structured-form-fixture';
  const form = {guide_id: 'rad.5.prostate-mri'};
  window.PrimerStructuredReporting = withComponent ? {render(value) {
    assert.equal(value, form);
    return marker;
  }} : undefined;
  const node = {id: form.guide_id, radiology_reference: {
    report_templates: [{title: 'Legacy report'}], ...(withForm ? {structured_form: form} : {}),
  }};
  const section = renderRadiologyReference(node);
  return {section, marker};
}

test('the structured form survives reporting-desk template-container extraction', () => {
  const {section, marker} = render();
  const container = descendants(section).find(node => node.className === 'rad-report-templates');
  assert.ok(container, 'the reporting desk extracts this container for its Report template tab');
  assert.ok(descendants(container).includes(marker), 'structured controls must be inside that extracted subtree');
  assert.equal(descendants(section).filter(node => node === marker).length, 1);
  assert.ok(descendants(container).some(node => node.className === 'rad-template'));
});

test('legacy templates remain usable without a form or its optional script', () => {
  for (const config of [{withForm: false}, {withComponent: false}]) {
    const {section, marker} = render(config);
    assert.ok(!descendants(section).includes(marker));
    assert.ok(descendants(section).some(node => node.className === 'rad-template'));
  }
});

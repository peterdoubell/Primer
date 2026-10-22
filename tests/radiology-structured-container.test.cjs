const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const app = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8');
const start = app.indexOf('function renderRadiologyReference(n) {');
const end = app.indexOf('/* Reporting desk:', start);
assert.ok(start >= 0 && end > start);
const renderer = app.slice(start, end);

function element(tag, attrs = {}, ...children) {
  return {tag, attrs, children: children.filter(child => child != null),
    append(...values) { this.children.push(...values.filter(value => value != null)); }};
}
function descendants(node) {
  if (!node || typeof node !== 'object') return [];
  return [node, ...node.children.flatMap(descendants)];
}
function render({withForm = true, withComponent = true} = {}) {
  const marker = element('section', {class: 'structured-form-fixture'});
  const form = {guide_id: 'rad.5.prostate-mri'};
  const context = {
    el: element,
    radiologySourceLink: () => element('a'),
    renderRadiologyTemplate: () => element('article', {class: 'legacy-template-fixture'}),
    attachPictureHandlers: () => {},
    window: withComponent ? {PrimerStructuredReporting: {render(value) {
      assert.equal(value, form);
      return marker;
    }}} : {},
    node: {id: form.guide_id, radiology_reference: {
      report_templates: [{}], ...(withForm ? {structured_form: form} : {}),
    }},
  };
  const section = vm.runInNewContext(renderer + '\nrenderRadiologyReference(node);', context);
  return {section, marker};
}

test('the structured form survives reporting-desk template-container extraction', () => {
  const {section, marker} = render();
  const container = descendants(section).find(node => node.attrs.class === 'rad-report-templates');
  assert.ok(container, 'the reporting desk extracts this container for its Report template tab');
  assert.ok(descendants(container).includes(marker), 'structured controls must be inside that extracted subtree');
  assert.equal(descendants(section).filter(node => node === marker).length, 1);
  assert.ok(descendants(container).some(node => node.attrs.class === 'legacy-template-fixture'));
});

test('legacy templates remain usable without a form or its optional script', () => {
  for (const config of [{withForm: false}, {withComponent: false}]) {
    const {section, marker} = render(config);
    assert.ok(!descendants(section).includes(marker));
    assert.ok(descendants(section).some(node => node.attrs.class === 'legacy-template-fixture'));
  }
});

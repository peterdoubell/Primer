'use strict';
const assert = require('node:assert/strict');
global.window = { addEventListener() {} };
global.document = { addEventListener() {} };
const { histologyFigure, radiologyPresentation } = require('../web/app.js');
assert.equal(histologyFigure({ src: '/mri.png', modality: 'MRI', caption: 'Histology confirmed the tumour.' }), false);
assert.equal(histologyFigure({ src: '/tissue.png', modality: 'Histology' }), true);
assert.equal(histologyFigure({ src: '/mixed.png', modality: 'CT', source_context: { panel_types: { a: 'CT', b: 'Histology' } } }), true);
const modules = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
let removed = 0;
function images(value, output = []) {
  if (!value || typeof value !== 'object') return output;
  if (value.src) output.push(value);
  Object.values(value).forEach(child => images(child, output));
  return output;
}
for (const module of modules) {
  const before = images(module.radiology_reference);
  const expected = before.filter(histologyFigure).length;
  const retainedMRI = before.filter(image => image.modality === 'MRI' && !histologyFigure(image)).map(image => image.src);
  radiologyPresentation(module);
  const after = images(module.radiology_reference);
  assert.equal(after.filter(histologyFigure).length, 0, module.id);
  for (const src of retainedMRI) assert.ok(after.some(image => image.src === src), module.id + ': MRI removed');
  const ref = module.radiology_reference;
  const available = new Set([...ref.key_images, ...ref.structure_atlas].map(image => image.id));
  for (const step of [ref.walkthrough.start, ...ref.walkthrough.steps]) {
    assert.ok(step.images.every(id => available.has(id)), module.id + ': missing walkthrough image');
  }
  removed += expected;
}
assert.ok(removed > 0, 'Catalogue should exercise real histology exclusions');
console.log(JSON.stringify({ modules: modules.length, histologyFiguresRemoved: removed, status: 'passed' }));

#!/usr/bin/env node
'use strict';
// Check the step-by-step reporting helpers and every investigation's 3D steps
// without a DOM. The argument is a JSON list of served spatial models and step
// landmarks, written from the catalogue by tests/test_radiology_walkthrough.py.
// Browser verification remains necessary for layout, focus and the mesh viewer.
const assert = require('node:assert/strict');
const fs = require('node:fs');
// Fixed shipped modules with inert event registration; no real reader or route.
globalThis.window = { addEventListener() {} };
globalThis.document = { addEventListener() {} };
require('../web/spatial-models.js');
require('../web/radiology-reference-models.js');
const { walkthroughPrompts, walkthroughFirstPrompt, walkthroughInsert, walkthroughReport } = require('../web/app.js');
const api = window.PrimerSpatial, wrapper = window.PrimerRadiologyReferenceModels;

// Blanks are the reader's to fill: underscores and bracketed prompts.
assert.equal(walkthroughPrompts('Tear __ mm at [level]; retraction ___.'), 3);
assert.equal(walkthroughPrompts('No rotator cuff tear.'), 0);
assert.equal(walkthroughPrompts(null), 0);
assert.deepEqual(walkthroughFirstPrompt('Size __ mm [site]'), [5, 7]);
assert.deepEqual(walkthroughFirstPrompt('Size __ mm [site]', 7), [11, 17]);
assert.equal(walkthroughFirstPrompt('Nothing to fill.'), null);
assert.equal(walkthroughFirstPrompt('A [prompt\nacross lines]'), null, 'A prompt never spans lines');

// A phrase replaces an untouched prompt or normal statement, never a written finding.
assert.deepEqual(walkthroughInsert('', 'Full-thickness tear __ mm.'), { text: 'Full-thickness tear __ mm.', start: 0 });
assert.deepEqual(walkthroughInsert('  \n', 'Effusion.'), { text: 'Effusion.', start: 0 });
assert.deepEqual(walkthroughInsert('Intact cuff.', 'Tendinosis.', ['Intact cuff.', '[Cuff]']),
  { text: 'Tendinosis.', start: 0 });
const kept = walkthroughInsert('Partial tear of the supraspinatus.\n\n', 'Muscle atrophy __.', ['Intact cuff.']);
assert.equal(kept.text, 'Partial tear of the supraspinatus.\nMuscle atrophy __.');
assert.equal(kept.text.slice(kept.start), 'Muscle atrophy __.');

// The report is reassembled in template order with the reader's edits.
const sections = [
  { heading: 'INDICATION', body: '[Clinical question]' },
  { heading: 'FINDINGS', body: ['Line one.', 'Line two.'] },
  { heading: 'EMPTY', body: '' },
  { heading: 'IMPRESSION', body: '[Summary]' },
];
assert.equal(walkthroughReport('MRI SHOULDER', sections, new Map([['FINDINGS', '  Edited.  '], ['IMPRESSION', 'Normal.']])),
  'MRI SHOULDER\n\nINDICATION\n[Clinical question]\n\nFINDINGS\nEdited.\n\nEMPTY\n\nIMPRESSION\nNormal.');
assert.equal(walkthroughReport('', sections.slice(1, 2), null), 'FINDINGS\nLine one.\nLine two.');

// Corrected investigation scenes register only from a valid served specification.
const corrected = { id: 'radiology-model-ra.check', title: 'Check · spatial orientation', instructions: 'Drag.',
  scenario: 'radiology-investigation:ra.check', family: 'elbow', focus: ['radius'], reporting_aim: 'Orientation only.' };
assert.equal(wrapper.ensure(corrected), corrected.scenario);
assert.equal(wrapper.ensure(corrected), corrected.scenario, 'Registration is idempotent');
for (const bad of [
  { ...corrected, scenario: 'radiology-investigation:ra.other', family: 'missing' },
  { ...corrected, scenario: 'radiology-investigation:ra.other', focus: ['humerus'] },
  { ...corrected, scenario: 'radiology-investigation:ra.other', focus: 'radius' },
  { ...corrected, scenario: 'radiology-investigation:ra.other', reporting_aim: null },
  { ...corrected, scenario: 'radiology-investigation:../ra.other' },
  { ...corrected, scenario: '__proto__' },
  null,
]) assert.equal(wrapper.ensure(bad), null, JSON.stringify(bad));
assert.equal(wrapper.landmarks('missing'), null);
assert.equal(wrapper.landmarks('__proto__'), null);

const served = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
assert.ok(Array.isArray(served) && served.length === 136, 'All investigations are checked');
let registered = 0, builds = 0;
for (const entry of served) {
  const model = entry.model;
  if (model.scenario.startsWith('radiology-investigation:')) {
    assert.equal(model.scenario, 'radiology-investigation:' + entry.id);
    assert.equal(wrapper.ensure(model), model.scenario, entry.id + ': corrected scene registers');
    assert.equal(model.focus[0], entry.landmarks[0], entry.id + ': corrected scene opens on the first step');
    registered++;
  } else assert.equal(wrapper.ensure(model), model.scenario, entry.id + ': module scene');
  const names = wrapper.landmarks(model.family);
  assert.ok(names, entry.id + ': known family ' + model.family);
  for (const landmark of new Set(entry.landmarks)) {
    assert.ok(Object.prototype.hasOwnProperty.call(names, landmark), entry.id + ': landmark ' + landmark);
    const scene = api.build(model.scenario, { focus: landmark });
    assert.equal(scene.state.focus, landmark, entry.id + ': step focus applies');
    assert.ok(scene.readout.startsWith(names[landmark]), entry.id + ': readout names the landmark');
    assert.ok(scene.primitives.length > 10 && scene.primitives.length <= 3000, entry.id + ': geometry budget');
    scene.primitives.forEach(p => p.points.forEach(point =>
      assert.ok(point.length === 3 && point.every(Number.isFinite), entry.id + ': finite geometry')));
    builds++;
  }
}
console.log(JSON.stringify({ investigations: served.length, corrected: registered, builds, status: 'passed' }, null, 2));

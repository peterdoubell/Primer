#!/usr/bin/env node
'use strict';

// Exercise the shipped scene builders and geometry engine directly, without a DOM.
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
global.window = {};
require('../web/spatial-models.js');
require('../web/spatial-radiology.js');
const api = global.window.PrimerSpatial;
const expected = ['rad.3.ct-image', 'rad.5.tavi-ct', 'rad.3.fracture-description'].sort();
assert.equal(JSON.stringify([...api.supported].sort()), JSON.stringify(expected));
const nodes = fs.readdirSync(path.join(ROOT, 'data/curriculum')).filter(file => /^\d.*\.json$/.test(file))
  .flatMap(file => JSON.parse(fs.readFileSync(path.join(ROOT, 'data/curriculum', file), 'utf8')).nodes);
const entries = nodes.flatMap(node => (node.lesson_media || []).filter(item => item.renderer === 'spatial-3d')
  .map(item => ({ node, item })));
assert.equal(entries.length, expected.length, 'Every spatial scene must be reachable from its curriculum lesson');
assert.equal(JSON.stringify(entries.map(({ node }) => node.id).sort()), JSON.stringify(expected));
entries.forEach(({ node, item }) => assert.deepEqual(item.props, { scenario: node.id }));
const C = { blue: '#3e7085', teal: '#317e78', gold: '#b98a2f', coral: '#b96652', plum: '#876888', green: '#5c7754', ink: '#263b46' };
const near = (a, b, tolerance = 1e-7) => assert.ok(Math.abs(a - b) <= tolerance, `${a} differs from ${b}`);
const sub = (a, b) => a.map((v, i) => v - b[i]);
const dot = (a, b) => a.reduce((sum, v, i) => sum + v * b[i], 0);
const norm = a => Math.hypot(...a);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const primitives = (scene, kind, color) => scene.primitives.filter(p => p.kind === kind && (!color || p.color === color));
const teaching = scene => JSON.stringify({ primitives: scene.primitives, readout: scene.readout, note: scene.note, legend: scene.legend });
let scenarioChecks = 0;
let controlChecks = 0;
function verify(id, supplied) {
  const scene = api.build(id, supplied);
  assert.ok(scene.primitives.length > 0 && scene.primitives.length <= 3000, id + ': geometry budget');
  assert.equal(JSON.stringify(scene), JSON.stringify(api.build(id, supplied)), id + ': deterministic rebuild');
  assert.ok(typeof scene.readout === 'string' && scene.readout.trim());
  assert.ok(typeof scene.note === 'string' && scene.note.trim());
  assert.ok(scene.legend.length > 0);
  scene.primitives.forEach(p => {
    assert.ok(['polygon', 'line', 'sphere', 'label'].includes(p.kind));
    assert.ok(p.points.length > 0);
    p.points.forEach(point => assert.ok(point.length === 3 && point.every(Number.isFinite), id + ': finite coordinates'));
    if (p.kind === 'sphere') assert.ok(Number.isFinite(p.radius) && p.radius > 0);
    if (p.opacity != null) assert.ok(Number.isFinite(p.opacity) && p.opacity >= 0 && p.opacity <= 1);
    if (p.width != null) assert.ok(Number.isFinite(p.width) && p.width > 0);
  });
  scenarioChecks += 1;
  return scene;
}
for (const id of expected) {
  const initial = verify(id);
  for (const control of api.controls(id)) {
    const values = control.options ? control.options.map(o => o.value) : [control.min, (control.min + control.max) / 2, control.max];
    const versions = values.map(value => verify(id, { ...initial.state, [control.key]: value }));
    assert.ok(versions.some(scene => teaching(scene) !== teaching(initial)), id + ': ' + control.key + ' must change the explanation or geometry');
    if (!control.options) {
      for (const invalid of [NaN, Infinity, -Infinity, 'not a number']) {
        assert.equal(JSON.stringify(verify(id, { [control.key]: invalid })), JSON.stringify(initial));
      }
    }
    controlChecks += 1;
  }
  console.log('COVER ' + id);
}
console.log(`Verified ${expected.length} spatial models`);
// Radiology: validate actual section geometry, not only readout strings.
for (const plane of ['axial', 'coronal', 'sagittal']) {
  const axis = { axial: 1, coronal: 2, sagittal: 0 }[plane];
  for (const position of [-.6, 0, .6, 1]) {
    const section = api.build('rad.3.ct-image', { plane, position });
    const contours = primitives(section, 'line', C.coral);
    assert.equal(contours.length, Math.abs(position) < .65 ? 1 : 0);
    contours.flatMap(p => p.points).forEach(p => { near(p[axis], position); near(norm(p), .65); });
  }
}
for (const tilt of [0, 30, 60]) {
  const section = api.build('rad.5.tavi-ct', { tilt });
  const diameter = primitives(section, 'line', C.coral).find(p => p.points.length === 2);
  near(norm(sub(...diameter.points)), 1.1 / Math.cos(tilt * Math.PI / 180));
  primitives(section, 'line', C.coral).flatMap(p => p.points).forEach(p => {
    near(Math.hypot(p[0], p[2]), .55);
    near(p[1], p[0] * Math.tan(tilt * Math.PI / 180));
  });
}
for (const direction of ['lateral', 'anterior']) {
  const scene = api.build('rad.3.fracture-description', { translation: 1, angle: 40, direction });
  const faces = primitives(scene, 'polygon', C.coral);
  // The fracture face centre translates exactly one shaft width, independent of angle.
  const centre = faces[2].points.reduce((sum,p) => sum.map((v,i) => v+p[i]/4), [0,0,0]);
  near(centre[direction === 'lateral' ? 0 : 2], .4);
  near(centre[1], -.08);
}
console.log('Verified radiology section, obliquity and fragment-position invariants.');

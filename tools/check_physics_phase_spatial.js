#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');

// Independent constant-property water reference. Ice at 0 °C defines h = 0.
// Q/m = c ΔT within a phase and Q/m = L Δf during a transition.
// Rounded teaching constants: c = 2.09, 4.186, 2.020 kJ/(kg·K),
// L_f = 334 and L_v = 2256 kJ/kg at fixed atmospheric pressure.
// Primary references:
// https://openstax.org/books/university-physics-volume-2/pages/1-4-heat-transfer-specific-heat-and-calorimetry
// https://openstax.org/books/university-physics-volume-2/pages/1-5-phase-changes
// These expected values never call the shipped phase resolver.
const knots = Object.freeze([
  Object.freeze({h: -62.7, temperature: -30, ice: 1, water: 0, steam: 0}),
  Object.freeze({h: 0, temperature: 0, ice: 1, water: 0, steam: 0}),
  Object.freeze({h: 334, temperature: 0, ice: 0, water: 1, steam: 0}),
  Object.freeze({h: 752.6, temperature: 100, ice: 0, water: 1, steam: 0}),
  Object.freeze({h: 3008.6, temperature: 100, ice: 0, water: 0, steam: 1}),
  Object.freeze({h: 3089.4, temperature: 140, ice: 0, water: 0, steam: 1}),
]);
const stages = Object.freeze(['ice', 'fusion', 'liquid', 'vaporization', 'steam']);
const fractionKeys = Object.freeze(['ice', 'water', 'steam']);
const near = (actual, expected, label) => assert.ok(
  Math.abs(actual - expected) <= 3e-12 * Math.max(1, Math.abs(actual), Math.abs(expected)),
  `${label}: ${actual} != ${expected}`,
);
function vector(actual, expected, label) {
  assert.equal(actual.length, 3, `${label}: three physical axes`);
  actual.forEach((value, axis) => near(value, expected[axis], `${label} axis ${axis}`));
}
function expectedState(index, progress) {
  const a = knots[index], b = knots[index + 1], t = progress / 100;
  return Object.fromEntries(Object.keys(a).map(key => [key, a[key] + (b[key] - a[key]) * t]));
}
function point(state) { return [state.h / 1000, state.temperature / 100, state.water]; }

// Load the actual CommonJS modules; do not evaluate filesystem source strings.
global.window = {PrimerPhysicsPhaseLab: require('../web/physics-phase-lab.js')};
require('../web/spatial-models.js');
require('../web/spatial-module-objects.js');
const binding = require('../data/module-models.json').models.find(model => model.node_id === 'phys.2.matter');
assert.ok(binding, 'Actual matter spatial binding must exist');
assert.equal(binding.family, 'phase-enthalpy-path');
assert.equal(binding.mode, 'model');
const item = {props: {scenario: 'module.phys.2.matter', family: binding.family,
  mode: binding.mode, context: binding.context, lesson: 'States of Matter'}};
assert.equal(window.PrimerModuleObjects.ensure(item), true);
const build = supplied => window.PrimerSpatial.build(item.props.scenario, supplied);
const controls = window.PrimerSpatial.controls(item.props.scenario);
assert.deepEqual(controls.map(control => control.key), ['stage', 'progress']);
assert.deepEqual(controls.find(control => control.key === 'stage').options.map(option => option.value), stages);
assert.deepEqual(
  ['min', 'max', 'step'].map(key => controls.find(control => control.key === 'progress')[key]),
  [0, 100, 1],
);

let states = 0;
const endpoints = [];
function checkScene(stageIndex, progress) {
  const scene = build({stage: stages[stageIndex], progress});
  const expected = expectedState(stageIndex, progress);
  assert.equal(scene.state.stage, stages[stageIndex]);
  assert.equal(scene.state.progress, progress);
  near(scene.phase.enthalpy, expected.h, 'Selected enthalpy');
  near(scene.phase.temperature, expected.temperature, 'Selected temperature');
  fractionKeys.forEach(key => near(scene.phase.fractions[key], expected[key], `${key} mass fraction`));
  near(fractionKeys.reduce((sum, key) => sum + scene.phase.fractions[key], 0), 1, 'Fractions sum to one');

  const segments = scene.primitives.filter(primitive => primitive.phase_kind === 'equilibrium_segment');
  assert.equal(segments.length, 5);
  stages.forEach((stage, index) => {
    const matches = segments.filter(segment => segment.stage === stage);
    assert.equal(matches.length, 1, `One continuous ${stage} interval`);
    const segment = matches[0];
    assert.equal(segment.kind, 'line');
    assert.equal(segment.points.length, 2, 'Constant-property segments are linear');
    vector(segment.points[0], point(knots[index]), `${stage} physical start`);
    vector(segment.points[1], point(knots[index + 1]), `${stage} physical end`);
    segment.enthalpy_bounds.forEach((value, end) => near(value, knots[index + end].h, `${stage} metadata endpoint`));
    if (index) vector(segment.points[0], segments.find(value => value.stage === stages[index - 1]).points[1], `${stage} shared endpoint`);
  });

  const markers = scene.primitives.filter(primitive => primitive.phase_kind === 'selected_state');
  assert.equal(markers.length, 1);
  const marker = markers[0];
  assert.equal(marker.kind, 'sphere');
  assert.equal(marker.points.length, 1);
  vector(marker.points[0], point(expected), 'Selected marker physical coordinates');
  near(marker.enthalpy, expected.h, 'Marker enthalpy metadata');
  near(marker.temperature, expected.temperature, 'Marker temperature metadata');
  fractionKeys.forEach(key => near(marker.fractions[key], expected[key], `Marker ${key} metadata`));
  near(marker.radius, .045, 'Marker radius is a constant display aid');
  const selectedSegment = segments.find(segment => segment.stage === stages[stageIndex]);
  vector(marker.points[0], selectedSegment.points[0].map((value, axis) =>
    value + (selectedSegment.points[1][axis] - value) * progress / 100), 'Marker lies on its interval');

  // A graph must not acquire extra particle, body, volume or force artwork.
  // Quantitative phase data are the five segments and the single point above;
  // remaining lines and labels are the three dimensioned coordinate axes.
  scene.primitives.forEach(primitive => {
    assert.ok(['line', 'sphere', 'label'].includes(primitive.kind), 'No material-volume surface on a thermodynamic graph');
    primitive.points.forEach(p => assert.ok(p.every(Number.isFinite), 'Finite physical graph coordinates'));
    if (primitive.kind === 'sphere') assert.equal(primitive.phase_kind, 'selected_state');
  });
  const axes = scene.primitives.filter(primitive => primitive.kind === 'line' && !primitive.phase_kind);
  assert.equal(axes.length, 3);
  axes.forEach(axis => {
    const changed = [0, 1, 2].filter(index => axis.points[0][index] !== axis.points[1][index]);
    assert.equal(changed.length, 1, 'Each reference line is a Cartesian axis');
    const coordinate = changed[0];
    for (const end of axis.points) end.forEach((value, index) => {if (index !== coordinate) assert.equal(value, 0);});
    assert.ok(Math.min(...axis.points.map(p => p[coordinate])) <= 0);
    const maximum = Math.max(...axis.points.map(p => p[coordinate]));
    assert.ok(maximum >= [3.0894, 1.4, 1][coordinate], 'Axis covers its full physical data range');
  });
  assert.deepEqual(axes.map(axis => [0, 1, 2].find(index => axis.points[0][index] !== axis.points[1][index])).sort(), [0, 1, 2]);
  const labels = scene.primitives.filter(primitive => primitive.kind === 'label');
  near(labels.find(label => label.text === '3000').points[0][0], 3, '3000 kJ/kg tick');
  near(labels.find(label => label.text === '100').points[0][1], 1, '100 °C tick');
  near(labels.find(label => label.text === '−30').points[0][1], -.3, '−30 °C tick');
  near(labels.find(label => label.text === '1').points[0][2], 1, 'Liquid mass-fraction one tick');
  assert.ok(scene.note.includes('not a molecular arrangement or inferred volume'));
  assert.ok(scene.note.includes('not elapsed time'));
  states++;
  return {scene, marker, segments};
}

for (let stage = 0; stage < 5; stage++) {
  let previous;
  for (let progress = 0; progress <= 100; progress++) {
    const current = checkScene(stage, progress);
    if (previous) assert.ok(current.marker.points[0][0] > previous.marker.points[0][0], 'Progress must advance specific enthalpy');
    if (progress === 0 || progress === 100) endpoints.push(current.marker.points[0]);
    previous = current;
  }
}
for (let index = 1; index < 5; index++) vector(endpoints[index * 2 - 1], endpoints[index * 2], 'Interval selection preserves boundary state');

// The latent-heat intervals have their actual relative widths. Their y
// coordinates are flat while z increases for melting and falls for boiling.
const sample = build({stage: 'fusion', progress: 50});
const fusion = sample.primitives.find(p => p.stage === 'fusion');
const vaporization = sample.primitives.find(p => p.stage === 'vaporization');
near((vaporization.points[1][0] - vaporization.points[0][0]) /
  (fusion.points[1][0] - fusion.points[0][0]), 2256 / 334, 'Latent-heat width ratio');
vector(fusion.points[1].map((v, i) => v - fusion.points[0][i]), [.334, 0, 1], 'Fusion physical displacement');
vector(vaporization.points[1].map((v, i) => v - vaporization.points[0][i]), [2.256, 0, -1], 'Vaporization physical displacement');

// Supplied values pass through the same normalization used by visible controls.
for (const [supplied, expected] of [[-1, 0], [101, 100], [49.49, 49], [49.51, 50]]) {
  const scene = build({stage: 'liquid', progress: supplied});
  assert.equal(scene.state.progress, expected);
  vector(scene.primitives.find(p => p.phase_kind === 'selected_state').points[0], point(expectedState(2, expected)), 'Normalized progress changes the marker');
}
for (const progress of [NaN, Infinity, -Infinity, 'invalid']) {
  const scene = build({stage: 'liquid', progress});
  assert.equal(scene.state.progress, 50);
  vector(scene.primitives.find(p => p.phase_kind === 'selected_state').points[0], point(expectedState(2, 50)), 'Invalid progress returns to default');
}
assert.equal(build({stage: 'unknown'}).state.stage, 'fusion');

console.log(`Verified ${states} phase spatial states: all five enthalpy intervals, every progress tick, physical endpoints, continuous boundaries, dimensioned axes, liquid-fraction coordinates and control dependence.`);

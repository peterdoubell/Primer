#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
// Only fixed shipped CommonJS modules are loaded. Manifest contents are data.
global.window = {};
window.PrimerPhysicsCycleLab = require('../web/physics-cycle-lab.js');
window.PrimerMathNumericalLab = require('../web/math-numerical-lab.js');
require('../web/spatial-models.js');
require('../web/spatial-module-objects.js');
const spatial = window.PrimerSpatial, objects = window.PrimerModuleObjects;
const manifest = JSON.parse(fs.readFileSync(require('node:path').join(__dirname, '../data/module-models.json'), 'utf8'));
function item(id, family) {
  const b = manifest.models.find(m => m.node_id === id);
  assert.equal(b.family, family); assert.equal(b.mode, 'model');
  return { title: b.title, instructions: b.instructions, props: { scenario: 'module.' + id, family: b.family, mode: b.mode, context: b.context, lesson: id } };
}
const measureItem = item('math.5.measure', 'shrinking-support-subgraph'), cycleItem = item('phys.3.thermo', 'carnot-state-path');
const numericalItem = item('math.5.numerical', 'numerical-conditioning');
assert.ok(objects.ensure(measureItem)); assert.ok(objects.ensure(cycleItem));
assert.ok(objects.ensure(numericalItem));
const measureId = measureItem.props.scenario, cycleId = cycleItem.props.scenario;
const near = (a, b, tolerance = 3e-11) => assert.ok(Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(b)), `${a} != ${b}`);
const vector = (a, b) => a.forEach((v, i) => near(v, b[i]));
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
function solidVolume(faces) {
  return faces.reduce((total, face) => total + face.points.slice(1, -1).reduce((sum, p, j) => sum + dot(face.points[0], cross(p, face.points[j + 2])) / 6, 0), 0);
}
let measureCount = 0, cycleCount = 0, pathPoints = 0, selectedCount = 0, mounted = 0;
function checkMeasure(raw) {
  const scene = spatial.build(measureId, raw), s = scene.state, n = 2 ** s.indexPower, a = Number(s.alpha), A = s.amplitude;
  const h = A * n ** a, w = 1 / n, faces = scene.primitives.filter(p => p.measure_kind === 'subgraph_boundary');
  assert.equal(faces.length, A === 0 ? 0 : 6);
  if (A > 0) {
    const points = faces.flatMap(f => f.points), ranges = [0, 1, 2].map(axis => [Math.min(...points.map(p => p[axis])), Math.max(...points.map(p => p[axis]))]);
    vector(ranges.map(r => r[0]), [0, 0, 0]); vector(ranges.map(r => r[1]), [w, h, 1]);
    const vertices = new Set(points.map(p => p.join(','))); assert.equal(vertices.size, 8);
    const planes = new Set();
    faces.forEach(f => {
      assert.equal(f.points.length, 4); assert.equal(f.x_boundaries_included, false);
      const axis = [0, 1, 2].find(i => f.points.every(p => p[i] === f.points[0][i]));
      assert.notEqual(axis, undefined); planes.add(axis + ':' + f.points[0][axis]);
      f.points.forEach(p => p.forEach((v, i) => assert.ok(v === ranges[i][0] || v === ranges[i][1])));
      vector([f.physical.width, f.physical.height, f.physical.depth], [w, h, 1]);
    });
    assert.equal(planes.size, 6); near(solidVolume(faces), h * w); near(scene.measure.integral, solidVolume(faces));
    near(scene.measure.norm2Squared, h * h * w);
    if (n === 65536) assert.equal(ranges[0][1], 1 / 65536, 'No minimum width is invented.');
  } else {
    const reference = scene.primitives.find(p => p.measure_kind === 'support_interval_reference');
    assert.ok(reference); assert.equal(reference.volume, 0); vector(reference.points[0], [0, 0, .5]); vector(reference.points[1], [w, 0, .5]);
    assert.equal(scene.measure.integral, 0); assert.equal(scene.measure.norm2Squared, 0);
  }
  const rationalProbe = s.probe === 'zero' ? [0, 1] : s.probe === 'quarter' ? [1, 4] : s.probe === 'boundary' ? [1, n] : [1, 2 * n];
  const inside = rationalProbe[0] > 0 && BigInt(n) * BigInt(rationalProbe[0]) < BigInt(rationalProbe[1]);
  const marker = scene.primitives.find(p => p.measure_kind === 'probe'); assert.equal(marker.inside, inside);
  assert.deepEqual(marker.rational, { a: rationalProbe[0], b: rationalProbe[1] });
  vector(marker.points[0], [rationalProbe[0] / rationalProbe[1], inside ? h : 0, .5]);
  near(scene.measure.width, w); near(scene.measure.height, h); near(scene.measure.integral, A * n ** (a - 1));
  assert.match(scene.note, /closure/); assert.match(scene.note, /not the squared L² norm/); assert.match(scene.note, /no minimum width/);
  measureCount++; return scene;
}
for (let q = 0; q <= 16; q++) for (let k = 0; k <= 32; k++) for (const alpha of ['0', '0.5', '1'])
  for (const probe of ['zero', 'quarter', 'boundary', 'inside']) checkMeasure({ indexPower: q, amplitude: k / 4, alpha, probe });
const example = spatial.build(measureId, { indexPower: 2, amplitude: 2, alpha: '1' });
assert.equal(example.measure.integral, 2); assert.equal(example.measure.norm2Squared, 16);

// Independently derive ideal-gas corners and quasistatic p(V), without using
// the 2D lab's stateAtLeg, cycleData, leg balances or interpolation as an oracle.
const R = 8.31446261815324, amount = .1, gamma = 5 / 3, Cv = 1.5 * R, VA = .001;
function oracle(s) {
  const ratio = Math.exp(s.hotHeat / (amount * R * s.hot)), factor = (s.hot / s.cold) ** (1 / (gamma - 1));
  const corners = [[VA, s.hot, 0], [VA * ratio, s.hot, s.hotHeat / s.hot], [VA * ratio * factor, s.cold, s.hotHeat / s.hot], [VA * factor, s.cold, 0]]
    .map(([V, T, S], i) => ({ name: 'ABCD'[i], V, T, S, p: amount * R * T / V, U: amount * Cv * T }));
  const indices = s.mode === 'engine' ? [0, 1, 2, 3, 0] : [0, 3, 2, 1, 0];
  return { corners, legs: indices.slice(0, -1).map((from, i) => ({ from: corners[from], to: corners[indices[i + 1]],
    kind: corners[from].T === corners[indices[i + 1]].T ? 'isothermal' : 'adiabatic' })) };
}
function stateAt(leg, fraction) {
  const V = fraction === 0 ? leg.from.V : fraction === 1 ? leg.to.V : Math.exp((1 - fraction) * Math.log(leg.from.V) + fraction * Math.log(leg.to.V));
  const T = leg.kind === 'isothermal' ? leg.from.T : leg.from.T * (leg.from.V / V) ** (gamma - 1);
  const p = leg.kind === 'isothermal' ? amount * R * T / V : leg.from.p * (leg.from.V / V) ** gamma;
  const deltaU = amount * Cv * (T - leg.from.T), Q = leg.kind === 'isothermal' ? amount * R * T * Math.log(V / leg.from.V) : 0;
  const Wby = leg.kind === 'isothermal' ? Q : (leg.from.p * leg.from.V - p * V) / (gamma - 1);
  return { V, T, p, U: amount * Cv * T, S: leg.from.S + amount * Cv * Math.log(T / leg.from.T) + amount * R * Math.log(V / leg.from.V), Q, Wby, deltaU };
}
function verifyState(q, expected) { for (const key of ['V', 'T', 'p', 'U', 'S', 'Q', 'Wby', 'deltaU']) near(q[key], expected[key]); near(q.Q - q.Wby, q.deltaU); }
const SI = { volume: .005, pressure: 200000, temperature: 1000 }, point = q => [q.V / SI.volume, q.p / SI.pressure, q.T / SI.temperature];
function checkCycle(raw, path = true) {
  const scene = spatial.build(cycleId, raw), c = scene.cycle, s = scene.state, expected = oracle(s);
  assert.ok(s.hot > s.cold && s.hotHeat > 0); assert.equal(c.state.hot, s.hot); assert.equal(c.state.cold, s.cold); assert.equal(c.state.hotHeat, s.hotHeat);
  assert.equal(c.state.moles, .1); assert.equal(c.state.volume, .001); assert.equal(c.state.leak, 0); assert.deepEqual(c.scales, SI);
  expected.corners.forEach((q, i) => { assert.equal(c.corners[i].name, q.name); for (const key of ['V', 'T', 'p', 'U', 'S']) near(c.corners[i][key], q[key]); });
  const curves = scene.primitives.filter(p => p.cycle_kind === 'process_leg'); assert.equal(curves.length, 4);
  for (let i = 0; i < 4; i++) {
    const leg = c.legs[i], wanted = expected.legs[i], curve = curves.find(p => p.leg === i);
    assert.equal(leg.from.name, wanted.from.name); assert.equal(leg.to.name, wanted.to.name); assert.equal(leg.kind, wanted.kind);
    assert.equal(curve.process, wanted.kind); assert.equal(curve.points.length, 121); assert.equal(leg.points.length, 121);
    vector(curve.points[0], point(wanted.from)); vector(curve.points[120], point(wanted.to));
    if (path) for (let j = 0; j <= 120; j++) { const q = stateAt(wanted, j / 120); verifyState(leg.points[j], q); vector(curve.points[j], point(q)); pathPoints++; }
    const end = stateAt(wanted, 1); for (const key of ['Q', 'Wby', 'deltaU']) near(leg[key], end[key]);
    near(leg.deltaS, wanted.to.S - wanted.from.S);
  }
  const selected = stateAt(expected.legs[Number(s.leg)], s.progress / 100), marker = scene.primitives.find(p => p.cycle_kind === 'selected_state');
  assert.equal(c.current.leg, Number(s.leg)); assert.equal(marker.physical.leg, Number(s.leg));
  verifyState(c.current, selected); verifyState(marker.physical, selected); vector(marker.points[0], point(selected));
  const sign = s.mode === 'engine' ? 1 : -1;
  near(c.legs.reduce((sum, leg) => sum + leg.Q, 0), sign * s.hotHeat * (1 - s.cold / s.hot));
  near(c.legs.reduce((sum, leg) => sum + leg.Wby, 0), sign * s.hotHeat * (1 - s.cold / s.hot));
  near(c.legs.reduce((sum, leg) => sum + leg.deltaU, 0), 0); near(c.legs.reduce((sum, leg) => sum + leg.deltaS, 0), 0);
  assert.ok(Math.exp(s.hotHeat / (amount * R * s.hot)) < 8);
  assert.match(scene.note, /121 log-volume samples/); assert.match(scene.note, /not elapsed time/);
  cycleCount++; selectedCount++; return scene;
}
for (const mode of ['engine', 'refrigerator']) for (const hot of [400, 600, 1200]) for (const cold of [100, 300, 350]) for (const hotHeat of [200, 400, 500]) {
  checkCycle({ mode, hot, cold, hotHeat });
  for (const leg of ['0', '1', '2', '3']) for (const progress of [0, 13, 50, 77, 100]) checkCycle({ mode, hot, cold, hotHeat, leg, progress }, false);
}
for (const c of spatial.controls(cycleId)) {
  const values = c.options ? c.options.map(o => o.value) : Array.from({ length: (c.max - c.min) / c.step + 1 }, (_, i) => c.min + i * c.step);
  values.forEach(value => checkCycle({ [c.key]: value }, false));
}

class Text { constructor(value) { this.nodeType = 3; this.textContent = String(value); } }
class Element {
  constructor(tag) {
    this.nodeType = 1; this.tagName = tag; this.attributes = {}; this.children = []; this.events = {}; this.dataset = {}; this.style = {};
    this.classList = { toggle: (name, force) => { const values = new Set((this.attributes.class || '').split(/\s+/).filter(Boolean)); if (force) values.add(name); else values.delete(name); this.attributes.class = [...values].join(' '); } };
  }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  append(...children) { this.children.push(...children); }
  prepend(...children) { this.children.unshift(...children); }
  replaceChildren(...children) { this.children = children; }
  get textContent() { return this.children.map(c => c.textContent).join(''); }
  set textContent(value) { this.children = [new Text(value)]; }
  get value() { return this._value; }
  set value(value) { this._value = String(value); } // Native select/input values are strings.
  addEventListener(name, fn) { (this.events[name] ||= []).push(fn); }
  fire(name) { (this.events[name] || []).forEach(fn => fn({ target: this })); }
  all() { return [this, ...this.children.filter(c => c.nodeType === 1).flatMap(c => c.all())]; }
}
global.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag), createTextNode: value => new Text(value) };
for (const [modelItem, id, check] of [[measureItem, measureId, checkMeasure], [cycleItem, cycleId, checkCycle]]) {
  const root = objects.render(modelItem), input = key => root.all().find(el => el.attributes['data-parameter'] === key);
  for (const c of spatial.controls(id)) for (const value of c.options ? c.options.map(o => o.value) : [c.min, c.min + Math.floor((c.max - c.min) / (2 * c.step)) * c.step, c.max]) {
    input(c.key).value = value; input(c.key).fire(c.options ? 'change' : 'input');
    assert.equal(input(c.key).value, String(value), id + ': native control must retain the requested value');
    const state = Object.fromEntries(spatial.controls(id).map(control => [control.key, control.options ? input(control.key).value : Number(input(control.key).value)]));
    const scene = check(state, false), readout = root.all().find(el => el.attributes.class === 'model-readout spatial-readout').textContent;
    assert.equal(readout, scene.readout); if (id === cycleId) assert.equal(scene.cycle.current.leg, Number(state.leg));
    mounted++;
  }
  root.all().find(el => el.tagName === 'button' && el.textContent === 'Reset model').fire('click');
  const reset = spatial.build(id);
  for (const c of spatial.controls(id)) assert.equal(input(c.key).value, String(reset.state[c.key]));
  assert.equal(root.all().find(el => el.attributes.class === 'model-readout spatial-readout').textContent, reset.readout);
  assert.equal(root.dataset.view, '-28,21,1'); mounted++;
}
// Existing numeric options must keep their authored type after a native select
// stringifies them. This regression exercises the visible old-family handler.
const numericalRoot = objects.render(numericalItem);
const signInput = numericalRoot.all().find(el => el.attributes['data-parameter'] === 'sign');
const numericReadout = () => numericalRoot.all().find(el => el.attributes.class === 'model-readout spatial-readout').textContent;
signInput.value = '-1'; signInput.fire('change');
const negative = spatial.build(numericalItem.props.scenario, { sign: -1 });
assert.equal(signInput.value, '-1'); assert.equal(negative.state.sign, -1);
assert.equal(numericReadout(), negative.readout);
const signedOracle = window.PrimerMathNumericalLab.conditioning(negative.state);
assert.equal(signedOracle.deltaExact.n, -1n); assert.equal(signedOracle.change.n, -1n);
assert.ok(negative.primitives.some(p => p.kind === 'label' && p.text === 'Δx₂ = -1e-15'));
numericalRoot.all().find(el => el.tagName === 'button' && el.textContent === 'Reset model').fire('click');
assert.equal(signInput.value, '1'); assert.equal(numericReadout(), spatial.build(numericalItem.props.scenario).readout);
mounted += 2;
if (process.argv.includes('--json')) {
  const measure = [];
  for (const indexPower of [0, 1, 2, 16]) for (const amplitude of [0, .25, 2]) for (const alpha of ['0', '0.5', '1']) for (const probe of ['zero', 'quarter', 'boundary', 'inside']) {
    const s = spatial.build(measureId, { indexPower, amplitude, alpha, probe });
    measure.push({ state: s.state, measure: s.measure, faces: s.primitives.filter(p => p.measure_kind === 'subgraph_boundary'), probe: s.primitives.find(p => p.measure_kind === 'probe') });
  }
  const cycle = [];
  for (const mode of ['engine', 'refrigerator']) for (const hot of [400, 1200]) for (const cold of [100, 350]) for (const hotHeat of [200, 500]) for (const leg of ['0', '1', '2', '3']) {
    const s = spatial.build(cycleId, { mode, hot, cold, hotHeat, leg, progress: 13 });
    cycle.push({ state: s.state, ...s.cycle, curves: s.primitives.filter(p => p.cycle_kind === 'process_leg'), marker: s.primitives.find(p => p.cycle_kind === 'selected_state') });
  }
  console.log(JSON.stringify({ measure, cycle }));
} else console.log(`Integration/cycle 3D: ${measureCount} exact subgraph states; ${pathPoints} independent Carnot path points; ${selectedCount} cycle states; ${mounted} native mounted controls passed.`);

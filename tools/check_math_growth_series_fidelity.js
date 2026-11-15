#!/usr/bin/env node
'use strict';
// Exact BigInt recurrence is independent of the shipped power formulas.
const assert = require('node:assert/strict');
globalThis.window = {};
require('../web/concept-models.js');
const lab = window.PrimerConceptModels;
const near = (a, b, relative = 2e-12) => assert.ok(Number.isFinite(a) && Number.isFinite(b) &&
  Math.abs(a - b) <= relative * Math.max(1, Math.abs(b)), `${a} != ${b}`);
const gcd = (a, b) => b === 0n ? (a < 0n ? -a : a) : gcd(b, a % b);
function rational(n, d = 1n) {
  if (d < 0n) { n = -n; d = -d; }
  const g = gcd(n, d); return { n: n / g, d: d / g };
}
const add = (a, b) => rational(a.n * b.d + b.n * a.d, a.d * b.d);
const multiply = (a, b) => rational(a.n * b.n, a.d * b.d);
const divide = (a, b) => rational(a.n * b.d, a.d * b.n);
const real = a => Number(a.n) / Number(a.d);
let sequenceStates = 0;
for (const mode of ['arithmetic', 'geometric']) for (let first = -4; first <= 4; first++) {
  for (let quarter = -16; quarter <= 16; quarter++) {
    const step = quarter / 4, q = rational(BigInt(quarter), 4n), reference = [], sums = [];
    let term = rational(BigInt(first)), sum = rational(0n);
    for (let n = 1; n <= 24; n++) {
      reference.push(term); sum = add(sum, term); sums.push(sum);
      const d = lab.build('math.3.sequences', { mode, first, step, count: n }).data;
      d.values.forEach((v, i) => near(v, real(reference[i])));
      d.partialSums.forEach((v, i) => near(v, real(sums[i])));
      near(d.sum, real(sum));
      const converges = mode === 'geometric' ? first === 0 || Math.abs(quarter) < 4 : first === 0 && quarter === 0;
      assert.equal(d.converges, converges);
      if (converges) {
        const total = first === 0 ? rational(0n) : divide(rational(BigInt(first)), add(rational(1n), rational(-q.n, q.d)));
        const next = mode === 'geometric' ? multiply(term, q) : rational(0n);
        const tail = first === 0 ? rational(0n) : divide(next, add(rational(1n), rational(-q.n, q.d)));
        near(d.infiniteSum, real(total)); near(d.remainder, real(tail));
        near(d.sum + d.remainder, d.infiniteSum);
      } else { assert.equal(d.infiniteSum, null); assert.equal(d.remainder, null); }
      if (quarter === 0 && mode === 'geometric') {
        assert.equal(d.values[0], first); assert.ok(d.values.slice(1).every(v => v === 0));
      }
      term = mode === 'arithmetic' ? add(term, q) : multiply(term, q);
      sequenceStates++;
    }
  }
}
// A convergent term sequence need not have a convergent series.
for (const first of [-4, -1, 1, 4]) {
  const d = lab.build('math.3.sequences', { mode: 'geometric', first, step: 1 }).data;
  assert.equal(d.sequenceLimit, first); assert.equal(d.converges, false);
}
assert.equal(lab.build('math.3.sequences', { mode: 'geometric', first: 1, step: -1 }).data.sequenceLimit, null);
assert.equal(lab.build('math.3.sequences', { mode: 'geometric', first: 0, step: -4 }).data.converges, true);
const tiny = lab.build('math.3.sequences', { mode: 'geometric', first: 1, step: .25, count: 24 });
assert.ok(tiny.data.remainder > 0); assert.match(tiny.readout, /e-15/);

let exponentialStates = 0;
for (let baseQuarter = 1; baseQuarter <= 20; baseQuarter++) for (let exponentQuarter = -12; exponentQuarter <= 12; exponentQuarter++) {
  const base = baseQuarter / 4, exponent = exponentQuarter / 4;
  const d = lab.build('math.3.expo-logs', { base, exponent }).data;
  // For quarter exponents, the unique positive fourth root of b^(4x)
  // is found with bisection, using rational integer-power input.
  let power = rational(1n), b = rational(BigInt(baseQuarter), 4n);
  for (let i = 0; i < Math.abs(exponentQuarter); i++) power = multiply(power, b);
  if (exponentQuarter < 0) power = divide(rational(1n), power);
  const target = real(power); let lo = 0, hi = Math.max(1, target);
  for (let i = 0; i < 100; i++) { const mid = (lo + hi) / 2; if (mid ** 4 < target) lo = mid; else hi = mid; }
  near(d.value, (lo + hi) / 2);
  assert.equal(d.invertible, base !== 1);
  if (base === 1) assert.equal(d.recovered, null); else near(d.recovered, exponent);
  if (Number.isInteger(exponent)) {
    let expected = rational(1n);
    for (let i = 0; i < Math.abs(exponent); i++) expected = multiply(expected, b);
    if (exponent < 0) expected = divide(rational(1n), expected);
    assert.equal(d.exact, expected.d === 1n ? String(expected.n) : `${expected.n}/${expected.d}`);
  } else assert.equal(d.exact, null);
  exponentialStates++;
}

// Minimal DOM mounts the actual SVG renderer and dispatched controls.
class Text {
  constructor(value) { this.nodeType = 3; this.textContent = String(value); }
}
class Element {
  constructor(tag) {
    this.nodeType = 1; this.tagName = tag; this.attributes = {}; this.children = []; this.events = {}; this.style = {};
    this.classList = { toggle() {} };
  }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  getAttribute(key) { return this.attributes[key] ?? null; }
  append(...items) { this.children.push(...items); }
  prepend(...items) { this.children.unshift(...items); }
  replaceChildren(...items) { this.children = items; }
  get textContent() { return this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.children = [new Text(value)]; }
  addEventListener(name, handler) { (this.events[name] ||= []).push(handler); }
  fire(name) { (this.events[name] || []).forEach(handler => handler({ target: this })); }
  all() { return [this, ...this.children.filter(c => c.nodeType === 1).flatMap(c => c.all())]; }
}
globalThis.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag), createTextNode: value => new Text(value) };
function mount(id, s) {
  const root = lab.render({ props: { scenario: id } });
  for (const [key, value] of Object.entries(s)) {
    const input = root.all().find(e => e.attributes['data-parameter'] === key);
    input.value = String(value); input.fire(input.tagName === 'select' ? 'change' : 'input');
  }
  return root;
}
let geometryStates = 0, curveSegments = 0, maxCurveErrorPixels = 0;
for (const mode of ['arithmetic', 'geometric']) for (const first of [-4, 0, 4]) for (const step of [-4, -1, -.75, 0, .25, .75, 1, 4]) for (const count of [1, 6, 24]) {
  const s = { mode, first, step, count }, root = mount('math.3.sequences', s), d = lab.build('math.3.sequences', s).data;
  const points = root.all().filter(e => e.attributes['data-sequence-point']);
  assert.equal(points.length, count * 2);
  const allValues = [0, ...d.values, ...d.partialSums, ...(d.converges ? [d.infiniteSum] : [])];
  const min = Math.min(...allValues), max = Math.max(...allValues), pad = max === min ? 1 : (max - min) * .08;
  for (const point of points) {
    const a = point.attributes, n = Number(a['data-index']), value = Number(a['data-value']);
    near(value, a['data-sequence-point'] === 'term' ? d.values[n - 1] : d.partialSums[n - 1]);
    near(Number(a.cx), 94 + (n - 1) * 276 / 23);
    near((257 - Number(a.cy)) / 183, (value - (min - pad)) / (max - min + 2 * pad));
    assert.ok(Number(a.cy) >= 74 && Number(a.cy) <= 257);
  }
  assert.equal(root.all().filter(e => e.attributes['data-infinite-sum-line'] !== undefined).length, Number(d.converges));
  const initial = lab.build('math.3.sequences');
  root.all().find(e => e.attributes['data-action'] === 'reset-model').fire('click');
  assert.equal(root.all().find(e => e.attributes.class === 'model-readout').textContent, initial.readout);
  geometryStates++;
}
for (const base of Array.from({ length: 20 }, (_, i) => (i + 1) / 4)) for (const exponent of [-3, -.25, 0, .5, 1, 3]) {
  const root = mount('math.3.expo-logs', { base, exponent }), d = lab.build('math.3.expo-logs', { base, exponent }).data;
  const exp = root.all().filter(e => e.attributes['data-exponential-segment'] !== undefined),
    logs = root.all().filter(e => e.attributes['data-logarithmic-segment'] !== undefined);
  assert.ok(exp.length > 0); assert.equal(logs.length, d.invertible ? exp.length : 0);
  const decode = a => [(Number(a.x1) - 94) / 28 - 3, (288 - Number(a.y1)) / 28 - 3,
    (Number(a.x2) - 94) / 28 - 3, (288 - Number(a.y2)) / 28 - 3];
  for (let i = 0; i < exp.length; i++) {
    const [x1, y1, x2, y2] = decode(exp[i].attributes);
    for (const v of [x1, y1, x2, y2]) assert.ok(v >= -3 - 1e-12 && v <= 5 + 1e-12);
    const mid = (x1 + x2) / 2;
    const error = Math.abs((y1 + y2) / 2 - base ** mid) * 28;
    assert.ok(error < .025, `Chord error ${error}px at base ${base}`); maxCurveErrorPixels = Math.max(maxCurveErrorPixels, error);
    if (d.invertible) {
      const reflection = decode(logs[i].attributes);
      reflection.forEach((v, j) => near(v, [y1, x1, y2, x2][j]));
    }
    curveSegments++;
  }
  const points = root.all().filter(e => e.attributes['data-exponential-point'] || e.attributes['data-logarithmic-point']);
  assert.equal(points.length, d.visiblePoint ? d.invertible ? 2 : 1 : 0);
  for (const p of points) {
    const reflected = p.attributes['data-logarithmic-point'];
    near(Number(p.attributes.cx), 94 + ((reflected ? d.value : exponent) + 3) * 28);
    near(Number(p.attributes.cy), 288 - ((reflected ? exponent : d.value) + 3) * 28);
  }
  geometryStates++;
}
console.log(JSON.stringify({ sequenceStates, exponentialStates, geometryStates, curveSegments, maxCurveErrorPixels }));

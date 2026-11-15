#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
globalThis.window = {};
require('../web/spatial-models.js');
require('../web/math-field-lab.js');
const lab = window.PrimerMathFieldLab;
const spatialBefore = window.PrimerSpatial.supported.slice();
const near = (a, b, tolerance = 1e-10) => assert.ok(Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(b)), `${a} != ${b}`);

// Independent quadrature: the 2×2 Gauss rule is exact through degree three in
// each coordinate. It uses the stated polynomial, not the implementation's
// integral formula or accumulated boundary total.
function gauss2(fn, a, b) {
  const midpoint = (a + b) / 2, half = (b - a) / 2, shift = half / Math.sqrt(3);
  return half * (fn(midpoint - shift) + fn(midpoint + shift));
}
const integrands = { linear: (x, y) => x + y, quadratic: (x, y) => x * x + 2 * y };
const fields = { linear: (x, y) => [x * x / 2, y * y / 2], quadratic: (x, y) => [x ** 3 / 3, y * y] };
let states = 0, edgeChecks = 0;
for (const field of ['linear', 'quadratic']) for (const left of [-2, -.5, 0, 1])
  for (const bottom of [-2, 0, 1]) for (const width of [0, .75, 3]) for (const height of [0, 1.25, 3])
    for (const portion of [0, 35, 100]) for (const resolution of [1, 4, 12]) {
      const options = { field, left, bottom, width, height, portion, resolution };
      const m = lab.build(options), { a, b, c, d } = m.bounds;
      const oracle = gauss2(x => gauss2(y => integrands[field](x, y), c, d), a, b);
      near(m.exact, oracle); near(m.area, (b - a) * (d - c));
      assert.equal(m.cells.length, resolution ** 2);
      let area = 0, sum = 0;
      for (const cell of m.cells) {
        near(cell.x1 - cell.x0, m.dx); near(cell.y1 - cell.y0, m.dy);
        near(cell.x, (cell.x0 + cell.x1) / 2); near(cell.y, (cell.y0 + cell.y1) / 2);
        near(cell.height, integrands[field](cell.x, cell.y));
        near(cell.contribution, cell.height * (cell.x1 - cell.x0) * (cell.y1 - cell.y0));
        area += cell.area; sum += cell.contribution;
      }
      near(area, m.area); near(sum, m.sum); near(m.positive + m.negative, sum);
      near(m.error, field === 'quadratic' ? m.area * m.dx ** 2 / 12 : 0);
      const inward = lab.build({ ...options, orientation: 'inward' });
      near(inward.flux.total, -m.flux.total); near(inward.exact, m.exact); near(inward.sum, m.sum);
      for (const side of m.flux.sides) {
        const tangent = side.end.map((v, i) => v - side.start[i]);
        const length = Math.hypot(...tangent), mid = side.start.map((v, i) => (v + side.end[i]) / 2);
        const oracleEdge = length === 0 ? 0 : gauss2(t => {
          const point = side.start.map((v, i) => v + t * tangent[i]);
          const vector = fields[field](...point);
          return length * (vector[0] * side.normal[0] + vector[1] * side.normal[1]);
        }, 0, 1);
        near(side.flux, oracleEdge);
        if (length > 0) {
          near(side.normal[0], tangent[1] / length);
          near(side.normal[1], -tangent[0] / length);
          const dx = mid[0] - (a + b) / 2, dy = mid[1] - (c + d) / 2;
          assert.ok(dx * side.normal[0] + dy * side.normal[1] >= 0, 'Normal must point out of the geometric rectangle.');
        }
        const reversed = inward.flux.sides.find(s => s.id === side.id);
        near(reversed.flux, -side.flux);
        reversed.normal.forEach((component, i) => near(component, -side.normal[i]));
        assert.deepEqual(reversed.start, side.end); assert.deepEqual(reversed.end, side.start);
        edgeChecks++;
      }
      near(m.flux.total, oracle);
      const derivative = field === 'quadratic' ? gauss2(x => x * x + 2 * d, a, b) : gauss2(x => x + d, a, b);
      near(m.sliceIntegral, derivative);
      if (height > 0 && portion > 0 && portion < 100) {
        const epsilon = 1e-5;
        const plus = lab.integral(field, { a, b, c, d: d + epsilon });
        const minus = lab.integral(field, { a, b, c, d: d - epsilon });
        near((plus - minus) / (2 * epsilon), m.sliceIntegral, 2e-8);
      }
      const differentOrder = lab.build({ ...options, order: 'dydx' });
      near(differentOrder.exact, m.exact); assert.notEqual(differentOrder.iterated, m.iterated);
      assert.equal(m.degenerate, width === 0 || height === 0 || portion === 0);
      if (m.degenerate) assert.match(m.readout, /not claimed/);
      assert.equal(JSON.stringify(m), JSON.stringify(lab.build(options)));
      states++;
    }

// Lower-left approximation has a distinct, independently derived error.
for (const field of ['linear', 'quadratic']) for (const n of [1, 2, 8, 12]) {
  const m = lab.build({ field, resolution: n, method: 'left' });
  const { a, b } = m.bounds;
  const error = m.area * (field === 'linear' ? (m.dx + m.dy) / 2 :
    (a + b) * m.dx / 2 - m.dx ** 2 / 6 + m.dy);
  near(m.error, error);
  m.cells.forEach(cell => { near(cell.x, cell.x0); near(cell.y, cell.y0); });
}
const unit = lab.build({ field: 'linear', left: 0, bottom: 0, width: 1, height: 1 });
near(unit.exact, 1); near(unit.sum, 1); near(unit.flux.total, 1);
const signed = lab.build({});
assert.ok(signed.positive > 0 && signed.negative < 0); near(signed.exact, 4 / 3); near(signed.sum, 1.25);
const early = lab.build({ portion: 25 });
assert.ok(early.exact < 0 && signed.exact > 0, 'Accumulation need not increase while adding negative values.');
const refined = lab.build({ resolution: 8 }); near(signed.error / refined.error, 4);
for (const control of lab.controls) {
  for (const bad of [undefined, null, NaN, Infinity, -Infinity, {}, 'invalid'])
    assert.equal(lab.normalize({ [control.key]: bad })[control.key], lab.initial[control.key]);
}
assert.throws(() => lab.integral('quadratic', { a: 1, b: 0, c: 0, d: 1 }), RangeError);
assert.throws(() => lab.fieldAt('other', 0, 0), RangeError);
assert.throws(() => lab.fieldAt('linear', NaN, 0), RangeError);
assert.throws(() => lab.boundaryFlux('linear', { a: 0, b: 1, c: 0, d: 1 }, 'other'), RangeError);

class Text {
  constructor(value) { this.nodeType = 3; this.textContent = String(value); }
}
class Element {
  constructor(tag) {
    this.nodeType = 1; this.tagName = tag; this.attributes = {}; this.children = []; this.events = {};
    this.classList = { toggle: (name, force) => {
      const values = new Set((this.attributes.class || '').split(/\s+/).filter(Boolean));
      const next = force === undefined ? !values.has(name) : force;
      if (next) values.add(name); else values.delete(name);
      this.attributes.class = [...values].join(' '); return next;
    } };
  }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  append(...items) { this.children.push(...items); }
  prepend(...items) { this.children.unshift(...items); }
  replaceChildren(...items) { this.children = items; }
  get textContent() { return this.children.map(c => c.textContent).join(''); }
  set textContent(value) { this.children = [new Text(value)]; }
  addEventListener(name, handler) { (this.events[name] ||= []).push(handler); }
  fire(name) { (this.events[name] || []).forEach(handler => handler({ target: this })); }
  all() { return [this, ...this.children.filter(c => c.nodeType === 1).flatMap(c => c.all())]; }
}
globalThis.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag),
  createTextNode: value => new Text(value) };
assert.equal(lab.render({ props: { scenario: 'math.4.multivar' } }), null);
const root = lab.render({ renderer: 'math-field-lab', props: { scenario: 'math.4.multivar.integral-flux' } });
const all = () => root.all(), inputFor = key => all().find(el => el.attributes['data-field-control'] === key);
const action = name => all().find(el => el.attributes['data-field-action'] === name);
const readout = () => all().find(el => el.attributes.class === 'model-readout').textContent;
const original = readout();
function checkGeometry() {
  const state = Object.fromEntries(lab.controls.map(control => [control.key, inputFor(control.key).value]));
  const m = lab.build(state), elements = all();
  const faces = elements.filter(el => el.attributes['data-field-face'] !== undefined);
  assert.equal(faces.length, m.degenerate ? 0 : m.cells.filter(cell => cell.height !== 0).length * 6);
  for (const face of faces) {
    const cell = m.cells.find(cell => face.attributes['data-field-cell'] === `${cell.i},${cell.j}`);
    near(Number(face.attributes['data-field-height']), cell.height);
    near(Number(face.attributes['data-field-area']), cell.area);
    assert.equal(face.attributes.fill, cell.height > 0 ? '#317e78' : '#b96652');
  }
  // Check the actual projected geometry, not just its data attributes. Recover
  // the common camera scale from an x-directed edge, then independently apply
  // the analytic orthographic projection to the prism's base and height.
  if (faces.length) {
    const { a, b, c, d } = m.bounds, theta = m.state.yaw * Math.PI / 180, phi = 24 * Math.PI / 180;
    const fmin = m.state.field === 'linear' ? a + c : (a <= 0 && b >= 0 ? 0 : Math.min(a * a, b * b)) + 2 * c;
    const fmax = m.state.field === 'linear' ? b + d : Math.max(a * a, b * b) + 2 * d;
    const vertical = 1.6 / Math.max(1, Math.abs(fmin), Math.abs(fmax));
    const xDirection = [Math.cos(theta), -Math.sin(theta) * Math.sin(phi)];
    const parse = face => face.attributes.points.split(' ').map(point => point.split(',').map(Number));
    const firstTop = faces.find(face => face.attributes['data-field-face'] === '1');
    const topPoints = parse(firstTop), edge = topPoints[1].map((v, i) => v - topPoints[0][i]);
    const scale = (edge[0] * xDirection[0] + edge[1] * xDirection[1]) /
      (m.dx * (xDirection[0] ** 2 + xDirection[1] ** 2));
    assert.ok(scale > 0 && Number.isFinite(scale));
    const project = (x, y, z) => {
      const xx = x - (a + b) / 2, yy = y - (c + d) / 2;
      return [220 + scale * (xx * Math.cos(theta) - yy * Math.sin(theta)),
        180 - scale * (z * vertical * Math.cos(phi) + xx * Math.sin(theta) * Math.sin(phi) + yy * Math.cos(theta) * Math.sin(phi))];
    };
    for (const face of faces.filter(face => ['1', '2'].includes(face.attributes['data-field-face']))) {
      const cell = m.cells.find(cell => face.attributes['data-field-cell'] === `${cell.i},${cell.j}`);
      const lo = Math.min(0, cell.height), hi = Math.max(0, cell.height);
      const expected = face.attributes['data-field-face'] === '1' ?
        [[cell.x0, cell.y0, hi], [cell.x1, cell.y0, hi], [cell.x1, cell.y1, hi], [cell.x0, cell.y1, hi]] :
        [[cell.x0, cell.y0, lo], [cell.x1, cell.y0, lo], [cell.x1, cell.y0, hi], [cell.x0, cell.y0, hi]];
      parse(face).forEach((point, i) => project(...expected[i]).forEach((coordinate, axis) => near(point[axis], coordinate)));
    }
  }
  assert.equal(elements.filter(el => el.tagName === 'svg').length, 3);
  for (const el of elements) for (const value of Object.values(el.attributes)) assert.doesNotMatch(value, /NaN|Infinity/);
  const vectors = elements.filter(el => el.attributes['data-field-vector']);
  assert.equal(vectors.length, m.degenerate ? 0 : 25);
  for (const vector of vectors) {
    const x = Number(vector.attributes['data-field-x']), y = Number(vector.attributes['data-field-y']);
    const expected = fields[m.state.field](x, y);
    near(Number(vector.attributes['data-field-p']), expected[0]); near(Number(vector.attributes['data-field-q']), expected[1]);
  }
  for (const el of elements.filter(el => el.attributes['data-field-normal'])) {
    const side = m.flux.sides.find(side => side.id === el.attributes['data-field-normal']);
    near(Number(el.attributes['data-field-nx']), side.normal[0]); near(Number(el.attributes['data-field-ny']), side.normal[1]);
  }
  near(Number(root.attributes['data-field-exact']), m.exact);
  near(Number(root.attributes['data-field-sum']), m.sum);
  near(Number(root.attributes['data-field-flux']), m.flux.total);
  assert.equal(elements.filter(el => el.attributes['data-field-side']).length, 4);
}
let controlStates = 0;
for (const control of lab.controls) {
  const values = control.options ? control.options.map(o => o.value) : [control.min, (control.min + control.max) / 2, control.max];
  const input = inputFor(control.key);
  assert.ok(all().some(el => el.tagName === 'label' && el.attributes.for === input.attributes.id));
  for (const value of values) {
    input.value = String(value); input.fire(control.options ? 'change' : 'input');
    if (!control.options) input.fire('change');
    checkGeometry(); controlStates++;
  }
  action('reset').fire('click'); assert.equal(readout(), original);
}
action('unit-square').fire('click'); checkGeometry(); near(Number(root.attributes['data-field-exact']), 1);
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true');
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'false');
assert.deepEqual(window.PrimerSpatial.supported, spatialBefore, 'The lab must not add unrelated generic spatial scenes.');
console.log(`Verified ${states} rectangle states, ${edgeChecks} independently integrated boundary sides and ${controlStates} mounted control states; signed cells, orientation, accumulation derivative, degenerate domains and resets passed.`);

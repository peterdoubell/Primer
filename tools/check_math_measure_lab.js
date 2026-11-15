#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/math-measure-lab.js');
const near = (actual, expected, tolerance = 2e-12) => assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
let states = 0, probes = 0, mounted = 0;
// Independent quadrature splits at the analytic support boundary. A fixed
// whole-domain sampling grid can miss the entire spike and is not an oracle.
function splitIntegral(n, A, alpha, power) {
  const f = x => x > 0 && n * x < 1 ? (A * n ** alpha) ** power : 0;
  const cuts = [0, 1 / n, 1]; let total = 0;
  for (let j = 0; j < 2; j++) {
    const width = cuts[j + 1] - cuts[j];
    if (width === 0) continue;
    for (let i = 0; i < 17; i++) total += width / 17 * f(cuts[j] + (i + .5) * width / 17);
  }
  return total;
}
for (const n of [1, 2, 3, 4, 7, 16, 255, 1023, 1024, 65536])
  for (const amplitude of [0, .25, 1, 2, 7.75]) for (const alpha of ['0', '0.5', '1']) {
    const m = lab.build({ n, amplitude, alpha });
    near(m.integral, splitIntegral(n, amplitude, Number(alpha), 1));
    near(m.norm2Squared, splitIntegral(n, amplitude, Number(alpha), 2));
    near(m.norm1, m.integral); near(m.norm2 ** 2, m.norm2Squared);
    near(m.height * m.intervalMeasure, m.integral);
    assert.equal(m.nonzeroMeasure, amplitude === 0 ? 0 : 1 / n);
    assert.equal(m.convergence.dominated, amplitude === 0 || alpha !== '1');
    assert.equal(m.convergence.l1, amplitude === 0 || alpha !== '1');
    assert.equal(m.convergence.l2, amplitude === 0 || alpha === '0');
    assert.equal(m.convergence.uniform, amplitude === 0);
    assert.equal(m.convergence.pointwise, true); assert.equal(m.convergence.almostEverywhere, true);
    if (amplitude === 0) { assert.equal(m.dominatorIntegral, 0); assert.equal(m.probe.dominator, 0); }
    else if (alpha !== '1') {
      near(m.dominatorIntegral, alpha === '0' ? amplitude : 2 * amplitude);
      for (const [a, b] of [[1, 2], [1, 7], [1, 65536], [3, 17], [1, 1]]) {
        const p = lab.build({ n, amplitude, alpha, numerator: a, denominator: b }).probe;
        assert.ok(p.value <= p.dominator * (1 + 1e-14));
      }
    }
    assert.ok(m.series.some(row => row.n === n));
    assert.equal(JSON.stringify(m), JSON.stringify(lab.build({ n, amplitude, alpha })));
    states++;
  }
for (const b of [1, 2, 3, 4, 7, 64, 1024, 65536]) for (const a of [...new Set([0, 1, Math.floor(b / 2), b])])
  for (const n of [...new Set([1, 3, b, 65536])]) for (const alpha of ['0', '0.5', '1']) {
    const m = lab.build({ n, alpha, amplitude: 2, numerator: a, denominator: b });
    const inside = a > 0 && BigInt(n) * BigInt(a) < BigInt(b);
    assert.equal(m.probe.inside, inside);
    near(m.probe.value, inside ? 2 * n ** Number(alpha) : 0);
    const zeroFrom = a === 0 ? 1 : Number((BigInt(b) + BigInt(a) - 1n) / BigInt(a));
    assert.equal(m.probe.zeroFrom, zeroFrom);
    const last = a === 0 ? 0 : zeroFrom - 1;
    near(m.probe.envelope, last === 0 ? 0 : 2 * last ** Number(alpha));
    if (last > 0) assert.equal(lab.probeInside(last, a, b), true);
    assert.equal(lab.probeInside(zeroFrom, a, b), false);
    if (a > 0 && 2 * a <= b) assert.ok(lab.envelopeAt(a, b, 2) >= b / a);
    probes++;
  }
assert.equal(lab.envelopeAt(1, 4, 1), 3); // Strict endpoint: 1/x is NOT the envelope.
assert.equal(lab.envelopeAt(1, 4, 1, '0'), 1);
near(lab.envelopeAt(1, 4, 1, '0.5'), Math.sqrt(3));
for (const alpha of ['0', '0.5', '1']) assert.equal(lab.envelopeAt(1, 1, 1, alpha), 0);
assert.throws(() => lab.envelopeAt(1, 4, -1), RangeError);
assert.throws(() => lab.envelopeAt(1, 4, 1, '2'), RangeError);
assert.throws(() => lab.probeInside(0, 1, 4), RangeError);
assert.throws(() => lab.probeInside(4, 1, 0), RangeError);
const thin = lab.build({ n: 1024, amplitude: 1, alpha: '1' });
const fixedGrid = Array.from({ length: 512 }, (_, j) => (j + .5) / 512).reduce((sum, x) => sum + (x > 0 && x < 1 / 1024 ? 1024 : 0) / 512, 0);
assert.equal(fixedGrid, 0); assert.equal(thin.integral, 1);
for (const control of lab.controls) for (const bad of [undefined, null, NaN, Infinity, -Infinity, {}, 'invalid'])
  assert.equal(lab.normalize({ [control.key]: bad })[control.key], lab.initial[control.key]);
assert.deepEqual(lab.normalize({ n: 999999, amplitude: -3, numerator: 70, denominator: 4, alpha: 2, zoom: false }),
  { n: 65536, amplitude: 0, numerator: 4, denominator: 4, alpha: '1', zoom: false });
assert.equal(lab.normalize({ amplitude: .37 }).amplitude, .25);

class Text { constructor(value) { this.nodeType = 3; this.textContent = String(value); } }
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
  fire(name) { (this.events[name] || []).forEach(fn => fn({ target: this })); }
  all() { return [this, ...this.children.filter(c => c.nodeType === 1).flatMap(c => c.all())]; }
}
global.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag), createTextNode: text => new Text(text) };
global.window = {}; delete require.cache[require.resolve('../web/math-measure-lab.js')];
const browserApi = require('../web/math-measure-lab.js'); assert.equal(browserApi, window.PrimerMathMeasureLab);
assert.equal(lab.render({ props: { scenario: 'math.5.functional.integration-norms' } }), null);
assert.equal(lab.render({ renderer: 'other', props: { scenario: 'math.5.measure.integration-norms' } }), null);
let spoken;
const root = lab.render({ renderer: 'math-measure-lab', props: { scenario: 'math.5.measure.integration-norms' } },
  { speakButton: callback => { spoken = callback; return new Element('button'); } });
const all = () => root.all(), input = key => all().find(el => el.attributes['data-measure-control'] === key);
const action = name => all().find(el => el.attributes['data-measure-action'] === name);
function checkMounted() {
  const m = lab.build(JSON.parse(root.attributes['data-measure-state'])), svgs = all().filter(el => el.tagName === 'svg');
  assert.equal(svgs.length, 4);
  for (const [i, svg] of svgs.slice(0, 2).entries()) {
    const rect = svg.all().find(el => el.attributes['data-measure-support'] !== undefined);
    const xMax = Number(svg.attributes['data-measure-x-max']), yMax = Number(svg.attributes['data-measure-y-max']);
    near(Number(rect.attributes.x), 80); near(Number(rect.attributes.width), 350 / (m.state.n * xMax));
    near(Number(rect.attributes.height), 180 * m.height / yMax); near(Number(rect.attributes.y), 252 - 180 * m.height / yMax);
    near(Number(rect.attributes.width) * Number(rect.attributes.height) / ((350 / xMax) * (180 / yMax)), m.integral);
    const opens = svg.all().filter(el => el.attributes['data-measure-open-endpoint']);
    assert.equal(opens.length, m.height > 0 && Number(rect.attributes.width) > 14 ? 2 : 0);
    if (opens.length) { near(Number(opens[1].attributes.cx), 80 + 350 / (m.state.n * xMax)); assert.equal(opens[1].attributes.fill, '#f5efdf'); }
    const dot = svg.all().find(el => el.attributes['data-measure-probe'] !== undefined);
    if (m.probe.x <= xMax) { near(Number(dot.attributes.cx), 80 + 350 * m.probe.x / xMax); near(Number(dot.attributes.cy), 252 - 180 * m.probe.value / yMax); }
    else assert.equal(dot, undefined);
    if (i === 0 && m.state.n === 65536) assert.ok(Number(rect.attributes.width) < .01, 'Do not widen subpixel support to fabricate mass.');
  }
  const accumulation = svgs[2].all().find(el => el.attributes['data-measure-accumulation']);
  const coords = accumulation.attributes.points.split(' ').map(p => p.split(',').map(Number));
  near(coords[1][0], 80 + 350 / m.state.n); near(coords[2][0], 430); near(coords[1][1], coords[2][1]);
  const curves = svgs[3].all().filter(el => el.attributes['data-measure-norm']);
  assert.equal(curves.length, m.state.amplitude === 0 ? 0 : 3);
  for (const curve of curves) {
    const exponent = Number(m.state.alpha) - ({ 'L¹': 1, 'L²': .5, 'L∞': 0 })[curve.attributes['data-measure-norm']];
    const points = curve.attributes.points.split(' ').map(p => p.split(',').map(Number));
    near(points[0][0], 80); near(points[0][1], 162); near(points[1][0], 430); near(points[1][1], 162 - 90 * exponent);
  }
  for (const el of all()) for (const value of Object.values(el.attributes)) assert.doesNotMatch(value, /NaN|Infinity/);
  const readout = all().find(el => el.attributes.class === 'model-readout').textContent;
  assert.ok(spoken().includes(readout)); assert.match(spoken(), /Lebesgue measure dx/); assert.match(spoken(), /not a conclusion proved by the finite plot/);
  mounted++;
}
checkMounted();
// Clearing and typing is a real number-input transition, not malformed props.
// Preserve the draft so the browser cannot append a digit to a fallback 1.
input('n').value = ''; input('n').fire('input');
assert.equal(input('n').value, ''); assert.equal(JSON.parse(root.attributes['data-measure-state']).n, 4);
input('n').value = '3'; input('n').fire('input');
assert.equal(input('n').value, '3'); assert.equal(JSON.parse(root.attributes['data-measure-state']).n, 3); checkMounted();
input('n').value = ''; input('n').fire('change');
assert.equal(input('n').value, '1'); assert.equal(JSON.parse(root.attributes['data-measure-state']).n, 1); checkMounted();
for (const [key, values] of [['n', [1, 3, 4, 1024, 65536]], ['alpha', ['0', '0.5', '1']], ['amplitude', [0, .25, 8]], ['denominator', [1, 4, 65536]], ['numerator', [0, 1, 65536]]])
  for (const value of values) { input(key).value = String(value); input(key).fire(key === 'alpha' ? 'change' : 'input'); checkMounted(); }
input('zoom').checked = false; input('zoom').fire('change'); checkMounted();
input('zoom').checked = true; input('zoom').fire('change'); checkMounted();
for (const n of [1, 4, 16, 256, 65536]) { all().find(el => el.attributes['data-measure-n'] === String(n)).fire('click'); checkMounted(); }
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true');
action('reset').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'false');
assert.deepEqual(JSON.parse(root.attributes['data-measure-state']), lab.initial); checkMounted();
const other = lab.render({ props: { scenario: 'math.5.measure.integration-norms' } });
assert.notEqual(other.attributes['aria-labelledby'], root.attributes['aria-labelledby']);
console.log(`Math measure lab: ${states} boundary-split integration states, ${probes} exact rational probe states and ${mounted} mounted control states passed.`);

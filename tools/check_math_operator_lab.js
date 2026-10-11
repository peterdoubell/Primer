#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/math-operator-lab.js');
const near = (a, b) => assert.ok(a === b || Math.abs(a - b) <= 2e-12 * Math.max(1e-30, Math.abs(a), Math.abs(b)), `${a} != ${b}`);
let states = 0, mounted = 0;
const cases = [];
for (const operator of ['shift', 'diagonal']) for (const cutoff of [1, 2, 4, 16])
  for (const index of [...new Set([1, cutoff, cutoff + 1, 257])]) for (const [first, second] of [[0, 0], [4, 0], [12, 16], [-3, 7]])
    for (const [lambdaNumerator, lambdaDenominator] of [[0, 1], [2, 5], [1, 2], [1, 65536], [-1, 7], [2, 1]]) {
      const state = { operator, cutoff, index, first, second, lambdaNumerator, lambdaDenominator }, m = lab.build(state), length = Math.max(index + 2, cutoff + 2), requested = Array(length).fill(0);
      requested[index - 1] = first / 4; requested[index] = second / 4;
      for (const r of m.comparisons) {
        const input = requested.map((v, j) => r.kind === 'matrix' && j >= cutoff ? 0 : v), output = Array(length).fill(0), lambda = lambdaNumerator / lambdaDenominator;
        // Independent finite matrix action with a sufficiently large sparse-input
        // window; every offscreen coordinate is retained in the norm accounting.
        for (let row = 0; row < length; row++) for (let col = 0; col < length; col++) {
          if (r.kind !== 'infinite' && (row >= cutoff || col >= cutoff)) continue;
          const entry = operator === 'shift' ? Number(row === col + 1) : row === col ? 1 / (row + 1) : 0;
          output[row] += entry * input[col];
        }
        const residual = output.map((v, j) => v - lambda * input[j]);
        for (const [actual, expected] of [[r.input, input], [r.output, output], [r.residual, residual]]) {
          const map = new Map(actual.entries.map(e => [e.index, e.value]));
          expected.forEach((v, j) => near(map.get(j + 1) || 0, v));
          near(actual.normSquared.value, expected.reduce((s, v) => s + v * v, 0));
          near(actual.visibleSquared.value, expected.slice(0, cutoff).reduce((s, v) => s + v * v, 0));
          near(actual.offscreenSquared.value, expected.slice(cutoff).reduce((s, v) => s + v * v, 0));
          near(actual.visibleSquared.value + actual.offscreenSquared.value, actual.normSquared.value);
        }
        near(r.excludedInputSquared.value, requested.reduce((s, v) => s + v * v, 0) - input.reduce((s, v) => s + v * v, 0));
        assert.equal(r.eigenvector, r.input.normSquared.numerator !== '0' && r.residual.normSquared.numerator === '0');
        if (operator === 'shift') assert.equal(r.spectrum.inverseNorm, null, 'Do not invent reciprocal-distance inverse norms for finite shifts.');
      }
      assert.equal(m.selected.kind, 'infinite'); assert.equal(JSON.stringify(m), JSON.stringify(lab.build(state))); states++;
      if (index !== 257 && first !== -3) cases.push(state);
    }
const boundary = lab.build({ index: 4, cutoff: 4, first: 4, second: 0 });
assert.equal(boundary.selected.output.offscreenSquared.exact, '1'); assert.equal(boundary.selected.output.entries[0].index, 5);
assert.equal(boundary.comparisons[1].output.normSquared.exact, '0'); assert.equal(boundary.comparisons[1].eigenvector, true);
const tail = lab.build({ index: 5, cutoff: 4, first: 4, second: 0, lambdaNumerator: 2, lambdaDenominator: 5 });
assert.equal(tail.comparisons[1].excludedInputSquared.exact, '1'); assert.equal(tail.comparisons[1].zeroInput, true); assert.equal(tail.comparisons[1].eigenvector, false);
assert.equal(tail.comparisons[2].residual.offscreenSquared.exact, '4/25');
const distance = lab.build({ operator: 'diagonal', cutoff: 2, lambdaNumerator: 2, lambdaDenominator: 5 });
assert.equal(distance.selected.spectrum.closest.index, 3); assert.equal(distance.selected.spectrum.distance.exact, '1/15'); assert.equal(distance.selected.spectrum.inverseNorm.exact, '15');
assert.equal(distance.comparisons[1].spectrum.inverseNorm.exact, '10');
const tiny = lab.build({ operator: 'diagonal', index: 65536, first: 4, second: 0 });
assert.equal(tiny.selected.residual.normSquared.exact, '1/4294967296'); assert.ok(tiny.selected.residual.normSquared.value > 0); assert.equal(tiny.selected.eigenvector, false);
assert.equal(tiny.selected.spectrum.eigenvalue, false); assert.equal(tiny.comparisons[1].spectrum.inverseNorm.exact, '4'); assert.equal(tiny.comparisons[2].spectrum.eigenvalue, true);
for (const c of lab.controls) for (const bad of [undefined, null, NaN, Infinity, -Infinity, {}, true, 'invalid', '']) assert.equal(lab.normalize({ [c.key]: bad })[c.key], lab.initial[c.key]);

class Text { constructor(text) { this.nodeType = 3; this.textContent = String(text); } }
class Element {
  constructor(tag) { this.nodeType = 1; this.tagName = tag; this.attributes = {}; this.children = []; this.events = {}; this.classList = { toggle: (name, on) => { const s = new Set((this.attributes.class || '').split(' ')); if (on) s.add(name); else s.delete(name); this.attributes.class = [...s].join(' '); } }; }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  append(...items) { this.children.push(...items); }
  prepend(...items) { this.children.unshift(...items); }
  replaceChildren(...items) { this.children = items; }
  get textContent() { return this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.children = [new Text(v)]; }
  set value(v) { this._value = String(v); }
  get value() { return this._value; }
  addEventListener(e, fn) { (this.events[e] ||= []).push(fn); }
  fire(e) { (this.events[e] || []).forEach(fn => fn({ target: this })); }
  all() { return [this, ...this.children.filter(c => c.nodeType === 1).flatMap(c => c.all())]; }
}
global.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag), createTextNode: text => new Text(text) };
global.window = {}; delete require.cache[require.resolve('../web/math-operator-lab.js')]; const browserApi = require('../web/math-operator-lab.js'); assert.equal(browserApi, window.PrimerMathOperatorLab);
assert.equal(lab.render({ props: { scenario: 'math.5.measure.operators-truncation' } }), null);
assert.equal(lab.render({ props: { scenario: 'math.5.functional.operators-truncation', extra: 1 } }), null);
let speak; const root = lab.render({ renderer: 'math-operator-lab', props: { scenario: 'math.5.functional.operators-truncation' } }, { speakButton: callback => { speak = callback; return new Element('button'); } });
const input = key => root.all().find(e => e.attributes['data-operator-control'] === key), action = name => root.all().find(e => e.attributes['data-operator-action'] === name);
function verifyMounted() {
  const state = JSON.parse(root.attributes['data-operator-state']), m = lab.build(state);
  for (const c of lab.controls) assert.equal(input(c.key).value, String(state[c.key]));
  assert.equal(root.all().find(e => e.attributes.class === 'model-readout').textContent, m.readout); assert.ok(speak().includes(m.readout));
  for (const stem of root.all().filter(e => e.attributes['data-operator-stem'])) {
    const set = m.selected[stem.attributes['data-operator-stem']], entry = set.entries.find(e => e.index === Number(stem.attributes['data-index']));
    near(Number(stem.attributes['data-value']), entry.value);
    const points = stem.attributes.points.split(' ').map(p => p.split(',').map(Number)), magnitude = Number(stem.attributes['data-scale']);
    near(points[0][1], 170); near(points[1][1], 170 - 100 * entry.value / magnitude);
  }
  for (const e of root.all()) for (const v of Object.values(e.attributes)) assert.doesNotMatch(v, /NaN|Infinity/);
  mounted++;
}
verifyMounted();
for (const c of lab.controls) for (const v of c.options ? c.options.map(o => o.value) : [c.min, c.max]) {
  input(c.key).value = v; input(c.key).fire('change'); assert.equal(input(c.key).value, String(v)); verifyMounted();
}
input('index').value = ''; input('index').fire('input'); assert.equal(input('index').value, '');
input('index').value = '3'; input('index').fire('change'); assert.equal(JSON.parse(root.attributes['data-operator-state']).index, 3); verifyMounted();
for (const key of ['boundary', 'resolvent', 'tiny', 'zero']) { action(key).fire('click'); verifyMounted(); }
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true'); action('reset').fire('click'); verifyMounted();
assert.deepEqual(JSON.parse(root.attributes['data-operator-state']), lab.initial); assert.equal(action('enlarge').attributes['aria-pressed'], 'false');
if (process.argv.includes('--json')) console.log(JSON.stringify(cases.map(state => lab.build(state))));
else console.log(`Operator lab: ${states} independent matrix-action states and ${mounted} native mounted control states passed.`);

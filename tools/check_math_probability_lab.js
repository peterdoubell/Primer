#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
globalThis.window = {};
require('../web/math-probability-lab.js');
const lab = window.PrimerMathProbabilityLab;
const near = (a, b, tolerance = 1e-10) => assert.ok(Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(b)), `${a} != ${b}`);
const rng = lab.pcg32(42, 54);
assert.deepEqual(Array.from({ length: 6 }, () => rng.word().toString(16)),
  ['a15c02b7', '7b47f409', 'ba1d3330', '83d2f293', 'bfa4784b', 'cbed606e'], 'Official PCG32 published test vector');

let distributions = 0;
for (const n of [1, 2, 10, 100, 1000, 6000, 8192]) for (const p of [0, .01, .1, 1 / 6, .5, .9, .99, 1]) {
  const d = lab.binomial(n, p);
  const total = d.pmf.reduce((sum, probability) => sum + probability, 0);
  const mean = d.pmf.reduce((sum, probability, k) => sum + probability * k, 0);
  const variance = d.pmf.reduce((sum, probability, k) => sum + probability * (k - n * p) ** 2, 0);
  near(total, 1); near(mean, n * p); near(variance, n * p * (1 - p), 1e-9);
  assert.ok(d.pmf.every(value => value >= 0 && value <= 1 && Number.isFinite(value)));
  if (p > 0 && p < 1) assert.ok(d.logs.every(Number.isFinite), 'Positive PMFs keep finite logs even if a binary64 value underflows.');
  else assert.equal(d.logs.filter(Number.isFinite).length, 1);
  if (n <= 10) {
    // Enumerate every binary outcome sequence independently of the PMF recurrence.
    const enumerated = Array(n + 1).fill(0);
    for (let bits = 0; bits < 2 ** n; bits++) {
      let successes = 0;
      for (let j = 0; j < n; j++) successes += (bits >> j) & 1;
      enumerated[successes] += p ** successes * (1 - p) ** (n - successes);
    }
    enumerated.forEach((value, k) => near(d.pmf[k], value));
  }
  distributions++;
}
let tails = 0;
for (const experiment of ['bernoulli', 'die']) for (const n of [1, 2, 10, 100, 1000, 6000, 8192])
  for (const percent of [0, 1, 50, 99, 100]) for (const tolerance of [1, 10, 50]) {
    const state = { experiment, n, percent, tolerance }, p = experiment === 'die' ? 1 / 6 : percent / 100;
    const t = lab.tail(state), bound = Math.min(1, p * (1 - p) / (n * (tolerance / 100) ** 2));
    assert.ok(t.value >= 0 && t.value <= bound + 1e-10);
    const pmf = lab.binomial(n, p).pmf;
    const ordinary = t.outcomes.reduce((sum, k) => sum + pmf[k], 0);
    near(t.value, ordinary);
    if (p === 0 || p === 1) { assert.equal(t.logProbability, -Infinity); assert.equal(lab.probabilityText(t.logProbability), '0'); }
    else assert.ok(Number.isFinite(t.logProbability));
    tails++;
  }
assert.equal(lab.outside(4, { n: 10, percent: 50, tolerance: 10 }), true);
assert.equal(lab.outside(6, { n: 10, percent: 50, tolerance: 10 }), true);
assert.equal(lab.outside(5, { n: 10, percent: 50, tolerance: 10 }), false);
assert.equal(lab.outside(8, { experiment: 'die', n: 30, tolerance: 10 }), true);
assert.equal(lab.outside(2, { experiment: 'die', n: 30, tolerance: 10 }), true);
assert.equal(lab.outside(7, { experiment: 'die', n: 30, tolerance: 10 }), false);
const rare = lab.tail({ n: 8192, percent: 50, tolerance: 50 });
near(rare.logProbability, (1 - 8192) * Math.LN2, 1e-11);
assert.equal(rare.value, 0, 'The binary64 scalar underflows; the log remains authoritative.');
assert.match(lab.probabilityText(rare.logProbability), /× 10\^-/);
assert.notEqual(lab.probabilityText(rare.logProbability), '0');

const short = lab.build({ n: 10 }), long = lab.build({ n: 1000 }), changedTolerance = lab.build({ n: 10, tolerance: 50 });
assert.deepEqual(short.path, long.path.slice(0, 10)); assert.deepEqual(short.path, changedTolerance.path);
assert.notDeepEqual(short.path, lab.build({ n: 10, seed: 43 }).path);
for (const percent of [0, 100]) {
  const model = lab.build({ percent, n: 6000 });
  assert.ok(model.path.every(row => row.outcome === percent / 100));
  assert.equal(model.countVariance, 0); assert.equal(model.proportionVariance, 0);
}
const die = lab.build({ experiment: 'die', n: 6000 });
assert.ok(die.path.every(row => Number.isInteger(row.outcome) && row.outcome >= 1 && row.outcome <= 6));
assert.equal(die.current.count, die.path.filter(row => row.outcome === 6).length);
near(die.current.faceMean, die.path.reduce((sum, row) => sum + row.outcome, 0) / 6000);
near(die.countVariance, 6000 * (1 / 6) * (5 / 6)); near(Math.sqrt(die.countVariance), Math.sqrt(2500 / 3));
const whole = lab.samplePath({});
assert.ok(whole.some((row, i) => i > 0 && Math.abs(row.proportion - .5) > Math.abs(whole[i - 1].proportion - .5)));
const outsideBand = row => Math.abs(100 * row.count - 50 * row.k) >= 10 * row.k;
const counterexample = lab.samplePath({ seed: 1 });
assert.ok(counterexample.some((row, i) => i > 0 && !outsideBand(counterexample[i - 1]) && outsideBand(row)),
  'A real replay path enters and leaves the tolerance band; monotonic convergence is not taught.');
assert.ok(whole.some(row => Math.abs(row.deviation) > Math.sqrt(row.k * .25)), 'One SD is not a path bound.');
for (const control of lab.controls) for (const invalid of [undefined, null, NaN, Infinity, -Infinity, {}, 'invalid'])
  assert.equal(lab.normalize({ [control.key]: invalid })[control.key], lab.initial[control.key]);
for (const [n, p] of [[0, .5], [8193, .5], [1.5, .5], [10, -.1], [10, 1.1], [10, NaN]]) assert.throws(() => lab.binomial(n, p), RangeError);

class Text { constructor(value) { this.nodeType = 3; this.textContent = String(value); } }
class Element {
  constructor(tag) {
    this.tagName = tag; this.nodeType = 1; this.attributes = {}; this.children = []; this.events = {};
    this.classList = { toggle: (name, force) => {
      const values = new Set((this.attributes.class || '').split(/\s+/).filter(Boolean));
      const next = force === undefined ? !values.has(name) : force;
      if (next) values.add(name); else values.delete(name);
      this.attributes.class = [...values].join(' '); return next;
    } };
  }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  append(...items) { this.children.push(...items); }
  prepend(...items) { this.children.unshift(...items); }
  replaceChildren(...items) { this.children = items; }
  get textContent() { return this.children.map(item => item.textContent).join(''); }
  set textContent(value) { this.children = [new Text(value)]; }
  addEventListener(name, handler) { (this.events[name] ||= []).push(handler); }
  fire(name) { (this.events[name] || []).forEach(handler => handler({ target: this })); }
  all() { return [this, ...this.children.filter(item => item.nodeType === 1).flatMap(item => item.all())]; }
}
globalThis.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag), createTextNode: value => new Text(value) };
assert.equal(lab.render({ props: { scenario: 'math.4.prob-theory' } }), null);
const root = lab.render({ renderer: 'math-probability-lab', props: { scenario: 'math.4.prob-theory.large-numbers' } });
const all = () => root.all(), input = key => all().find(el => el.attributes['data-probability-control'] === key);
const action = key => all().find(el => el.attributes['data-probability-action'] === key);
const text = () => all().find(el => el.attributes.class === 'model-readout').textContent;
const original = text(); let mounted = 0;
function verifyMounted() {
  const state = Object.fromEntries(lab.controls.map(c => [c.key, input(c.key).value])), model = lab.build(state);
  assert.equal(Number(root.attributes['data-probability-count']), model.current.count);
  near(Number(root.attributes['data-probability-proportion']), model.current.proportion);
  assert.equal(input('percent').disabled, model.state.experiment === 'die');
  assert.equal(all().filter(el => el.tagName === 'svg').length, 3);
  for (const el of all()) for (const value of Object.values(el.attributes)) assert.doesNotMatch(value, /NaN|Infinity/);
  assert.doesNotMatch(text(), /NaN|Infinity/);
  const proportion = all().find(el => el.attributes['data-probability-path'] === 'proportion');
  if (model.state.n > 1) {
    const points = proportion.attributes.points.split(' ').map(point => point.split(',').map(Number));
    assert.equal(points.length, model.state.n);
    for (const i of [0, Math.floor(points.length / 2), points.length - 1]) {
      near(points[i][0], 72 + 342 * Math.log2(model.path[i].k) / 13);
      near(points[i][1], 260 - 210 * model.path[i].count / model.path[i].k);
    }
  } else assert.equal(proportion, undefined);
  const shown = all().filter(el => el.attributes['data-probability-trial']);
  assert.equal(shown.length, Math.min(20, model.state.n));
  shown.forEach((el, i) => {
    const row = model.path[model.path.length - shown.length + i];
    assert.equal(Number(el.attributes['data-probability-trial']), row.k);
    assert.equal(Number(el.attributes['data-probability-outcome']), row.outcome);
    assert.ok(el.attributes['aria-label']);
  });
}
for (const c of lab.controls) {
  const values = c.options ? c.options.map(o => o.value) : [c.min, (c.min + c.max) / 2, c.max];
  for (const value of values) { input(c.key).value = String(value); input(c.key).fire(c.options ? 'change' : 'input'); verifyMounted(); mounted++; }
  action('reset').fire('click'); assert.equal(text(), original);
}
for (const n of [10, 100, 1000, 6000]) { all().find(el => Number(el.attributes['data-probability-n']) === n).fire('click'); verifyMounted(); }
action('next-seed').fire('click'); assert.equal(input('seed').value, '43');
action('reset').fire('click'); assert.equal(text(), original);
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true');
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'false');
console.log(`Verified ${distributions} binomial distributions, ${tails} concentration states and ${mounted} mounted controls; PCG reference, persistent prefixes, integer tail boundaries, rare probabilities, endpoint laws and resets passed.`);

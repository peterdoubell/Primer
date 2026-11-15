#!/usr/bin/env node
'use strict';
/* Independent second-order ODE checks, followed by interaction/readout checks.
   RK4 is an oracle for the analytic renderer, not the renderer's algorithm. */
const assert = require('node:assert/strict');
globalThis.window = {};
require('../web/math-ode-lab.js');
const lab = window.PrimerMathODELab;
function near(actual, expected, tolerance = 1e-9) {
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)),
    `${actual} differs from ${expected}`);
}

// Solve the first-order system independently by fourth-order Runge–Kutta.
function reference(s, end) {
  const steps = Math.max(1, Math.ceil(end * 2000)), h = end / steps;
  const rhs = (x, v) => [v, -2 * s.damping * s.frequency * v - s.frequency ** 2 * x];
  let x = s.position, v = s.velocity;
  for (let i = 0; i < steps; i++) {
    const k1 = rhs(x, v), k2 = rhs(x + h * k1[0] / 2, v + h * k1[1] / 2);
    const k3 = rhs(x + h * k2[0] / 2, v + h * k2[1] / 2), k4 = rhs(x + h * k3[0], v + h * k3[1]);
    x += h * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]) / 6;
    v += h * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]) / 6;
  }
  return { x, v };
}

let cases = 0;
for (const damping of [0, .35, .95, 1 - 1e-10, 1, 1 + 1e-10, 1.05, 1.7, 2]) {
  for (const frequency of [.5, 2, 3]) for (const [position, velocity] of [[1, 0], [0, 3], [-2, -3], [0, 0]]) {
    const s = { damping, frequency, position, velocity };
    const start = lab.exact(s, 0);
    near(start.x, position); near(start.v, velocity);
    near(start.a, -2 * damping * frequency * velocity - frequency ** 2 * position);
    for (const t of [.125, 1, 3.75, 12]) {
      const q = lab.exact(s, t), oracle = reference(s, t);
      near(q.x, oracle.x, 2e-9); near(q.v, oracle.v, 2e-9);
      const h = 1e-5, left = lab.exact(s, t - h), right = lab.exact(s, Math.min(12, t + h));
      if (t < 12) {
        near(q.v, (right.x - left.x) / (2 * h), 5e-7);
        near(q.a, (right.v - left.v) / (2 * h), 5e-7);
        near(q.energyRate, (right.energy - left.energy) / (2 * h), 2e-6);
      }
      near(q.a + 2 * damping * frequency * q.v + frequency ** 2 * q.x, 0, 2e-12);
      assert.ok(q.energy >= 0 && q.energy <= start.energy + 1e-10);
      assert.ok(q.energyRate <= 0);
      if (damping === 0) near(q.energy, start.energy);
      cases++;
    }
    // Complete finite window: energy must never grow, including the critical
    // limit and cases in which displacement changes sign only once.
    let previous = start.energy;
    for (let i = 1; i <= 120; i++) {
      const q = lab.exact(s, i / 10);
      assert.ok(q.energy <= previous + 1e-10); previous = q.energy;
    }
  }
}

// Repeated-root case from the curriculum: y″+4y′+4y=0,
// y(0)=1, y′(0)=0 gives (1+2t)e^(−2t).
for (const t of [0, .5, 1, 3, 12]) {
  const q = lab.exact({ damping: 1, frequency: 2, position: 1, velocity: 0 }, t);
  near(q.x, (1 + 2 * t) * Math.exp(-2 * t));
  near(q.v, -4 * t * Math.exp(-2 * t));
}
// y″+9y=0, y(0)=0, y′(0)=3 has y=sin(3t).
for (const t of [.125, 1, 3, 12]) near(lab.exact({ damping: 0, frequency: 3, position: 0, velocity: 3 }, t).x, Math.sin(3 * t));
const critical = lab.build({ damping: 1 });
assert.match(critical.basis, /t exp/);
assert.doesNotMatch(lab.build({ damping: 1, time: 12 }).readout, /Energy per unit mass E = 0 /);
assert.notEqual(lab.build({ damping: 1 - 1e-10 }).regime, critical.regime);
assert.notEqual(lab.build({ damping: 1 + 1e-10 }).regime, critical.regime);
for (const damping of [1, 1.7]) {
  const crossing = lab.exact({ damping, frequency: 2, position: .25, velocity: -3 }, 3);
  assert.ok(crossing.x < 0, 'Non-oscillatory does not mean unable to cross equilibrium.');
}
for (const control of lab.controls) {
  for (const bad of [undefined, null, NaN, Infinity, -Infinity, 'bad']) {
    assert.equal(lab.normalize({ [control.key]: bad })[control.key], lab.initial[control.key]);
  }
  assert.equal(lab.normalize({ [control.key]: control.max + 100 })[control.key], control.max);
  assert.equal(lab.normalize({ [control.key]: control.min - 100 })[control.key], control.min);
}
for (const t of [-1, 13, NaN, Infinity, 'bad']) assert.throws(() => lab.exact({}, t), RangeError);

// Minimal owned DOM: exercise actual mounted controls rather than a separate
// simulation. Browser visual QA is a separate release check.
class Text {
  constructor(value) { this.nodeType = 3; this.textContent = String(value); }
}
class Element {
  constructor(tag) {
    this.nodeType = 1; this.tagName = tag; this.attributes = {}; this.children = []; this.events = {};
    this.classList = { toggle: (name, force) => {
      const tokens = new Set((this.attributes.class || '').split(/\s+/).filter(Boolean));
      const value = force === undefined ? !tokens.has(name) : force;
      if (value) tokens.add(name); else tokens.delete(name);
      this.attributes.class = [...tokens].join(' ');
      return value;
    } };
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
globalThis.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag),
  createTextNode: value => new Text(value) };
const item = { renderer: 'math-ode-lab', props: { scenario: 'math.4.diffeq.second-order' } };
assert.equal(lab.render({ props: { scenario: 'math.4.diffeq' } }), null);
const root = lab.render(item), all = () => root.all();
const readout = () => all().find(e => e.attributes.class === 'model-readout').textContent;
const initialReadout = readout();
assert.equal(all().filter(e => e.tagName === 'svg').length, 3);
assert.equal(all().filter(e => e.attributes['data-ode-current-point']).length, 3);
assert.equal(all().filter(e => e.tagName === 'input').length, 5);
const inputFor = key => all().find(e => e.attributes['data-ode-control'] === key);
const buttonFor = action => all().find(e => e.attributes['data-ode-action'] === action);
let controlStates = 0;
for (const control of lab.controls) {
  const input = inputFor(control.key);
  assert.ok(all().some(e => e.tagName === 'label' && e.attributes.for === input.attributes.id));
  for (const value of [control.min, (control.min + control.max) / 2, control.max]) {
    input.value = String(value); input.fire('input'); input.fire('change');
    assert.equal(input.value, String(value));
    assert.ok(input.attributes['aria-valuetext']);
    for (const e of all()) for (const attr of Object.values(e.attributes)) assert.doesNotMatch(attr, /NaN|Infinity/);
    controlStates++;
  }
  buttonFor('reset').fire('click'); assert.equal(readout(), initialReadout);
}
for (const [ratio, regime] of [[0, 'Undamped'], [.35, 'Underdamped'], [1, 'Critically damped'], [1.7, 'Overdamped']]) {
  inputFor('time').value = '3'; inputFor('time').fire('input');
  const button = all().find(e => Number(e.attributes['data-ode-damping']) === ratio);
  button.fire('click');
  assert.equal(root.attributes['data-ode-regime'], regime);
  assert.equal(root.attributes['data-ode-time'], '3'); // Regime changes preserve selected time.
  assert.match(readout(), /At t = 3 s/);
}
buttonFor('enlarge').fire('click'); assert.equal(buttonFor('enlarge').attributes['aria-pressed'], 'true');
buttonFor('enlarge').fire('click'); assert.equal(buttonFor('enlarge').attributes['aria-pressed'], 'false');
inputFor('position').value = '0'; inputFor('position').fire('input');
inputFor('velocity').value = '0'; inputFor('velocity').fire('input');
assert.match(readout(), /Energy per unit mass E = 0/);
buttonFor('reset').fire('click'); assert.equal(readout(), initialReadout);
console.log(`Verified ${cases} analytic states against independent RK4, derivative and energy identities; ${controlStates} mounted control states, four regimes, equilibrium and resets passed.`);

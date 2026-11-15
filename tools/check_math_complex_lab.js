#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/math-complex-lab.js');
const PI = Math.PI, TAU = 2 * PI;
const plus = (a, b) => [a[0] + b[0], a[1] + b[1]], minus = (a, b) => [a[0] - b[0], a[1] - b[1]], times = (a, b) => [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]], scale = (a, n) => a.map(v => v * n);
const divide = (a, b) => scale(times(a, [b[0], -b[1]]), 1 / (b[0] ** 2 + b[1] ** 2));
const mag = a => Math.hypot(...a), exponential = a => [Math.exp(a[0]) * Math.cos(a[1]), Math.exp(a[0]) * Math.sin(a[1])];
const cp = z => [z.re, z.im], object = z => ({ re: z[0], im: z[1] });
const near = (actual, expected, tol = 1e-9) => assert.ok(Number.isFinite(actual) && Number.isFinite(expected) && Math.abs(actual - expected) <= tol * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
const vectorNear = (actual, expected, tol) => { assert.ok(actual); cp(actual).forEach((v, j) => near(v, expected[j], tol)); };
function power(a, n) { if (n < 0) return divide([1, 0], power(a, -n)); let value = [1, 0]; for (let j = 0; j < n; j++) value = times(value, a); return value; }
// Independently written complex functions. Neither runtime evaluate nor its
// complex arithmetic supplies the derivative or quadrature expectations.
function value(name, z, p = {}) {
  if (name === 'z2') return times(z, z);
  if (name === 'exp') return exponential(z);
  if (name === 'conjugate') return [z[0], -z[1]];
  if (name === 'abs2') return [z[0] ** 2 + z[1] ** 2, 0];
  if (name === 'peak') return [1 - z[0] ** 2 - z[1] ** 2, 0];
  if (name === 'constant' || name === 'one') return [1, 0];
  if (name === 'linear' || name === 'annulus-z') return z;
  if (name === 'pathology') return mag(z) === 0 ? [0, 0] : exponential(scale(power(z, -4), -1));
  if (name === 'geometric') return divide([1, 0], minus([1, 0], z));
  if (name === 'poles') return divide([1, 0], plus(times(z, z), [1, 0]));
  if (name === 'annulus-inverse') return divide([1, 0], z);
  if (name === 'rational') return plus(p.residueA === 0 ? [0, 0] : divide([p.residueA, 0], z), p.residueB === 0 ? [0, 0] : divide([p.residueB, 0], minus(z, [2, 0])));
  if (name === 'laurent') return [[3, -2], [5, -1], [7, 0], [2, 1], [1, 2]].reduce((r, [a, n]) => plus(r, scale(power(z, n), a)), [0, 0]);
  throw Error(name);
}
// Midpoint integration and periodic trapezoids are separate from production's
// Simpson rule; analytic antiderivatives/proof inequalities supply more oracles.
function midpoint(fn, a, b, n = 8192) { let r = [0, 0]; for (let j = 0; j < n; j++) r = plus(r, fn(a + (b - a) * (j + .5) / n)); return scale(r, (b - a) / n); }
function periodic(fn, n = 4096) { let r = [0, 0]; for (let j = 0; j < n; j++) r = plus(r, fn(TAU * j / n)); return scale(r, TAU / n); }
function circle(center, radius, theta) { return plus(center, [radius * Math.cos(theta), radius * Math.sin(theta)]); }
let derivatives = 0, contours = 0, taylors = 0, means = 0, arcs = 0, proofs = 0;
for (const name of ['z2', 'exp', 'conjugate', 'abs2']) for (const x of [-1, 0, .25, 1]) for (const y of [-.5, 0, .75]) for (const angle of [0, 45, 90, 120]) for (const logStep of [-1, -3]) {
  const m = lab.directionalModel({ directionalFn: name, pointRe: x, pointIm: y, angle, logStep }), z = [x, y], h = 10 ** logStep, theta = angle * PI / 180, delta = [h * Math.cos(theta), h * Math.sin(theta)], expected = divide(minus(value(name, plus(z, delta)), value(name, z)), delta);
  vectorNear(m.selected.value, expected, 2e-8);
  const tiny = 1e-5, fx = scale(minus(value(name, plus(z, [tiny, 0])), value(name, minus(z, [tiny, 0]))), .5 / tiny), fy = scale(minus(value(name, plus(z, [0, tiny])), value(name, minus(z, [0, tiny]))), .5 / tiny);
  [m.jacobian.ux, m.jacobian.vx, m.jacobian.uy, m.jacobian.vy].forEach((n, j) => near(n, [fx[0], fx[1], fy[0], fy[1]][j], 2e-8));
  const crFromPartials = Math.abs(fx[0] - fy[1]) < 1e-6 && Math.abs(fy[0] + fx[1]) < 1e-6;
  assert.equal(m.cr, crFromPartials); assert.equal(m.holomorphic, name === 'z2' || name === 'exp'); assert.equal(m.pointwise, name === 'z2' || name === 'exp' || name === 'abs2' && x === 0 && y === 0);
  derivatives++;
}
for (const angle of [0, 45, 90]) for (const logStep of [-.5, -1, -2, -4]) {
  const m = lab.directionalModel({ directionalFn: 'pathology', angle, logStep }), h = 10 ** logStep, expected = (angle === 45 ? 1 : -1) / h ** 4 - Math.log(h);
  near(m.selected.logAbs, expected); near(m.selected.phase, -angle * PI / 180); assert.equal(m.cr, true); assert.equal(m.pointwise, false); assert.equal(m.holomorphic, false); assert.deepEqual(m.jacobian, { ux: 0, uy: 0, vx: 0, vy: 0 });
  if (expected > 700) assert.equal(m.selected.value, null); else if (expected < -740) assert.equal(m.selected.status, 'underflow-log-only'); derivatives++;
}
for (const name of ['z2', 'exp']) for (const center of [[0, 0], [.25, -.5]]) for (let n = 0; n <= 4; n++) {
  const r = .75, integral = periodic(theta => { const delta = [r * Math.cos(theta), r * Math.sin(theta)], z = plus(center, delta), dz = times([0, 1], delta); return times(divide(value(name, z), power(delta, n + 1)), dz); });
  let factorial = 1; for (let j = 1; j <= n; j++) factorial *= j;
  const fromCauchy = times(integral, [0, -factorial / TAU]), expected = name === 'exp' ? value(name, center) : n === 0 ? value(name, center) : n === 1 ? scale(center, 2) : n === 2 ? [2, 0] : [0, 0];
  fromCauchy.forEach((v, j) => near(v, expected[j], 2e-10));
  if (n === 1) vectorNear(lab.directionalModel({ directionalFn: name, pointRe: center[0], pointIm: center[1] }).derivative, fromCauchy); derivatives++;
}
for (const z of [[.25, 0], [0, .25], [.5, .25], [.25, .25]]) {
  const m = lab.directionalModel({ directionalFn: 'pathology', pointRe: z[0], pointIm: z[1], angle: 90, logStep: -3 }), h = 1e-6;
  const finiteDerivative = scale(minus(value('pathology', plus(z, [h, 0])), value('pathology', minus(z, [h, 0]))), .5 / h);
  assert.ok(mag(minus(cp(m.derivative), finiteDerivative)) <= 2e-5 * mag(finiteDerivative));
  const step = [0, .001], expectedQuotient = divide(minus(value('pathology', plus(z, step)), value('pathology', z)), step);
  assert.ok(mag(minus(cp(m.selected.value), expectedQuotient)) <= 2e-8 * mag(expectedQuotient));
  assert.equal(m.cr, true); assert.equal(m.holomorphic, true); derivatives++;
}
function winding(center, radius, pole, signed) {
  let total = 0, previous = Math.atan2(center[1] - pole[1], center[0] + radius - pole[0]);
  for (let j = 1; j <= 4096; j++) { const z = minus(circle(center, radius, signed * TAU * j / 4096), pole), angle = Math.atan2(z[1], z[0]); let delta = angle - previous; if (delta > PI) delta -= TAU; if (delta < -PI) delta += TAU; total += delta; previous = angle; }
  return Math.round(total / TAU) || 0;
}
for (const name of ['rational', 'laurent', 'poles', 'annulus-inverse', 'annulus-z']) for (const center of [[0, 0], [0, 1], [.5, .25], [2, 0]]) for (const radius of [.5, 1, 1.5, 2.5, 3]) for (const signed of [-2, -1, 1, 2]) {
  const raw = { contourFn: name, circleRe: center[0], circleIm: center[1], radius, winding: String(signed), residueA: -2, residueB: 2 }, m = lab.contourModel(raw);
  const expectedPoles = name === 'rational' ? [[0, 0], [2, 0]] : name === 'poles' ? [[0, 1], [0, -1]] : name === 'laurent' || name === 'annulus-inverse' ? [[0, 0]] : [];
  const onPath = expectedPoles.some(p => Math.abs(mag(minus(p, center)) - radius) < 1e-12);
  assert.equal(m.pathPole, onPath);
  if (onPath) { assert.equal(m.integral, null); assert.equal(m.numerical, null); }
  else {
    const direct = periodic(theta => { const delta = [radius * Math.cos(signed * theta), radius * Math.sin(signed * theta)]; return times(value(name, plus(center, delta), raw), times([0, signed], delta)); });
    vectorNear(m.integral, direct, 2e-8); vectorNear(m.numerical, direct, 2e-8);
    m.poles.forEach(p => assert.equal(p.winding, winding(center, radius, cp(p.z), signed)));
  }
  contours++;
}
const assessedLaurent = lab.contourModel({ contourFn: 'laurent', radius: 1, winding: '1' }); vectorNear(assessedLaurent.integral, [0, 10 * PI]); assert.equal(assessedLaurent.poles[0].order, 2);
vectorNear(lab.contourModel({ contourFn: 'poles', circleIm: 1, radius: .5 }).integral, [PI, 0]);
vectorNear(lab.contourModel({ contourFn: 'poles', radius: 2 }).integral, [0, 0]);
vectorNear(lab.contourModel({ contourFn: 'poles', circleIm: 1, radius: .5 }).poles[0].residue, [0, -.5]);
for (const raw of [{ contourFn: 'rational', circleRe: -1, circleIm: .25, radius: 3, winding: '2' }, { contourFn: 'poles', circleRe: .25, circleIm: -2, radius: 3, winding: '2' }]) {
  const m = lab.contourModel(raw), center = [raw.circleRe, raw.circleIm], direct = periodic(theta => { const delta = [3 * Math.cos(2 * theta), 3 * Math.sin(2 * theta)]; return times(value(raw.contourFn, plus(center, delta), { residueA: 1, residueB: 1 }), times([0, 2], delta)); }, 65536);
  vectorNear(m.numerical, direct, 1e-9); vectorNear(m.integral, direct, 1e-9); assert.ok(m.quadraturePanels > 1024 && m.quadratureResolved);
}
for (const eps of [1e-3, 1e-5]) { const poleLimit = times(value('poles', [eps, 1]), [eps, 0]); near(poleLimit[0], 0, eps); near(poleLimit[1], -.5, eps); }
const eps = 1e-5, laurentResidue = scale(minus(times(power([eps, 0], 2), value('laurent', [eps, 0])), times(power([-eps, 0], 2), value('laurent', [-eps, 0]))), .5 / eps); laurentResidue.forEach((v, j) => near(v, [5, 0][j], 1e-8));
for (let exponent = -4; exponent <= 5; exponent++) { const integral = periodic(theta => { const z = circle([0, 0], .75, theta); return times(power(z, exponent), times([0, 1], z)); }); integral.forEach((v, j) => near(v, exponent === -1 && j === 1 ? TAU : 0)); contours++; }
for (const radius of [.5, 1, 2, 3]) {
  const removed = lab.contourModel({ contourFn: 'rational', residueA: 0, residueB: 0, radius }); assert.equal(removed.poles.length, 0); assert.equal(removed.pathPole, false); vectorNear(removed.integral, [0, 0]);
}
assert.equal(lab.contourModel({ contourFn: 'annulus-inverse', radius: .25 }).contourInDomain, false);
assert.equal(lab.contourModel({ contourFn: 'annulus-inverse', radius: 1 }).contourInDomain, true);
for (const name of ['geometric', 'poles', 'exp']) for (const z of [[0, 0], [.25, .25], [-.5, .25], [.75, 0], [1.25, .5], [1, 0], [0, 1]]) for (const terms of [1, 2, 6, 15, 24]) {
  const m = lab.taylorModel({ taylorFn: name, pointRe: z[0], pointIm: z[1], terms });
  assert.equal(m.radius, name === 'exp' ? Infinity : 1); assert.equal(m.valid, mag(z) < m.radius);
  const r = .5;
  for (let j = 0; j <= Math.min(terms, 6); j++) { const coeff = scale(periodic(theta => { const delta = circle([0, 0], r, theta); return divide(value(name, delta), power(delta, j)); }), 1 / TAU); near(m.coefficients[j], coeff[0], 2e-9); near(coeff[1], 0, 2e-9); }
  if (m.probe.value) { const actualError = minus(value(name, z), cp(m.partial)); vectorNear(m.error, actualError, 1e-8); if (m.exactRemainder) vectorNear(m.exactRemainder, actualError, 1e-8);
    if (m.valid) assert.ok(mag(actualError) <= m.remainderBound + 2e-12 * Math.max(1, mag(value(name, z)))); }
  if (!m.valid) assert.equal(m.remainderBound, null); taylors++;
}
// Endpoint witnesses independent of the runtime inference. Geometric series
// Σ(z/R)^n converges throughout |z|<2 for R=2,2.5,3, and diverges at z=3.
for (const R of [2, 2.5, 3]) {
  const m = lab.taylorModel({ inferenceRadius: String(R) }); assert.deepEqual(m.inference, { lower: 2, upper: 3, selected: R, endpointsAllowed: true, boundaryDetermined: false });
  assert.ok(1.999 / R < 1); assert.ok(3 / R >= 1); taylors++;
}
for (const name of ['z2', 'exp', 'constant', 'abs2', 'peak', 'geometric']) for (const center of [[0, 0], [.25, .25], [-1, .5], [1, 0]]) for (const radius of [.25, .5, 1, 2]) {
  const m = lab.meanModel({ meanFn: name, circleRe: center[0], circleIm: center[1], radius }), distance = mag(minus(center, [1, 0]));
  assert.equal(m.pathPole, name === 'geometric' && Math.abs(distance - radius) < 1e-12); assert.equal(m.meanEquality, !['abs2', 'peak'].includes(name) && (name !== 'geometric' || distance > radius));
  if (!m.pathPole) {
    const complexMean = scale(periodic(theta => value(name, circle(center, radius, theta)), 8192), 1 / TAU), modulusMean = scale(periodic(theta => [mag(value(name, circle(center, radius, theta))), 0], 8192), 1 / TAU)[0];
    vectorNear(m.mean, complexMean, 2e-8); vectorNear(m.numericMean, complexMean, 2e-8); near(m.modulusMean, modulusMean, 2e-6);
    if (m.meanEquality) vectorNear(m.mean, value(name, center), 2e-8);
    const sampledMaximum = Math.max(...Array.from({ length: 65536 }, (_, j) => mag(value(name, circle(center, radius, TAU * j / 65536))))); near(m.maxModulus, sampledMaximum, 2e-6);
  } else { assert.equal(m.mean, null); assert.equal(m.modulusMean, null); }
  means++;
}
vectorNear(lab.meanModel({ meanFn: 'z2', radius: 1 }).mean, [0, 0]); near(lab.meanModel({ meanFn: 'z2', radius: 1 }).modulusMean, 1);
near(lab.meanModel({ meanFn: 'constant' }).modulusMean, 1); assert.equal(lab.meanModel({ meanFn: 'constant' }).constantEquality, true);
near(lab.meanModel({ meanFn: 'abs2', radius: 1 }).mean.re, 1); assert.equal(lab.meanModel({ meanFn: 'abs2' }).meanEquality, false);
near(lab.meanModel({ meanFn: 'peak', radius: .25 }).probe.value.re, 1); assert.ok(lab.meanModel({ meanFn: 'peak', radius: .25 }).maxModulus < 1);
const nearPoleMean = lab.meanModel({ meanFn: 'geometric', circleRe: -2, circleIm: .25, radius: 3 });
vectorNear(nearPoleMean.numericMean, scale(periodic(theta => value('geometric', circle([-2, .25], 3, theta)), 65536), 1 / TAU), 1e-9);
assert.match(lab.build({ station: 'C1', directionalFn: 'pathology', pointIm: .25, angle: 90 }).readout, /e-108i/); // Tiny nonzero derivative must not become zero.
assert.match(lab.build({ station: 'C1', directionalFn: 'pathology', angle: 0, logStep: -1 }).readout, /underflow: nonzero/);
for (const coefficients of [[[1, 0], [1, 0]], [[1, -1], [-2, 0], [0, 1], [1, 0]], [[3, 2], [-5, 1], [.5, -.25]]]) {
  const ledger = lab.polynomialExterior(coefficients.map(object)), R0 = Math.max(1, 2 * coefficients.slice(0, -1).reduce((s, c) => s + mag(c), 0) / mag(coefficients.at(-1)));
  near(ledger.radius, R0);
  for (const ratio of [1, 1.1, 2, 5]) for (let j = 0; j < 64; j++) { const z = circle([0, 0], R0 * ratio, TAU * j / 64), p = coefficients.reduce((sum, c, n) => plus(sum, times(c, power(z, n))), [0, 0]), lower = mag(coefficients.at(-1)) * mag(z) ** (coefficients.length - 1) / 2; assert.ok(mag(p) >= lower * (1 - 1e-12)); proofs++; }
}
for (const count of [1, 2, 3, 4, 5, 6]) { const m = lab.liouvilleModel({ proofStep: String(count) }), prior = new Set(); m.steps.forEach(step => { step.requires.forEach(id => assert.ok(prior.has(id), `${step.id} missing prerequisite ${id}`)); prior.add(step.id); }); assert.equal(m.steps.length, count); }
const complete = lab.liouvilleModel({ proofStep: '6' }); assert.match(complete.steps[2].text, /aₙ.*Σ/); assert.match(complete.steps[3].text, /compact.*GLOBAL/); assert.match(complete.steps[5].text, /never 0.*Contradiction/);
for (const name of ['constant', 'linear', 'exp']) { const small = lab.liouvilleModel({ growthFn: name, growthRadius: 1 }), large = lab.liouvilleModel({ growthFn: name, growthRadius: 12 }); assert.equal(small.globalBounded, name === 'constant'); near(large.hypotheticalCauchyBound / small.hypotheticalCauchyBound, 1 / 12); if (name !== 'constant') assert.ok(large.diskMaximum > small.diskMaximum); }
function factor(name, z, a) { return name === 'one' ? [1, 0] : name === 'linear' ? divide([1, 0], plus(z, [0, a])) : divide([1, 0], plus(times(z, z), [a * a, 0])); }
for (const name of ['one', 'linear', 'quadratic']) for (const k of [-2, -.5, 0, .5, 2]) for (const halfPlane of ['upper', 'lower']) for (const R of [2, 3, 8]) for (const a of [.5, 1.5]) {
  const m = lab.jordanModel({ arcFn: name, k, halfPlane, arcRadius: R, poleA: a }), sign = halfPlane === 'upper' ? 1 : -1;
  const integrand = z => times(exponential(times([0, k], z)), factor(name, z, a));
  // Dense midpoint quadrature independently parameterizes clockwise lower arc.
  const segment = midpoint(x => integrand([x, 0]), -R, R, 32768), arc = midpoint(theta => { const z = circle([0, 0], R, sign * theta); return times(integrand(z), times([0, sign], z)); }, 0, PI, 32768);
  vectorNear(m.realIntegral, segment, 2e-7); vectorNear(m.arcIntegral, arc, 1e-6); vectorNear(m.directArc, arc, 1e-6); vectorNear(m.closedIntegral, plus(segment, arc), 1e-6);
  const samples = Array.from({ length: 2049 }, (_, j) => mag(factor(name, circle([0, 0], R, sign * PI * j / 2048), a))); near(m.factorSupremum, Math.max(...samples), 2e-9);
  const matching = k * sign > 0; assert.equal(m.matching, matching); assert.equal(m.certificate, matching && name !== 'one');
  if (matching) { near(m.jordanBound, PI * Math.max(...samples) / Math.abs(k)); assert.ok(mag(arc) <= m.jordanBound + 1e-6); } else assert.equal(m.jordanBound, null);
  if (name === 'one') vectorNear(m.arcIntegral, [k === 0 ? -2 * R : -2 * Math.sin(k * R) / k, 0]);
  m.samples.forEach(p => near(p.expLogAbs, -k * p.z.im)); arcs++;
}
// No-decay subsequences for g=1: R=(π/2+2πn)/k yields arc −2/k.
for (let j = 1; j <= 6; j++) near(-2 * Math.sin(PI / 2 + TAU * j), -2);
for (const control of lab.controls) for (const bad of [undefined, null, NaN, Infinity, -Infinity, {}, '', 'invalid']) assert.equal(lab.normalize({ [control.key]: bad })[control.key], lab.initial[control.key]);
assert.throws(() => lab.evaluate('arbitrary', { re: 0, im: 0 }), RangeError); assert.throws(() => lab.evaluate('exp', { re: Infinity, im: 0 }), RangeError);
assert.throws(() => lab.circlePoints({ re: 0, im: 0 }, 0), RangeError); assert.throws(() => lab.polynomialExterior([{ re: 1, im: 0 }, { re: 0, im: 0 }]), RangeError);

class Text { constructor(value) { this.nodeType = 3; this.textContent = String(value); } }
class Element {
  constructor(tag) { this.nodeType = 1; this.tagName = tag; this.attributes = {}; this.children = []; this.events = {}; this.classList = { toggle: (name, force) => { const values = new Set((this.attributes.class || '').split(/\s+/).filter(Boolean)); const next = force === undefined ? !values.has(name) : force; if (next) values.add(name); else values.delete(name); this.attributes.class = [...values].join(' '); return next; } }; }
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
globalThis.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag), createTextNode: value => new Text(value) };
const scenario = 'math.5.complex-analysis.holomorphy-contours';
assert.equal(lab.render({ props: { scenario: 'math.5.complex-analysis' } }), null); assert.equal(lab.render({ props: { scenario, arbitrary: true } }), null); assert.equal(lab.render({ renderer: 'other', props: { scenario } }), null);
let speech;
const root = lab.render({ renderer: 'math-complex-lab', props: { scenario } }, { speakButton: provider => { speech = provider; return new Element('button'); } });
const all = () => root.all(), inputFor = key => all().find(e => e.attributes['data-complex-control'] === key), action = key => all().find(e => e.attributes['data-complex-action'] === key), state = () => JSON.parse(root.attributes['data-complex-state']);
function mounted() {
  const elements = all(), s = state(); assert.equal(elements.filter(e => e.tagName === 'svg').length, 2); assert.equal(elements.filter(e => e.tagName === 'table').length, 1);
  assert.match(speech(), new RegExp(s.station)); assert.match(speech(), /finite plot or sampled directions/);
  for (const e of elements) for (const [key, attr] of Object.entries(e.attributes)) {
    assert.doesNotMatch(attr, /NaN|Infinity/);
    if (key === 'points') for (const coordinate of attr.split(' ').map(p => p.split(',').map(Number))) { assert.equal(coordinate.length, 2); assert.ok(coordinate[0] >= -1 && coordinate[0] <= 481 && coordinate[1] >= -1 && coordinate[1] <= 341, 'SVG point outside view box: ' + attr); }
    if (['cx', 'x'].includes(key)) assert.ok(Number(attr) >= -1 && Number(attr) <= 481);
    if (['cy', 'y'].includes(key)) assert.ok(Number(attr) >= -1 && Number(attr) <= 341);
  }
  for (const c of lab.controls) { const input = inputFor(c.key), label = elements.find(e => e.tagName === 'label' && e.attributes.for === input.attributes.id), hidden = c.stations && !c.stations.includes(s.station) || c.presets && !c.presets.includes(s.contourFn); assert.equal(Boolean(label.hidden), Boolean(hidden)); assert.equal(Boolean(input.disabled), Boolean(hidden)); }
  if (s.station === 'C2' || s.station === 'C5') {
    const center = [s.circleRe, s.circleIm], radius = s.radius, name = s.station === 'C2' ? s.contourFn : s.meanFn, poles = s.station === 'C2' ? name === 'poles' ? [[0, 1], [0, -1]] : name === 'rational' ? [[0, 0], [2, 0]].filter((p, j) => [s.residueA, s.residueB][j] !== 0) : name === 'laurent' || name === 'annulus-inverse' ? [[0, 0]] : [] : name === 'geometric' ? [[1, 0]] : [];
    const bound = Math.max(1, mag(center) + radius, name.startsWith('annulus') ? 4.5 : 0, ...poles.map(mag)) * 1.25, curve = elements.find(e => e.attributes['data-complex-circle'] === s.station), actual = curve.attributes.points.split(' ').map(p => p.split(',').map(Number));
    const signed = s.station === 'C2' ? Number(s.winding) : 1;
    actual.forEach((p, j) => { const z = circle(center, radius, signed * TAU * j / 128); near(p[0], 250 + 110 * z[0] / bound); near(p[1], 183 - 110 * z[1] / bound); });
    if (poles.some(p => Math.abs(mag(minus(center, p)) - radius) < 1e-12)) assert.equal(elements.filter(e => e.attributes['data-complex-output'] === 'curve').length, 0, 'A path-pole trace must not bridge the singularity.');
  }
  if (s.station === 'C6') { const curve = elements.find(e => e.attributes['data-complex-arc']), actual = curve.attributes.points.split(' ').map(p => p.split(',').map(Number)), sign = s.halfPlane === 'upper' ? 1 : -1; actual.forEach((p, j) => { const z = circle([0, 0], s.arcRadius, sign * PI * j / 96); near(p[0], 250 + 110 * z[0] / (s.arcRadius * 1.2)); near(p[1], 183 - 110 * z[1] / (s.arcRadius * 1.2)); }); }
}
let mountedControls = 0;
for (const control of lab.controls) {
  inputFor('station').value = control.stations ? control.stations[0] : 'C1'; inputFor('station').fire('change');
  if (control.presets) { inputFor('contourFn').value = control.presets[0]; inputFor('contourFn').fire('change'); }
  const values = control.options ? control.options.map(o => o.value) : [control.min, control.max];
  for (const v of values) { inputFor(control.key).value = String(v); inputFor(control.key).fire('change'); mounted(); mountedControls++; }
  action('reset').fire('click'); assert.deepEqual(state(), lab.initial);
}
for (const preset of ['abszero', 'pathology', 'laurent', 'imagpole', 'pathpole', 'inference', 'fta', 'mean', 'jordan', 'counterexample']) { action(preset).fire('click'); mounted(); }
action('abszero').fire('click'); assert.match(root.textContent, /Pointwise complex derivative exists: 0/); assert.match(root.textContent, /Holomorphic on no open neighborhood/);
action('pathology').fire('click'); assert.match(root.textContent, /discontinuous at 0/); assert.match(root.textContent, /CR hold/);
action('pathpole').fire('click'); assert.match(root.textContent, /UNDEFINED/);
action('fta').fire('click'); assert.equal(all().filter(e => e.attributes['data-complex-proof-step']).length, 6);
action('counterexample').fire('click'); assert.match(speech(), /g=1 is a counterexample/);
action('reset').fire('click'); const draft = inputFor('pointRe'); draft.value = '.37'; draft.fire('input'); assert.equal(draft.value, '.37'); assert.equal(state().pointRe, 0); draft.fire('blur'); assert.equal(state().pointRe, .25); assert.equal(draft.value, '0.25');
draft.value = ''; draft.fire('blur'); assert.equal(state().pointRe, 0); draft.value = '1e100'; draft.fire('blur'); assert.equal(state().pointRe, 2);
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true'); action('reset').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'false'); assert.deepEqual(state(), lab.initial); mounted();
const second = lab.render({ props: { scenario } }); assert.notEqual(root.attributes['aria-labelledby'], second.attributes['aria-labelledby']);
// Two live views share a complete normalized state by exact lesson key. The
// real bus excludes the source; peer setters suppress publication and echoes.
const shared = require('../web/lesson-state.js'), joined = [], published = [];
globalThis.window = { PrimerLessonStateBus: { join: (key, view, receive) => { joined.push(key); shared.join(key, view, receive); }, publish: (key, view, values) => { published.push({ key, view, values }); shared.publish(key, view, values); } } };
const complexA = lab.render({ props: { scenario } }), complexB = lab.render({ props: { scenario } });
const quantum = require('../web/physics-quantum-lab.js'), quantumA = quantum.render({ props: { scenario: quantum.SCENARIO } }), quantumB = quantum.render({ props: { scenario: quantum.SCENARIO } });
const sharedState = (view, kind) => JSON.parse(view.attributes[kind === 'complex' ? 'data-complex-state' : 'data-quantum-state']);
assert.deepEqual(joined, ['math.5.complex-analysis', 'math.5.complex-analysis', 'phys.4.quantum', 'phys.4.quantum']); assert.equal(published.length, 0, 'Mounting never publishes or replays stale state.');
complexA.setModelState({ station: 'C2', contourFn: 'poles', circleIm: 1, radius: .5 });
assert.equal(published.length, 1); assert.equal(published[0].key, 'math.5.complex-analysis'); assert.deepEqual(sharedState(complexA, 'complex'), sharedState(complexB, 'complex')); assert.deepEqual(sharedState(quantumA, 'quantum'), quantum.initial);
complexB.setModelState({ angle: 90 }, false, true); assert.equal(published.length, 1, 'Peer reception never echoes.');
complexA.all().find(e => e.attributes['data-complex-action'] === 'pathology').fire('click'); assert.equal(published.length, 2); assert.equal(sharedState(complexB, 'complex').directionalFn, 'pathology');
quantumA.setModelState({ mode: 'photon', wavelengthNm: 500 }); assert.equal(published.length, 3); assert.equal(published[2].key, 'phys.4.quantum'); assert.deepEqual(sharedState(quantumA, 'quantum'), sharedState(quantumB, 'quantum')); assert.equal(sharedState(complexA, 'complex').station, 'C1');
const wavelength = quantumB.all().find(e => e.attributes['data-quantum-control'] === 'wavelengthNm'); wavelength.value = '1000'; wavelength.fire('input'); assert.equal(published.length, 4, 'Unannounced user range input still publishes once.'); assert.equal(sharedState(quantumA, 'quantum').wavelengthNm, 1000);
quantumA.all().find(e => e.attributes['data-quantum-action'] === 'reset').fire('click'); assert.equal(published.length, 5); assert.deepEqual(sharedState(quantumB, 'quantum'), quantum.initial);
complexA.all().find(e => e.attributes['data-complex-action'] === 'reset').fire('click'); assert.equal(published.length, 6); assert.deepEqual(sharedState(complexB, 'complex'), lab.initial);
complexB.isConnected = false; complexA.setModelState({ angle: 30 }); assert.equal(sharedState(complexB, 'complex').angle, 45, 'Disconnected views are pruned.');
delete globalThis.window;
console.log(`Verified ${derivatives} independent derivative/CR/Cauchy states, ${contours} contour quadrature/winding states, ${taylors} Taylor/coefficient states, ${means} mean/max states, ${arcs} Jordan arc states, ${proofs} polynomial exterior inequalities and ${mountedControls} mounted controls; all six stations, hypotheses, complex residues, endpoint inference, proof dependencies, safe logs, path-pole omissions, drafts, blur, geometry and exact resets passed.`);
console.log('Two views per lesson share full normalized state without source echo, peer echo, mounting replay, cross-lesson delivery or disconnected-view updates.');

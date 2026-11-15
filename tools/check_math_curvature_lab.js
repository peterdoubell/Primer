#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/math-curvature-lab.js');
const PI = Math.PI, TAU = 2 * PI;
const dot = (a, b) => a.reduce((sum, x, i) => sum + x * b[i], 0);
const add = (a, b) => a.map((x, i) => x + b[i]);
const sub = (a, b) => a.map((x, i) => x - b[i]);
const scale = (a, x) => a.map(v => v * x);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = a => Math.hypot(...a);
const near = (actual, expected, tolerance = 2e-10) => assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
const vectorNear = (a, b, tolerance) => a.forEach((x, i) => near(x, b[i], tolerance));
const relative = (actual, expected, tolerance = 1e-12) => assert.ok(Math.abs(actual - expected) <= tolerance * Math.abs(expected), `${actual} != ${expected} relatively`);

// Independent geometric oracle: differentiate an independently written
// embedding, then compute both forms by Euclidean inner products. No runtime
// derivative, normal, curvature or integral supplies these expected values.
function embedding(kind, p, u, v) {
  if (kind === 'plane') return [u, v, 0];
  if (kind === 'cylinder') return [p.radius * Math.cos(u), p.radius * Math.sin(u), v];
  if (kind === 'sphere') return [p.radius * Math.cos(v) * Math.cos(u), p.radius * Math.cos(v) * Math.sin(u), p.radius * Math.sin(v)];
  const a = p.major + p.radius * Math.cos(v);
  return [a * Math.cos(u), a * Math.sin(u), p.radius * Math.sin(v)];
}
let surfaces = 0, integrals = 0, transports = 0;
for (const kind of ['plane', 'cylinder', 'sphere', 'torus']) for (const radius of [.5, 1, 2])
  for (const major of [3, 6]) for (const u of [-2.4, -.7, 0, 1.2, 2.8]) for (const v of [-1.3, -.4, 0, .8, 1.4]) for (const normalSign of [-1, 1]) {
    const p = { u, v, radius, major, normalSign }, m = lab.surfaceAt(kind, p);
    const h = 1e-5, h2 = 1e-3, X = embedding(kind, p, u, v);
    const Xu = scale(sub(embedding(kind, p, u + h, v), embedding(kind, p, u - h, v)), .5 / h);
    const Xv = scale(sub(embedding(kind, p, u, v + h), embedding(kind, p, u, v - h)), .5 / h);
    const Xuu = scale(sub(add(embedding(kind, p, u + h2, v), embedding(kind, p, u - h2, v)), scale(X, 2)), 1 / (h2 * h2));
    const Xvv = scale(sub(add(embedding(kind, p, u, v + h2), embedding(kind, p, u, v - h2)), scale(X, 2)), 1 / (h2 * h2));
    const Xuv = scale(sub(sub(embedding(kind, p, u + h2, v + h2), embedding(kind, p, u + h2, v - h2)), sub(embedding(kind, p, u - h2, v + h2), embedding(kind, p, u - h2, v - h2))), 1 / (4 * h2 * h2));
    const rawNormal = cross(Xu, Xv), n = scale(rawNormal, normalSign / norm(rawNormal));
    const E = dot(Xu, Xu), F = dot(Xu, Xv), G = dot(Xv, Xv), e = dot(n, Xuu), f = dot(n, Xuv), g = dot(n, Xvv);
    vectorNear(m.point, X); vectorNear(m.Xu, Xu, 2e-9); vectorNear(m.Xv, Xv, 2e-9); vectorNear(m.normal, n, 2e-9);
    near(m.metric.E, E, 2e-9); near(m.metric.F, F, 2e-9); near(m.metric.G, G, 2e-9);
    near(m.areaElement, Math.sqrt(E * G - F * F), 2e-9);
    near(m.secondForm.e, e, 2e-7); near(m.secondForm.f, f, 2e-7); near(m.secondForm.g, g, 2e-7);
    near(m.gaussian, (e * g - f * f) / (E * G - F * F), 7e-7);
    near(m.principal[0], e / E, 7e-7); near(m.principal[1], g / G, 7e-7);
    const reverse = lab.surfaceAt(kind, { ...p, normalSign: -normalSign });
    assert.deepEqual(reverse.metric, m.metric); near(reverse.areaElement, m.areaElement); near(reverse.gaussian, m.gaussian);
    vectorNear(reverse.normal, scale(m.normal, -1)); vectorNear(reverse.principal, scale(m.principal, -1));
    m.principalDirections.forEach(direction => { near(norm(direction), 1); near(dot(direction, m.normal), 0); });
    surfaces++;
  }

// Composite Simpson quadrature samples the geometric metric and shape operator
// densities directly. Torus sign regions are independently split at cos(v)=0.
function simpson(fn, a, b, n = 512) {
  if (a === b) return 0;
  const h = (b - a) / n;
  let sum = fn(a) + fn(b);
  for (let i = 1; i < n; i++) sum += (i % 2 ? 4 : 2) * fn(a + i * h);
  return sum * h / 3;
}
for (const kind of ['plane', 'cylinder', 'sphere', 'torus']) for (const radius of [.5, 1.25, 2]) for (const major of [3, 6])
  for (const range of [[-.8, .2], [-PI / 2, PI / 2], [0, .7], [.3, .3]]) {
    const p = { radius, major }, [v0, v1] = range, patch = { u0: -1.2, u1: 1.4, v0, v1 }, du = patch.u1 - patch.u0;
    const metricDensity = v => kind === 'plane' ? 1 : kind === 'cylinder' ? radius : kind === 'sphere' ? radius ** 2 * Math.cos(v) : radius * (major + radius * Math.cos(v));
    const curvatureDensity = v => ['plane', 'cylinder'].includes(kind) ? 0 : Math.cos(v);
    const m = lab.patchIntegral(kind, p, patch);
    near(m.area, du * simpson(metricDensity, v0, v1), 2e-10); near(m.curvatureIntegral, du * simpson(curvatureDensity, v0, v1), 2e-10);
    near(m.positive + m.negative, m.curvatureIntegral); near(m.absolute, m.positive - m.negative);
    integrals++;
  }
for (const range of [[-PI, PI], [-PI, -PI / 2], [-PI / 2, PI / 2], [PI / 2, PI], [0, TAU], [.1, 5.8], [1.3, 1.9]]) {
  const [v0, v1] = range, du = 1.7, p = { radius: 1.2, major: 3.5 }, m = lab.patchIntegral('torus', p, { u0: 0, u1: du, v0, v1 });
  const split = [v0, v1];
  for (let q = -6; q <= 6; q++) if (PI / 2 + q * PI > v0 && PI / 2 + q * PI < v1) split.push(PI / 2 + q * PI);
  split.sort((a, b) => a - b);
  let positive = 0, negative = 0;
  for (let j = 1; j < split.length; j++) {
    const value = du * simpson(v => Math.cos(v), split[j - 1], split[j]);
    if (Math.cos((split[j - 1] + split[j]) / 2) > 0) positive += value; else negative += value;
  }
  near(m.positive, positive); near(m.negative, negative); near(m.curvatureIntegral, positive + negative); integrals++;
}
const full = lab.patchIntegral('torus', { radius: 1, major: 3 }, { u0: -PI, u1: PI, v0: -PI, v1: PI });
assert.equal(full.curvatureIntegral, 0); assert.equal(full.positive, 4 * PI); assert.equal(full.negative, -4 * PI); assert.equal(full.positive + full.negative, 0);
near(full.area, 12 * PI * PI);
const closedSphere = lab.build({ surface: 'sphere', radius: 2 }); near(closedSphere.fullIntegral.curvatureIntegral, 4 * PI); near(closedSphere.fullIntegral.area, 16 * PI);
for (const delta of [1e-5, 1e-9, 1e-12, 1e-15, Number.EPSILON]) {
  const a = PI / 2 - delta, representedDistance = PI / 2 - a;
  const thin = lab.patchIntegral('sphere', { radius: 2, major: 3 }, { u0: 0, u1: .7, v0: a, v1: PI / 2 });
  const expected = .7 * 2 * Math.sin(representedDistance / 2) ** 2;
  assert.ok(thin.area > 0 && thin.curvatureIntegral > 0); relative(thin.curvatureIntegral, expected); relative(thin.area, 4 * expected);
  const local = lab.surfaceAt('sphere', { radius: 2, major: 3, u: .2, v: a });
  assert.ok(local.regular && local.metric.E > 0 && local.areaElement > 0); local.principalDirections.forEach(d => near(norm(d), 1));
  const ring = lab.surfaceAt('torus', { radius: 1, major: 3, u: .2, v: a }); assert.ok(ring.gaussian > 0);
  assert.ok(lab.surfaceAt('torus', { radius: 1, major: 3, u: .2, v: PI / 2 + delta }).gaussian < 0);
}
const poleInner0 = PI / 2 - 3 * Number.EPSILON, poleInner1 = PI / 2 - Number.EPSILON;
const betweenNearPoles = lab.patchIntegral('sphere', { radius: 1, major: 3 }, { u0: 0, u1: 1, v0: poleInner0, v1: poleInner1 });
relative(betweenNearPoles.curvatureIntegral, 2 * Math.sin(((PI / 2 - poleInner0) + (PI / 2 - poleInner1)) / 2) * Math.sin((poleInner1 - poleInner0) / 2));
const nearlyZero = lab.patchIntegral('torus', { radius: 1, major: 3 }, { u0: 0, u1: 1e-12, v0: -1e-15, v1: 1e-15 });
assert.ok(nearlyZero.area > 0 && nearlyZero.curvatureIntegral > 0); relative(nearlyZero.curvatureIntegral, 2e-12 * Math.sin(1e-15));
for (const v of [-PI / 2, PI / 2]) {
  const pole = lab.surfaceAt('sphere', { radius: 2, major: 3, u: 1, v });
  assert.equal(pole.regular, false); assert.equal(pole.metric.E, 0); assert.equal(pole.areaElement, 0); assert.equal(pole.principalDirections, null); near(pole.gaussian, .25);
  assert.equal(lab.surfaceAt('torus', { radius: 1, major: 3, u: .2, v }).gaussian, 0);
}
for (const kind of ['cylinder', 'sphere', 'torus']) {
  const p = { radius: 1.25, major: 3, v: .4 };
  const left = lab.surfaceAt(kind, { ...p, u: -PI }), right = lab.surfaceAt(kind, { ...p, u: PI });
  assert.deepEqual(left.point, right.point); assert.deepEqual(left.normal, right.normal); assert.deepEqual(left.metric, right.metric);
}

// Independent great-circle transport uses the closed-form tangent map between
// points: w = v - (v·q)/(1+p·q) (p+q). It is not Rodrigues rotation.
function parallelMap(v, p, q) { return sub(v, scale(add(p, q), dot(v, q) / (1 + dot(p, q)))); }
for (const direction of ['positive', 'negative']) for (const normal of ['outward', 'inward']) for (const radius of [.5, 1, 2])
  for (const startAngle of [0, 45, 90, 165, 270, 360]) for (const vectorLength of [0, .25, 1, 2]) for (const leg of ['0', '1', '2']) for (const progress of [0, 17, 50, 83, 100]) {
    const raw = { direction, normal, radius, startAngle, vectorLength, leg, progress }, t = lab.transportOctant(raw);
    const A = [1, 0, 0], B = [0, 1, 0], C = [0, 0, 1], vertices = direction === 'positive' ? [A, B, C, A] : [A, C, B, A];
    const beta = startAngle * PI / 180, initial = [0, vectorLength * Math.cos(beta), vectorLength * Math.sin(beta)];
    let current = initial;
    for (let j = 0; j < 3; j++) {
      vectorNear(t.legs[j].startVector, current);
      const next = parallelMap(current, vertices[j], vertices[j + 1]); vectorNear(t.legs[j].endVector, next); current = next;
    }
    const j = Number(leg), theta = progress * PI / 200;
    const position = add(scale(vertices[j], Math.cos(theta)), scale(vertices[j + 1], Math.sin(theta)));
    const atLeg = t.legs[j].startVector, expectedVector = parallelMap(atLeg, vertices[j], position);
    vectorNear(t.unitPoint, position); vectorNear(t.point, scale(position, radius)); vectorNear(t.tangent, expectedVector);
    vectorNear(t.geodesicVelocity, scale(add(scale(vertices[j], -Math.sin(theta)), scale(vertices[j + 1], Math.cos(theta))), radius));
    const derivativeStep = 1e-5;
    const vectorAt = angle => parallelMap(atLeg, vertices[j], add(scale(vertices[j], Math.cos(angle)), scale(vertices[j + 1], Math.sin(angle))));
    const numericalDerivative = scale(sub(vectorAt(theta + derivativeStep), vectorAt(theta - derivativeStep)), .5 / derivativeStep);
    vectorNear(t.vectorDerivative, numericalDerivative, 3e-9);
    near(norm(t.point), radius); near(norm(t.tangent), vectorLength); near(dot(t.unitPoint, t.tangent), 0);
    near(dot(t.unitPoint, t.geodesicVelocity), 0); near(norm(t.geodesicVelocity), radius);
    const projectedDerivative = sub(t.vectorDerivative, scale(t.unitPoint, dot(t.vectorDerivative, t.unitPoint)));
    vectorNear(projectedDerivative, [0, 0, 0]);
    vectorNear(sub(numericalDerivative, scale(position, dot(numericalDerivative, position))), [0, 0, 0], 3e-9);
    vectorNear(t.finalVector, direction === 'positive' ? [0, -initial[2], initial[1]] : [0, initial[2], -initial[1]]);
    const angle = (direction === 'positive' ? 1 : -1) * (normal === 'outward' ? 1 : -1) * PI / 2;
    near(t.expectedHolonomy, angle); near(t.octantArea, radius * radius * PI / 2); near(t.curvatureIntegral, PI / 2);
    if (vectorLength === 0) assert.equal(t.measuredHolonomy, null); else near(t.measuredHolonomy, angle);
    const flipped = lab.transportOctant({ ...raw, normal: normal === 'outward' ? 'inward' : 'outward' });
    assert.deepEqual(flipped.initialVector, t.initialVector); assert.deepEqual(flipped.finalVector, t.finalVector); assert.deepEqual(flipped.tangent, t.tangent); assert.deepEqual(flipped.point, t.point);
    transports++;
  }
for (const kind of ['plane', 'cylinder', 'sphere', 'torus']) for (const coverage of [0, 5, 50, 100]) {
  const m = lab.build({ surface: kind, coverage }); assert.equal(JSON.stringify(m), JSON.stringify(lab.build({ surface: kind, coverage })));
  if (coverage === 0) { assert.equal(m.integral.area, 0); assert.equal(m.integral.curvatureIntegral, 0); }
}
for (const control of lab.controls) for (const bad of [undefined, null, NaN, Infinity, -Infinity, {}, '', 'invalid']) assert.equal(lab.normalize({ [control.key]: bad })[control.key], lab.initial[control.key]);
assert.throws(() => lab.surfaceAt('sphere', { u: 0, v: PI / 2 + Number.EPSILON, radius: 1, major: 3 }), RangeError);
assert.throws(() => lab.surfaceAt('torus', { u: 0, v: 0, radius: 1, major: 1 }), RangeError);
assert.throws(() => lab.patchIntegral('torus', { radius: 1, major: 3 }, { u0: 0, u1: TAU + .1, v0: 0, v1: 1 }), RangeError);
assert.throws(() => lab.patchIntegral('sphere', { radius: 1, major: 3 }, { u0: 0, u1: 1, v0: -2, v1: 1 }), RangeError);

class Text { constructor(value) { this.nodeType = 3; this.textContent = String(value); } }
class Element {
  constructor(tag) { this.nodeType = 1; this.tagName = tag; this.attributes = {}; this.children = []; this.events = {};
    this.classList = { toggle: (name, force) => { const values = new Set((this.attributes.class || '').split(/\s+/).filter(Boolean)); const next = force === undefined ? !values.has(name) : force; if (next) values.add(name); else values.delete(name); this.attributes.class = [...values].join(' '); return next; } }; }
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
const scenario = 'math.5.diffgeo.curvature-transport';
assert.equal(lab.render({ props: { scenario: 'math.5.diffgeo' } }), null);
assert.equal(lab.render({ props: { scenario, arbitrary: true } }), null);
assert.equal(lab.render({ renderer: 'other', props: { scenario } }), null);
let speech;
const root = lab.render({ renderer: 'math-curvature-lab', props: { scenario } }, { speakButton: provider => { speech = provider; return new Element('button'); } });
const all = () => root.all(), inputFor = key => all().find(e => e.attributes['data-curvature-control'] === key), action = key => all().find(e => e.attributes['data-curvature-action'] === key);
const state = () => JSON.parse(root.attributes['data-curvature-state']), original = state();
function mounted() {
  const elements = all(); assert.equal(elements.filter(e => e.tagName === 'svg').length, 3);
  assert.equal(elements.filter(e => e.attributes['data-curvature-geodesic'] !== undefined).length, 3);
  for (const e of elements) for (const value of Object.values(e.attributes)) assert.doesNotMatch(value, /NaN|Infinity/);
  assert.match(speech(), /principal curvatures/); assert.match(speech(), /zero tangent vector/);
  const s = state(), A = [1, 0, 0], B = [0, 1, 0], C = [0, 0, 1];
  const vertices = s.direction === 'positive' ? [A, B, C, A] : [A, C, B, A], j = Number(s.leg), angle = s.progress * PI / 200;
  let carried = [0, s.vectorLength * Math.cos(s.startAngle * PI / 180), s.vectorLength * Math.sin(s.startAngle * PI / 180)];
  for (let k = 0; k < j; k++) carried = parallelMap(carried, vertices[k], vertices[k + 1]);
  const unitPoint = add(scale(vertices[j], Math.cos(angle)), scale(vertices[j + 1], Math.sin(angle))), tangent = parallelMap(carried, vertices[j], unitPoint);
  const gain = .32, cameraScale = 132 / Math.hypot(s.radius, gain * s.vectorLength);
  const projection = p => [220 + cameraScale * (Math.sqrt(3) * p[0] / 2 + p[1] / 2), 187 - cameraScale * (Math.cos(PI / 7) * p[2] + Math.sin(PI / 7) * (-p[0] / 2 + Math.sqrt(3) * p[1] / 2))];
  elements.filter(e => e.attributes['data-curvature-geodesic'] !== undefined).forEach(e => {
    const edge = Number(e.attributes['data-curvature-geodesic']), points = e.attributes.points.split(' ').map(point => point.split(',').map(Number));
    assert.equal(points.length, 33);
    points.forEach((point, k) => {
      assert.equal(point.length, 2, 'SVG points must contain x/y pairs, excluding camera depth.');
      const theta = k * PI / 64, expected = scale(add(scale(vertices[edge], Math.cos(theta)), scale(vertices[edge + 1], Math.sin(theta))), s.radius);
      vectorNear(point, projection(expected));
    });
  });
  const arrow = elements.find(e => e.attributes['data-curvature-transported'] === 'current');
  if (s.vectorLength === 0) assert.equal(arrow, undefined);
  else {
    const actual = arrow.attributes.points.split(' ').map(point => point.split(',').map(Number)), point = scale(unitPoint, s.radius);
    vectorNear(actual[0], projection(point)); vectorNear(actual[1], projection(add(point, scale(tangent, gain))));
  }
}
let controlsChecked = 0;
for (const control of lab.controls) {
  const values = control.options ? control.options.map(o => o.value) : [control.min, control.max];
  const input = inputFor(control.key); assert.ok(all().some(e => e.tagName === 'label' && e.attributes.for === input.attributes.id));
  for (const value of values) { input.value = String(value); input.fire('change'); mounted(); controlsChecked++; }
  action('reset').fire('click'); assert.deepEqual(state(), original);
}
const radius = inputFor('radius'); radius.value = '1.37'; radius.fire('input'); assert.equal(radius.value, '1.37'); assert.equal(state().radius, 1); radius.fire('change'); assert.equal(state().radius, 1.25);
for (const [key, value] of [['radius', .5], ['vectorLength', 2], ['startAngle', 90], ['leg', '1'], ['progress', 17]]) { inputFor(key).value = String(value); inputFor(key).fire('change'); } mounted();
action('pole').fire('click'); assert.equal(state().surface, 'sphere'); assert.equal(state().v, 90); assert.match(root.textContent, /u direction is undefined/);
action('inner').fire('click'); assert.equal(state().surface, 'torus'); assert.equal(state().v, 180);
action('zero').fire('click'); assert.equal(state().v, 90);
action('closed').fire('click'); assert.equal(state().leg, '2'); assert.equal(state().progress, 100);
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true');
action('reset').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'false'); assert.deepEqual(state(), original); mounted();
const second = lab.render({ props: { scenario } }); assert.notEqual(root.attributes['aria-labelledby'], second.attributes['aria-labelledby']);
console.log(`Verified ${surfaces} independently differentiated surface states, ${integrals} quadrature patches, ${transports} geometric transport states and ${controlsChecked} mounted controls; signs, cancellation, poles, seams, normal invariance and resets passed.`);

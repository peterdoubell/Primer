'use strict';
// The calculation behind each stand-alone lesson activity, checked against hand-worked values.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..', 'web');
const load = name => require(path.join(root, name, 'lab.js'));
const near = (actual, expected, tolerance = 1e-9) => assert.ok(Math.abs(actual - expected) <= tolerance, actual + ' is not ' + expected);

test('unit circle gives exact special values, signs by quadrant and undefined tangents', () => {
  const m = load('math/unit-circle');
  near(m.trig(30).sin, 0.5); near(m.trig(60).cos, 0.5); near(m.trig(45).tan, 1);
  assert.equal(m.trig(90).tan, null); assert.equal(m.trig(270).tan, null); assert.equal(m.trig(180).sin, 0);
  assert.deepEqual([m.trig(100).quadrant, m.trig(200).quadrant, m.trig(300).quadrant, m.trig(90).quadrant], [2, 3, 4, 0]);
  assert.deepEqual(m.exact(150), {sin: '1/2', cos: '−√3/2', tan: '−√3/3'});
  assert.deepEqual(m.exact(225), {sin: '−√2/2', cos: '−√2/2', tan: '1'});
  assert.deepEqual(m.exact(270), {sin: '−1', cos: '0', tan: 'undefined'});
  assert.equal(m.exact(20), null); assert.equal(m.reference(330), 30);
  for (let d = 0; d <= 360; d += 5) near(m.trig(d).sin ** 2 + m.trig(d).cos ** 2, 1);
});

test('exponential model doubles, halves and inverts with a logarithm', () => {
  const m = load('math/exponential-growth');
  assert.equal(m.value(2, 3, 2), 18); near(m.changeTime(2), 1); near(m.changeTime(0.5), 1); near(m.changeTime(4), 0.5);
  assert.equal(m.changeTime(1), null); near(m.log(2, 8), 3);
  near(m.value(5, 1.5, m.changeTime(1.5)), 10); near(m.value(5, 0.8, m.changeTime(0.8)), 2.5);
  assert.deepEqual([m.kind(2), m.kind(0.5), m.kind(1)], ['growth', 'decay', 'constant']);
});

test('series formulas agree with direct addition and geometric limits need |r| < 1', () => {
  const m = load('math/series-sums');
  assert.equal(m.term('arithmetic', 3, 2, 5), 11); assert.equal(m.closed('arithmetic', 1, 1, 100), 5050);
  assert.equal(m.term('geometric', 2, 3, 4), 54); assert.equal(m.closed('geometric', 1, 2, 10), 1023);
  assert.equal(m.closed('geometric', 4, 1, 6), 24);
  for (const [kind, a, d] of [['arithmetic', -5, 0.25], ['arithmetic', 10, -2], ['geometric', 3, 0.5], ['geometric', -2, -1.5], ['geometric', 7, 1]])
    for (let n = 1; n <= 20; n++) near(m.closed(kind, a, d, n), m.partial(kind, a, d, n), 1e-6);
  near(m.limit('geometric', 3, 0.5), 6); assert.equal(m.limit('geometric', 3, 1), null); assert.equal(m.limit('geometric', 3, -1.5), null);
  assert.equal(m.limit('arithmetic', 3, 0.5), null);
});

test('two lines have one, no or infinitely many solutions', () => {
  const m = load('math/two-lines');
  assert.deepEqual(m.solve(1, 2, -1, 4), {kind: 'one', x: 1, y: 3});
  assert.deepEqual(m.solve(2, 1, 2, 5), {kind: 'parallel'}); assert.deepEqual(m.solve(2, 1, 2, 1), {kind: 'same'});
  const s = m.solve(0.5, -3, -2, 7); near(0.5 * s.x - 3, s.y); near(-2 * s.x + 7, s.y);
});

test('number line follows the sign rules', () => {
  const m = load('math/number-line');
  assert.equal(m.apply(3, 'add', -5), -2); assert.equal(m.apply(3, 'subtract', -5), 8); assert.equal(m.apply(-3, 'multiply', -5), 15);
  assert.equal(m.apply(-3, 'multiply', 5), -15); assert.equal(m.move('subtract', -5), 5); assert.equal(m.move('add', -5), -5);
  assert.deepEqual([m.sign(-2), m.sign(0), m.sign(4)], ['negative', 'zero', 'positive']);
});

test('sieve, factorisation, gcd and lcm are exact', () => {
  const m = load('math/factor-sieve'), primes = m.sieve(200);
  assert.equal(primes.filter(Boolean).length, 46); assert.equal(primes[1], false); assert.equal(primes[2], true); assert.equal(primes[199], true); assert.equal(primes[91], false);
  assert.deepEqual(m.factorise(84), [2, 2, 3, 7]); assert.deepEqual(m.factorise(97), [97]); assert.deepEqual(m.factorise(200), [2, 2, 2, 5, 5]);
  assert.deepEqual(m.divisors(12), [1, 2, 3, 4, 6, 12]); assert.equal(m.gcd(84, 90), 6); assert.equal(m.lcm(84, 90), 1260);
  for (let n = 2; n <= 200; n++) {
    assert.equal(m.factorise(n).reduce((a, b) => a * b, 1), n);
    assert.ok(m.factorise(n).every(p => primes[p]));
    assert.equal(m.gcd(n, 90) * m.lcm(n, 90), n * 90);
  }
});

test('block on a slope: static friction holds until tan θ exceeds μs', () => {
  const m = load('physics/incline-friction');
  const rest = m.incline({m: 5, theta: 20, mus: 0.5, muk: 0.4});
  assert.equal(rest.slides, false); near(rest.friction, rest.parallel); assert.equal(rest.acceleration, 0);
  near(rest.weight, 49.05); near(rest.normal, 49.05 * Math.cos(20 * Math.PI / 180)); near(rest.criticalAngle, 26.565051177, 1e-8);
  const slide = m.incline({m: 5, theta: 40, mus: 0.5, muk: 0.4});
  assert.equal(slide.slides, true); near(slide.acceleration, 9.81 * (Math.sin(40 * Math.PI / 180) - 0.4 * Math.cos(40 * Math.PI / 180)));
  // Mass changes the forces but not whether the block slides, nor its acceleration.
  const heavy = m.incline({m: 20, theta: 40, mus: 0.5, muk: 0.4});
  near(heavy.acceleration, slide.acceleration); assert.equal(m.incline({m: 20, theta: 20, mus: 0.5, muk: 0.4}).slides, false);
  near(m.incline({m: 2, theta: 30, mus: 0, muk: 0}).acceleration, 9.81 / 2);
});

test('lever balances torques and conserves work', () => {
  const m = load('physics/lever-balance'), r = m.lever(100, 1, 3);
  near(r.effort, 100 / 3); near(r.advantage, 3); assert.equal(r.torque, 100);
  near(r.effort * m.travel(0.1, 1, 3), 100 * 0.1); assert.equal(m.lever(60, 2, 2).effort, 60);
  near(m.lever(50, 4, 0.5).advantage, 0.125);
});

test('Lorentz factor matches standard values', () => {
  const m = load('physics/time-dilation');
  assert.equal(m.gamma(0), 1); near(m.gamma(0.6), 1.25); near(m.gamma(0.8), 5 / 3); near(m.gamma(0.99), 7.088812050083354, 1e-9);
  near(m.dilated(1, 0.6), 1.25); near(m.contracted(10, 0.6), 8);
});

test('photoelectric effect: threshold depends on wavelength, not brightness', () => {
  const m = load('physics/photoelectric');
  near(m.photonEnergy(400), 3.09960496, 1e-8); near(m.threshold(2.1), 590.40094476, 1e-7);
  assert.equal(m.emits(400, m.METALS.caesium), true); assert.equal(m.emits(400, m.METALS.zinc), false);
  near(m.kinetic(400, 2.1), 0.99960496, 1e-8); assert.equal(m.kinetic(700, 4.7), 0);
  near(m.frequency(500), 5.99584916e14, 1e7);
  // At the threshold wavelength the electron leaves with no energy to spare.
  for (const work of Object.values(m.METALS)) near(m.kinetic(m.threshold(work), work), 0, 1e-12);
});

test('every registered activity has its page, script and a return link to its module', () => {
  const registry = JSON.parse(fs.readFileSync(path.join(root, 'activities', 'registry.json'), 'utf8'));
  const curriculum = fs.readdirSync(path.join(root, '..', 'data', 'curriculum')).map(f => fs.readFileSync(path.join(root, '..', 'data', 'curriculum', f), 'utf8')).join('');
  assert.ok(Object.keys(registry).length >= 10);
  for (const [node, links] of Object.entries(registry)) {
    assert.ok(curriculum.includes('"id": "' + node + '"') || curriculum.includes('"id":"' + node + '"'), node);
    for (const {href, label} of links) {
      assert.match(href, /^\/app\/(math|physics|language)\/[a-z0-9-]+\/index\.html$/); assert.ok(label.length > 8);
      const dir = path.join(root, href.replace('/app/', '').replace('/index.html', ''));
      const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
      assert.ok(html.includes('href="/app/#/node/' + node + '"'), href); assert.ok(html.includes('role="status"') && html.includes('role="img"'), href);
      assert.ok(fs.existsSync(path.join(dir, 'lab.js')), href);
      // Every control has a label.
      for (const id of [...html.matchAll(/<(?:input|select)[^>]* id="([a-z0-9-]+)"/g)].map(x => x[1])) assert.ok(html.includes('for="' + id + '"'), href + ' ' + id);
    }
  }
});

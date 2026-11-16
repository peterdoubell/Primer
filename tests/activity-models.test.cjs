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

test('clock reads hand angles and words', () => {
  const m = load('math/clock-reading');
  assert.deepEqual(m.angles(3, 0), {minute: 0, hour: 90}); assert.deepEqual(m.angles(12, 30), {minute: 180, hour: 15}); assert.deepEqual(m.angles(9, 45), {minute: 270, hour: 292.5});
  assert.equal(m.words(3, 0), "three o'clock"); assert.equal(m.words(3, 15), 'quarter past three'); assert.equal(m.words(3, 30), 'half past three');
  assert.equal(m.words(3, 45), 'quarter to four'); assert.equal(m.words(12, 50), '10 minutes to one'); assert.equal(m.words(7, 5), '5 minutes past seven');
  assert.equal(m.words(11, 59), '1 minute to twelve'); assert.equal(m.digital(4, 5), '4:05');
});

test('order of operations reduces brackets, powers, then × ÷, then + −', () => {
  const m = load('math/order-of-operations'), value = e => Number(m.steps(e).pop().text);
  const cases = {'3 + 4 × 2': 11, '(3 + 4) × 2': 14, '20 - 8 ÷ 4 + 1': 19, '2 × 3 ^ 2': 18, '(2 × 3) ^ 2': 36, '18 ÷ 3 × 2': 12, '10 - 4 - 3': 3, '2 ^ 3 ^ 2': 512,
    '6 + 2 × (5 - 3) ^ 2 ÷ 4': 8, '100 ÷ (2 + 3) × 2 - 1': 39};
  for (const [expression, expected] of Object.entries(cases)) assert.equal(value(expression), expected, expression);
  assert.deepEqual(m.steps('3 + 4 × 2').map(s => s.text), ['3 + 4 × 2', '3 + 8', '11']);
  assert.equal(m.steps('(3 + 4) × 2')[1].rule, 'Inside the brackets: Add or subtract, left to right');
  assert.equal(m.leftToRight('3 + 4 × 2'), 14); assert.equal(m.leftToRight('18 ÷ 3 × 2'), 12);
  // Every option offered on the page is covered here.
  const html = fs.readFileSync(path.join(root, 'math/order-of-operations/index.html'), 'utf8');
  for (const option of [...html.matchAll(/<option value="([^"]+)"/g)].map(x => x[1])) assert.ok(option in cases, option);
});

test('laws of exponents hold, including zero and negative exponents', () => {
  const m = load('math/powers-table');
  assert.equal(m.power(2, 10), 1024); assert.equal(m.power(2, -2), 0.25); assert.equal(m.power(5, 0), 1); assert.equal(m.power(-3, 3), -27);
  assert.equal(m.expand(2, 3), '2 × 2 × 2'); assert.equal(m.expand(-3, 2), '(-3) × (-3)'); assert.equal(m.expand(2, -2), '1 ÷ (2 × 2)');
  for (const a of [-3, -2, 2, 3, 5]) for (let i = -3; i <= 6; i++) for (let j = -3; j <= 4; j++) { const l = m.laws(a, i, j); for (const [x, y] of Object.values(l)) near(x, y, Math.abs(y) * 1e-9 + 1e-12); }
});

test('balance equation undoes addition then multiplication', () => {
  const m = load('math/balance-equation'), s = m.solve(3, 4, 19);
  assert.equal(s.x, 5); assert.deepEqual(s.steps.map(t => t.left + ' = ' + t.right), ['3x + 4 = 19', '3x = 15', 'x = 5']);
  assert.equal(m.solve(2, -6, 4).steps[1].rule, 'Add 6 to both sides'); assert.equal(m.solve(2, -6, 4).x, 5);
  for (let a = 1; a <= 9; a++) for (let b = -10; b <= 10; b++) for (let x = -6; x <= 9; x++) assert.equal(m.solve(a, b, m.check(a, b, x)).x, x);
});

test('complex multiplication multiplies moduli and adds arguments', () => {
  const m = load('math/complex-multiply');
  assert.deepEqual(m.mul([1, 1], [0, 1]), [-1, 1]); assert.deepEqual(m.mul([0, 1], [0, 1]), [-1, 0]); assert.deepEqual(m.mul([2, 3], [4, -1]), [11, 10]);
  near(m.mod([3, 4]), 5); near(m.arg([0, 2]), 90); assert.equal(m.show([1, -2]), '1 − 2i');
  for (const z of [[1, 1], [-2, 0.5], [3, -3]]) for (const w of [[0, 1], [2, 2], [-1.5, 1]]) {
    const p = m.mul(z, w); near(m.mod(p), m.mod(z) * m.mod(w)); near(Math.cos((m.arg(p) - m.arg(z) - m.arg(w)) * Math.PI / 180), 1);
  }
});

test('Euler steps converge on the exact solutions', () => {
  const m = load('math/slope-field');
  near(m.LAWS.growth.exact(2, 3, 0.5), 3 * Math.E); near(m.LAWS.cooling.exact(1e3, 5, 0.5), 2); near(m.LAWS.logistic.exact(1e3, 0.5, 0.5), 4, 1e-9); near(m.LAWS.logistic.exact(0, 0.5, 0.5), 0.5);
  for (const law of Object.values(m.LAWS)) {
    const truth = law.exact(5, 0.5, 0.5), error = h => Math.abs(m.euler(law.f, 0.5, 0.5, h, 5).pop()[1] - truth);
    assert.ok(error(0.125) < error(0.25) && error(0.25) < error(0.5), law.label); assert.ok(error(0.125) / error(0.25) > 0.4 && error(0.125) / error(0.25) < 0.62, law.label);
    // The exact solution satisfies the equation: its numerical derivative equals f.
    for (const t of [0.5, 2, 4]) near((law.exact(t + 1e-6, 0.5, 0.5) - law.exact(t - 1e-6, 0.5, 0.5)) / 2e-6, law.f(law.exact(t, 0.5, 0.5), 0.5), 1e-6);
  }
  assert.equal(m.euler(m.LAWS.growth.f, 1, 1, 0.5, 5).length, 11);
});

test('projectile range, peak and symmetry', () => {
  const m = load('physics/projectile'), f = m.flight(20, 45);
  near(f.range, 400 / 9.81, 1e-9); near(f.peak, 200 / (2 * 9.81)); near(f.time, 2 * f.peakTime); near(f.impactSpeed, 20);
  near(m.flight(20, 30).range, m.flight(20, 60).range, 1e-9); assert.ok(m.flight(20, 45).range > m.flight(20, 40).range);
  const high = m.flight(10, 0, 20); near(high.time, Math.sqrt(40 / 9.81)); near(m.position(10, 0, 20, high.time)[1], 0, 1e-9); near(high.impactSpeed ** 2, 100 + 2 * 9.81 * 20, 1e-9);
});

test('floating depends on density alone', () => {
  const m = load('physics/density-float');
  assert.equal(m.floats(m.SOLIDS.ice, m.LIQUIDS['fresh water']), true); near(m.submerged(m.SOLIDS.ice, m.LIQUIDS['fresh water']), 0.92);
  assert.equal(m.floats(m.SOLIDS.iron, m.LIQUIDS['fresh water']), false); assert.equal(m.submerged(m.SOLIDS.iron, 1), 1);
  assert.equal(m.floats(m.SOLIDS.iron, m.LIQUIDS.mercury), true); assert.equal(m.floats(m.SOLIDS.gold, m.LIQUIDS.mercury), false);
  assert.equal(m.floats(m.SOLIDS.ice, m.LIQUIDS['cooking oil']), false); near(m.submerged(0.5, 1.025), 0.5 / 1.025);
});

test('additive colour mixing names the primaries and secondaries', () => {
  const m = load('physics/colour-mixing');
  assert.equal(m.name(100, 100, 0), 'yellow'); assert.equal(m.name(0, 100, 100), 'cyan'); assert.equal(m.name(100, 0, 100), 'magenta');
  assert.equal(m.name(100, 100, 100), 'white'); assert.equal(m.name(0, 0, 0), 'black (no light)'); assert.equal(m.hex(100, 0, 50), '#ff0080');
  assert.deepEqual(m.complement(100, 100, 0), [0, 0, 100]); assert.equal(m.name(...m.complement(100, 0, 0)), 'cyan');
});

test('mixing water conserves energy', () => {
  const m = load('physics/heat-mixing');
  assert.equal(m.final(1, 80, 3, 20), 35); assert.equal(m.final(2, 50, 2, 50), 50); near(m.transferred(1, 80, 3, 20), 4186 * 45);
  for (const [m1, t1, m2, t2] of [[1, 80, 3, 20], [0.5, 10, 4.5, 95], [2, 0, 2, 100]]) {
    const f = m.final(m1, t1, m2, t2); near(m1 * (t1 - f) + m2 * (t2 - f), 0, 1e-9); assert.ok(f >= Math.min(t1, t2) && f <= Math.max(t1, t2));
  }
});

test('every registered activity has its page, script and a return link to its module', () => {
  const registry = JSON.parse(fs.readFileSync(path.join(root, 'activities', 'registry.json'), 'utf8'));
  const curriculum = fs.readdirSync(path.join(root, '..', 'data', 'curriculum')).map(f => fs.readFileSync(path.join(root, '..', 'data', 'curriculum', f), 'utf8')).join('');
  assert.ok(Object.keys(registry).length >= 20);
  for (const [node, links] of Object.entries(registry)) {
    assert.ok(curriculum.includes('"id": "' + node + '"') || curriculum.includes('"id":"' + node + '"'), node);
    for (const {href, label} of links) {
      assert.match(href, /^\/app\/(math|physics|language)\/[a-z0-9-]+\/index\.html$/); assert.ok(label.length > 8);
      const dir = path.join(root, href.replace('/app/', '').replace('/index.html', ''));
      const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
      assert.ok(html.includes('href="/app/#/node/' + node + '"'), href); assert.ok(html.includes('role="status"'), href); assert.equal(html.includes('<canvas'), html.includes('role="img"'), href);
      assert.ok(fs.existsSync(path.join(dir, 'lab.js')), href);
      // Every control has a label.
      for (const id of [...html.matchAll(/<(?:input|select)[^>]* id="([a-z0-9-]+)"/g)].map(x => x[1])) assert.ok(html.includes('for="' + id + '"'), href + ' ' + id);
    }
  }
});

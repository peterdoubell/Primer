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

test('parts of speech: every word is tagged with a known class and each sentence has a verb', () => {
  const m = load('language/parts-of-speech');
  for (const sentence of m.SENTENCES) {
    assert.ok(sentence.every(([word, kind]) => word && kind in m.JOBS)); assert.ok(m.count(sentence).verb >= 1); assert.ok(m.count(sentence).noun + (m.count(sentence).pronoun || 0) >= 1);
    assert.match(m.text(sentence), /^[A-Z].*\.$/);
  }
  assert.deepEqual(m.count(m.SENTENCES[0]), {determiner: 2, adjective: 1, noun: 2, verb: 1, adverb: 1, preposition: 1});
  assert.equal(Object.keys(m.JOBS).length, 8);
});

test('sentence builder always produces a capital letter, an end mark and a verb', () => {
  const m = load('language/sentence-builder');
  assert.equal(m.build('the cat', 'sleeps', 'on the mat', 'statement'), 'The cat sleeps on the mat.');
  assert.equal(m.build('the cat', 'sleeps', 'on the mat', 'question'), 'Does the cat sleep on the mat?');
  assert.equal(m.build('the rain', 'falls', '', 'exclamation'), 'The rain falls!');
  for (const s of m.SUBJECTS) for (const v of m.VERBS) for (const e of m.ENDINGS) for (const k of ['statement', 'question', 'exclamation']) {
    const text = m.build(s, v, e, k); assert.deepEqual(m.check(text), {capital: true, end: true, verb: true}, text); assert.equal(m.kind(text), k); assert.ok(!text.includes('  '));
  }
  assert.deepEqual(m.check('the cat'), {capital: false, end: false, verb: false});
});

test('metre: syllable counts match the stress pattern and the named foot fills the line', () => {
  const m = load('language/meter-scansion');
  for (const line of m.LINES) {
    assert.equal(line.syllables.length, line.stress.length, line.poet);
    assert.match(line.stress, /^[Sx]+$/, line.poet);
    assert.ok(m.matches(line) >= line.feet - 1, line.poet); assert.ok(line.feet in m.COUNT);
  }
  assert.equal(m.name(m.LINES[0]), 'iambic pentameter'); assert.equal(m.name(m.LINES[1]), 'trochaic tetrameter'); assert.equal(m.name(m.LINES[4]), 'dactylic hexameter');
  assert.equal(m.matches(m.LINES[0]), 5); assert.equal(m.matches(m.LINES[2]), 4);
});

test('word roots: every word decomposes into listed roots that appear in its spelling', () => {
  const m = load('language/word-roots'), variant = {phon: ['phon'], in: ['in', 'im'], logy: ['logy'], graph: ['graph'], meter: ['meter']};
  for (const [word, roots] of Object.entries(m.WORDS)) for (const root of roots) {
    assert.ok(root in m.ROOTS, root); assert.ok((variant[root] || [root]).some(form => word.includes(form)), word + ' ' + root);
  }
  assert.equal(m.literal('telephone'), 'far + sound'); assert.equal(m.literal('biology'), 'life + study of'); assert.equal(m.literal('transport'), 'across + carry');
  assert.deepEqual(m.family('scope'), ['telescope', 'microscope']); assert.ok(m.family('graph').length >= 5);
  for (const [origin] of Object.values(m.ROOTS)) assert.ok(['Greek', 'Latin'].includes(origin));
});

test('English timeline: periods are contiguous and events are in order', () => {
  const m = load('language/english-timeline');
  m.PERIODS.forEach((p, i) => { if (i) assert.equal(p.from, m.PERIODS[i - 1].to); assert.ok(p.sample && p.source); });
  assert.equal(m.period(900).name, 'Old English'); assert.equal(m.period(1150).name, 'Middle English'); assert.equal(m.period(1400).name, 'Middle English');
  assert.equal(m.period(1611).name, 'Early Modern English'); assert.equal(m.period(2025).name, 'Modern English');
  assert.deepEqual(m.EVENTS.map(e => e[0]), [...m.EVENTS.map(e => e[0])].sort((a, b) => a - b));
  assert.equal(m.eventsBy(1066).length, 3); assert.equal(m.eventsBy(450).length, 0); assert.equal(m.eventsBy(2025).length, m.EVENTS.length);
});

test('alphabet: 26 letters, five vowels, and each example word contains its letter', () => {
  const m = load('language/alphabet-grid');
  assert.equal(m.letters().length, 26); assert.equal(m.letters().filter(l => m.info(l).vowel).join(''), 'aeiou');
  for (const letter of m.letters()) { const i = m.info(letter); assert.ok(i.position === 'starts' ? i.word.startsWith(letter) : i.word.endsWith(letter), i.word); assert.equal(i.upper.toLowerCase(), letter); }
  assert.deepEqual([m.info('a').before, m.info('a').after, m.info('z').before, m.info('z').after, m.info('m').index], [null, 'b', 'y', null, 13]);
});

test('paragraph builder: scrambled order is scored against each sentence’s role', () => {
  const m = load('language/paragraph-builder');
  for (const p of m.PARAGRAPHS) {
    assert.deepEqual(p.sentences.map(s => s[1]), [0, 1, 2, 3]); assert.equal(m.score(p, [2, 0, 3, 1]), 4); assert.equal(m.score(p, [0, 1, 2, 3]), 0); assert.equal(m.score(p, [2, 0, 1, 3]), 2);
    assert.equal(m.ordered(p).split('. ').length, 4);
  }
  assert.equal(m.ROLES.length, 4); for (const role of m.ROLES) assert.ok(m.JOB[role]);
});

test('rhyme families: rhyme is by family, and every odd-one-out round has exactly one outsider', () => {
  const m = load('language/rhyme-families');
  assert.equal(m.rhymes('cat', 'hat'), true); assert.equal(m.rhymes('cat', 'dog'), false); assert.equal(m.rhymes('cat', 'cat'), false); assert.equal(m.rhymes('night', 'kite'), true);
  assert.deepEqual(m.surprising('tree'), ['sea', 'key']); assert.deepEqual(m.surprising('sun'), ['one']);
  const all = Object.values(m.FAMILIES).flat(); assert.equal(new Set(all).size, all.length);
  for (let n = 0; n < 30; n++) { const r = m.round(n); assert.equal(r.words.length, 4); assert.equal(r.words.filter(w => m.family(w) !== m.family(r.words.find(x => x !== r.odd))).length, 1); assert.ok(r.words.includes(r.odd)); }
});

const SORTING = ['letter-sounds', 'question-words', 'story-parts', 'childrens-classics', 'letter-shapes', 'read-for-meaning', 'word-hoard', 'story-mountain', 'myth-traditions', 'novel-elements',
  'source-types', 'argument-parts', 'literary-devices', 'shakespeare-plays', 'world-classics', 'ancient-canon', 'poetic-forms', 'theory-schools', 'garden-paths', 'registers'];

test('sorting activities: every table row and quiz entry has a known answer, and each round offers it exactly once', () => {
  for (const slug of SORTING) {
    const m = load('language/' + slug);
    assert.equal(new Set(m.ITEMS.map(item => item.name)).size, m.ITEMS.length, slug);
    for (const item of m.ITEMS) { assert.ok(m.CATEGORIES.includes(item.cat), slug + ' ' + item.name); assert.equal(m.category(item.name), item.cat); assert.ok(m.inCategory(item.cat).includes(item.name)); }
    assert.ok(m.QUIZ.length >= 6, slug);
    const asked = new Set();
    for (let n = 0; n < m.QUIZ.length; n++) {
      const round = m.round(n); asked.add(round.text);
      assert.ok(round.options.length >= 3 && round.options.length <= 4, slug);
      assert.equal(new Set(round.options).size, round.options.length, slug);
      assert.equal(round.options.filter(option => option === round.answer).length, 1, slug + ' ' + round.text);
      assert.equal(m.check(n, round.answer), true); assert.equal(m.check(n, round.options.find(option => option !== round.answer)), false);
      assert.ok(!round.prompt.includes('{name}'), slug);
    }
    assert.equal(asked.size, m.QUIZ.length, slug + ' repeats a question before asking them all');
  }
});

test('sorting activities: spot checks of the facts they teach', () => {
  const cat = (slug, name) => load('language/' + slug).category(name);
  assert.equal(cat('childrens-classics', "Charlotte's Web"), 'E. B. White'); assert.equal(cat('childrens-classics', 'The Tale of Peter Rabbit'), 'Beatrix Potter');
  assert.equal(cat('letter-shapes', 'g'), 'Tail'); assert.equal(cat('letter-shapes', 'h'), 'Tall'); assert.equal(cat('letter-shapes', 'a'), 'Small');
  assert.equal(load('language/letter-shapes').ITEMS.length, 26);
  assert.equal(cat('myth-traditions', 'Thor'), 'Norse'); assert.equal(cat('myth-traditions', 'Anubis'), 'Egyptian'); assert.equal(cat('myth-traditions', 'Amaterasu'), 'Japanese');
  assert.equal(cat('shakespeare-plays', 'Hamlet'), 'Tragedy'); assert.equal(cat('shakespeare-plays', 'Twelfth Night'), 'Comedy'); assert.equal(cat('shakespeare-plays', 'Henry V'), 'History');
  assert.equal(cat('ancient-canon', 'Aeneid'), 'Virgil'); assert.equal(cat('ancient-canon', 'Odyssey'), 'Homer'); assert.equal(cat('ancient-canon', 'Medea'), 'Euripides');
  assert.equal(cat('world-classics', 'The Tale of Genji'), 'Japan'); assert.equal(cat('world-classics', 'Don Quixote'), 'Spain'); assert.equal(cat('world-classics', 'Things Fall Apart'), 'Nigeria');
  assert.equal(cat('poetic-forms', 'Haiku'), 'Japanese'); assert.equal(cat('poetic-forms', 'Sonnet'), 'Italian'); assert.equal(cat('source-types', 'a diary'), 'Primary'); assert.equal(cat('source-types', 'an encyclopedia'), 'Tertiary');
  assert.equal(cat('word-hoard', 'enormous'), 'tiny'); assert.equal(cat('garden-paths', 'The old man the boats.'), 'man');
  // Time lines run in order, and the story mountain peaks at the problem.
  for (const slug of ['childrens-classics', 'shakespeare-plays', 'ancient-canon']) { const years = load('language/' + slug).ITEMS.map(item => item.year); assert.deepEqual(years, [...years].sort((a, b) => a - b), slug); }
  assert.deepEqual(load('language/story-mountain').ITEMS.map(item => item.name), ['Opening', 'Build-up', 'Problem', 'Resolution', 'Ending']);
  // Garden-path options are words of the sentence itself.
  const paths = load('language/garden-paths'); for (let n = 0; n < paths.QUIZ.length; n++) { const round = paths.round(n); for (const option of round.options) assert.ok(round.text.includes(option), option); }
});

test('speech pace: words that fit, the three-part plan and overrun', () => {
  const m = load('language/speech-pace');
  assert.equal(m.words(3, 130), 390); assert.equal(m.seconds(390, 130), 180); assert.equal(m.count('  one two\nthree  '), 3); assert.equal(m.count(''), 0);
  near(m.PARTS.reduce((sum, part) => sum + part.share, 0), 1);
  assert.deepEqual(m.plan(3, 130).map(part => [part.name, part.seconds, part.words]), [['Opening', 27, 59], ['Body', 126, 273], ['Close', 27, 59]]);
  assert.equal(m.clock(125), '2:05'); assert.equal(m.describe(100), 'slow and clear'); assert.equal(m.describe(130), 'comfortable'); assert.equal(m.describe(170), 'fast');
  assert.equal(m.overrun('word '.repeat(520), 3, 130), 60); assert.ok(m.overrun('word '.repeat(100), 3, 130) < 0);
});

test('bigram counter: counts, probabilities, smoothing and greedy generation', () => {
  const m = load('language/bigram-counter'), text = 'the cat sat on the mat. the dog sat on the log. the cat saw the dog. the dog saw the cat on the mat.', c = m.count(text);
  assert.deepEqual(m.stats(text), {tokens: 25, types: 8}); assert.equal(c.unigrams.the, 9); assert.equal(c.bigrams['<s>'].the, 4);
  assert.deepEqual(m.next(c, 'the').map(row => [row.word, row.count]), [['cat', 3], ['dog', 3], ['mat', 2], ['log', 1]]);
  near(m.next(c, 'the').reduce((sum, row) => sum + row.p, 0), 1); near(m.probability(c, 'the', 'cat'), 1 / 3); assert.equal(m.probability(c, 'sat', 'on'), 1); assert.equal(m.probability(c, 'cat', 'log'), 0);
  assert.equal(m.vocabulary(c).length, 9); near(m.probability(c, 'cat', 'log', true), 1 / 12); near(m.next(c, 'cat', true).reduce((sum, row) => sum + row.p, 0), 1);
  assert.equal(m.generate(c), 'the cat on the'); assert.equal(m.generate(m.count('')), ''); assert.equal(m.probability(m.count(''), 'x', 'y'), 0);
});

test('early number activities: comparing, counting, tens and ones, patterns and shapes', () => {
  const c = load('math/bigger-smaller'); assert.deepEqual([c.sign(7, 4), c.sign(2, 9), c.sign(5, 5)], ['>', '<', '=']); assert.equal(c.difference(4, 7), 3); assert.equal(c.words(3, 3), '3 is the same as 3');
  const n = load('math/count-to-ten'); assert.deepEqual(n.forward(4), [1, 2, 3, 4]); assert.deepEqual(n.back(4), [4, 3, 2, 1]); assert.deepEqual(n.forward(0), []); assert.equal(n.WORDS[10], 'ten');
  const t = load('math/numbers-to-twenty'); assert.deepEqual(t.split(13), {tens: 1, ones: 3}); assert.deepEqual(t.split(20), {tens: 2, ones: 0}); assert.deepEqual(t.split(7), {tens: 0, ones: 7}); assert.equal(t.WORDS[13], 'thirteen'); assert.equal(t.WORDS.length, 21);
  const p = load('math/what-comes-next'); assert.deepEqual(p.sequence('aab', 7), ['red', 'red', 'blue', 'red', 'red', 'blue', 'red']); assert.equal(p.term('abc', 6), 'green'); assert.deepEqual(p.sequence('plus2', 5), [1, 3, 5, 7, 9]); assert.equal(p.term('plus3', 6), 17);
  const s = load('math/shape-sides'); assert.deepEqual(['circle', 'triangle', 'square', 'rectangle', 'pentagon', 'hexagon'].map(s.sides), [0, 3, 4, 4, 5, 6]); assert.equal(s.points('hexagon').length, 6); assert.equal(s.points('circle').length, 0);
});

test('arithmetic activities: carrying, exchanging, arrays, remainders and place value', () => {
  const a = load('math/column-addition'); assert.deepEqual(a.add(47, 38), {sum: 85, ones: 15, carry: 1, onesDigit: 5, tens: 8}); assert.deepEqual(a.add(21, 34), {sum: 55, ones: 5, carry: 0, onesDigit: 5, tens: 5}); assert.equal(a.add(99, 99).tens * 10 + a.add(99, 99).onesDigit, 198);
  const s = load('math/column-subtraction'); assert.deepEqual(s.subtract(52, 27), {difference: 25, exchange: true, ones: 5, tens: 2, possible: true}); assert.deepEqual(s.subtract(68, 25), {difference: 43, exchange: false, ones: 3, tens: 4, possible: true}); assert.equal(s.subtract(20, 30).possible, false);
  for (let x = 0; x < 100; x += 7) for (let y = 0; y <= x; y += 3) { const r = s.subtract(x, y); assert.equal(r.tens * 10 + r.ones, x - y); const q = a.add(x, y); assert.equal(q.tens * 10 + q.onesDigit, x + y); }
  const m = load('math/times-table-array'); assert.equal(m.product(7, 8), 56); assert.equal(m.repeated(3, 5), '5 + 5 + 5'); assert.deepEqual(m.table(12)[11], ['12 × 12', 144]);
  const d = load('math/equal-sharing'); assert.deepEqual(d.divide(23, 4), {each: 5, left: 3, exact: false}); assert.deepEqual(d.divide(24, 6), {each: 4, left: 0, exact: true}); assert.ok(d.check(59, 12));
  const f = load('math/halves-and-quarters'); assert.equal(f.name(1, 2), 'one half'); assert.equal(f.name(3, 4), 'three quarters'); assert.equal(f.name(4, 4), 'one whole'); assert.equal(f.name(2, 8), 'two eighths'); assert.deepEqual(f.simplest(2, 4), [1, 2]); assert.deepEqual(f.simplest(6, 8), [3, 4]);
  const u = load('math/unit-conversion'); assert.equal(u.toBig('length', 250), 2.5); assert.equal(u.toBig('mass', 1500), 1.5); assert.equal(u.toSmall('capacity', 2), 2000); assert.deepEqual(u.split('length', 1250), {big: 12, small: 50});
  const v = load('math/place-value-digits'); assert.deepEqual(v.digits(3407).map(x => [x.digit, x.value]), [[3, 3000], [4, 400], [0, 0], [7, 7]]); assert.equal(v.expanded(3407), '3000 + 400 + 7'); assert.equal(v.expanded(0), '0'); assert.equal(v.expanded(9999), '9000 + 900 + 90 + 9');
});

test('middle activities: coordinates, decimals, fractions, measures, percent and ratio', () => {
  const c = load('math/plot-a-point'); assert.deepEqual([c.quadrant(3, 2), c.quadrant(-3, 2), c.quadrant(-3, -2), c.quadrant(3, -2)], ['in the first quadrant', 'in the second quadrant', 'in the third quadrant', 'in the fourth quadrant']);
  assert.equal(c.quadrant(0, 0), 'at the origin'); assert.equal(c.quadrant(4, 0), 'on the x-axis'); assert.equal(c.distance(3, -4), 5); assert.deepEqual(c.reflectX(3, -2), [3, 2]); assert.deepEqual(c.reflectY(3, -2), [-3, -2]);
  const d = load('math/decimal-arithmetic'); assert.equal(d.calc(0.1, 0.2, 'add'), 0.3); assert.equal(d.calc(3.75, 1.4, 'add'), 5.15); assert.equal(d.calc(1.4, 3.75, 'subtract'), -2.35); assert.equal(d.calc(3.75, 1.4, 'multiply'), 5.25); assert.equal(d.calc(0.05, 0.05, 'multiply'), 0.0025);
  assert.equal(d.round(5.25, 1), 5.3); assert.equal(d.round(2.45, 0), 2); assert.equal(d.places(0.0025), 4); assert.equal(d.places(5), 0); assert.equal(d.show(-2.35), '−2.35');
  const f = load('math/fraction-arithmetic'); assert.deepEqual(f.calc(2, 3, 3, 4, 'add'), [17, 12]); assert.deepEqual(f.calc(2, 3, 3, 4, 'subtract'), [-1, 12]); assert.deepEqual(f.calc(2, 3, 3, 4, 'multiply'), [1, 2]); assert.deepEqual(f.calc(2, 3, 3, 4, 'divide'), [8, 9]);
  assert.equal(f.calc(1, 2, 0, 5, 'divide'), null); assert.equal(f.lcm(3, 4), 12); assert.equal(f.lcm(6, 4), 12); assert.equal(f.compare(2, 3, 3, 4), -1); assert.equal(f.compare(2, 4, 1, 2), 0); assert.equal(f.mixed([17, 12]), '1 and 5/12'); assert.equal(f.text([4, 1]), '4'); assert.equal(f.text([-1, 12]), '−1/12');
  const g = load('math/area-perimeter-volume'), val = (shape, a, b, cc, name) => g.measure(shape, a, b, cc).find(r => r[0] === name)[2];
  assert.equal(val('rectangle', 6, 4, 1, 'Area'), 24); assert.equal(val('rectangle', 6, 4, 1, 'Perimeter'), 20); assert.equal(val('triangle', 3, 4, 1, 'Longest side'), 5); assert.equal(val('triangle', 3, 4, 1, 'Area'), 6); assert.equal(val('triangle', 3, 4, 1, 'Perimeter'), 12);
  near(val('circle', 2, 1, 1, 'Area'), 4 * Math.PI); near(val('circle', 2, 1, 1, 'Circumference'), 4 * Math.PI); assert.equal(val('cuboid', 2, 3, 4, 'Volume'), 24); assert.equal(val('cuboid', 2, 3, 4, 'Surface area'), 52); assert.equal(val('cuboid', 2, 3, 4, 'Total edge length'), 36);
  const p = load('math/percent-grid'); assert.deepEqual(p.fraction(35), [7, 20]); assert.deepEqual(p.fraction(50), [1, 2]); assert.deepEqual(p.fraction(100), [1, 1]); assert.deepEqual(p.fraction(0), [0, 1]); assert.equal(p.of(35, 80), 28); assert.equal(p.increase(10, 80), 88); assert.equal(p.decrease(10, 88), 79.2);
  const r = load('math/ratio-sharing'); assert.deepEqual(r.simplify(4, 6), [2, 3]); assert.deepEqual(r.share(60, 2, 3), {part: 12, first: 24, second: 36}); assert.deepEqual(r.scale(2, 3, 5), [10, 15]); assert.equal(r.proportion(2, 3, 10), 15);
});

test('secondary mathematics: functions, linear and quadratic equations, polynomials, slope and vectors', () => {
  const f = load('math/compose-functions'); assert.equal(f.apply('double', 2), 5); assert.equal(f.compose('double', 'square', 2), 9); assert.equal(f.compose('square', 'double', 2), 25); assert.equal(f.commute('double', 'square'), false); assert.equal(f.commute('shift', 'shift'), true); assert.equal(f.commute('half', 'abs'), true);
  const l = load('math/solve-linear'); assert.deepEqual(l.solve(2, -3, -1, 6), {kind: 'one', x: 3, y: 3}); assert.deepEqual(l.solve(2, 1, 2, 5), {kind: 'none'}); assert.deepEqual(l.solve(2, 1, 2, 1), {kind: 'all'});
  assert.equal(l.side(2, -3), '2x − 3'); assert.equal(l.side(-1, 6), '−x + 6'); assert.equal(l.side(0, -4), '−4'); assert.equal(l.side(3, 0), '3x'); assert.equal(l.side(0, 0), '0'); assert.equal(l.side(1, 2), 'x + 2');
  const p = load('math/polynomial-roots'); assert.deepEqual(p.expand(1, [-2, 1, 3]), [1, -2, -5, 6]); assert.equal(p.text([1, -2, -5, 6]), 'x³ − 2x² − 5x + 6'); assert.equal(p.text([-1, 0, 1, 0]), '−x³ + x'); assert.equal(p.text([0, 0, 0, 0]), '0');
  for (const r of [-2, 1, 3]) assert.equal(p.value([1, -2, -5, 6], r), 0); assert.equal(p.value([1, -2, -5, 6], 0), 6); assert.equal(p.factored(2, [-2, 0, 3]), '2(x + 2)x(x − 3)'); assert.deepEqual(p.expand(2, [1, 1, 1]), [2, -6, 6, -2]);
  const q = load('math/quadratic-solver'); assert.deepEqual(q.solve(1, -2, -3), {D: 16, h: 1, k: -4, kind: 'two', roots: [-1, 3]}); assert.deepEqual(q.solve(1, -4, 4), {D: 0, h: 2, k: 0, kind: 'one', roots: [2]});
  const c = q.solve(1, 2, 5); assert.deepEqual([c.kind, c.re, c.im, c.D], ['complex', -1, 2, -16]); assert.equal(q.solve(0, 2, 5), null); assert.deepEqual(q.solve(-1, 0, 4).roots, [-2, 2]);
  const s = load('math/slope-between-points'); const line = s.line(-2, -1, 4, 3); near(line.m, 2 / 3); near(line.b, 1 / 3); near(line.perpendicular, -1.5); assert.deepEqual(s.line(2, 1, 2, 5), {kind: 'vertical', x: 2}); assert.deepEqual(s.line(1, 1, 1, 1), {kind: 'point'}); assert.equal(s.line(0, 3, 4, 3).perpendicular, null);
  const v = load('math/vector-sum-dot'); assert.deepEqual(v.add([3, 1], [1, 4]), [4, 5]); assert.equal(v.dot([3, 1], [1, 4]), 7); assert.equal(v.length([3, 4]), 5); near(v.angle([1, 0], [0, 2]), 90); near(v.angle([1, 0], [-3, 0]), 180); assert.equal(v.angle([0, 0], [1, 1]), null); near(v.projection([3, 4], [1, 0]), 3);
});

test('university mathematics I: convergence, sets, matrices, gradients, number theory and the binomial', () => {
  const a = load('math/epsilon-n'); assert.equal(a.threshold('inv', 0.1), 11); assert.equal(a.threshold('ratio', 0.1), 11); assert.equal(a.threshold('alt', 0.25), 5); assert.equal(a.threshold('geo', 0.1), 4); assert.equal(a.threshold('inv', 0.5), 3);
  for (const name of Object.keys(a.SEQUENCES)) for (const eps of [0.5, 0.2, 0.05, 0.01]) { const N = a.threshold(name, eps); for (let n = N; n < N + 50; n++) assert.ok(a.gap(name, n) < eps, name); if (N > 1) assert.ok(a.gap(name, N - 1) >= eps - 1e-12, name); }
  const d = load('math/set-operations'); assert.deepEqual(d.members('prime'), [2, 3, 5, 7, 11]); assert.deepEqual(d.intersection('even', 'three'), [6, 12]); assert.equal(d.union('even', 'three').length, 8); assert.deepEqual(d.difference('prime', 'odd'), [2]); assert.deepEqual(d.complement('big'), [1, 2, 3, 4, 5, 6]); assert.equal(d.subsets(5), 32);
  for (const x of Object.keys(d.SETS)) for (const y of Object.keys(d.SETS)) assert.equal(d.union(x, y).length, d.members(x).length + d.members(y).length - d.intersection(x, y).length);
  const m = load('math/matrix-transform'); assert.equal(m.det(2, 1, 1, 2), 3); assert.equal(m.trace(2, 1, 1, 2), 4); assert.deepEqual(m.eigen(2, 1, 1, 2), {real: true, values: [3, 1]}); assert.deepEqual(m.eigen(0, -1, 1, 0), {real: false, re: 0, im: 1});
  assert.deepEqual(m.apply(2, 1, 1, 2, 1, 1), [3, 3]); assert.equal(m.inverse(1, 2, 2, 4), null); assert.deepEqual(m.inverse(2, 0, 0, 4), [0.5, 0, 0, 0.25]); assert.deepEqual(m.inverse(2, 1, 1, 1), [1, -1, -1, 2]);
  const g = load('math/gradient-field'); assert.deepEqual(g.gradient('bowl', 1, 0.5), [2, 1]); assert.deepEqual(g.gradient('saddle', 1, 0.5), [2, -1]); assert.deepEqual(g.gradient('product', 1, 0.5), [0.5, 1]); near(g.directional('bowl', 1, 0, 0), 2); near(g.directional('bowl', 1, 0, 90), 0); near(g.directional('bowl', 1, 0, 180), -2); near(g.steepest('bowl', 3, 4), 10);
  for (let deg = 0; deg < 360; deg += 15) assert.ok(g.directional('saddle', 1, 0.5, deg) <= g.steepest('saddle', 1, 0.5) + 1e-9);
  const n = load('math/modular-clock'); assert.deepEqual(n.euclid(14, 45).steps.map(x => x.r), [14, 3, 2, 1, 0]); assert.equal(n.gcd(14, 45), 1); assert.equal(n.gcd(48, 18), 6); assert.equal(n.inverse(14, 45), 29); assert.equal(n.inverse(6, 9), null); assert.equal(n.power(3, 4, 7), 4); assert.equal(n.power(2, 10, 1000), 24);
  assert.equal(n.multiples(6, 9).length, 3); assert.equal(n.multiples(14, 45).length, 45); assert.equal(n.isPrime(47), true); assert.equal(n.isPrime(49), false); for (let x = 1; x < 13; x++) assert.equal(n.power(x, 12, 13), 1);
  const b = load('math/binomial-distribution'); assert.equal(b.choose(10, 3), 120); assert.equal(b.choose(30, 15), 155117520); assert.equal(b.choose(5, 7), 0); near(b.pmf(10, 0.3, 3), 0.266827932, 1e-9); near(b.cdf(10, 0.5, 10), 1); near(b.cdf(4, 0.5, 1), 5 / 16); assert.equal(b.mean(10, 0.3), 3); near(b.variance(10, 0.3), 2.1); assert.equal(b.pmf(5, 0, 0), 1); assert.equal(b.pmf(5, 1, 5), 1);
});

test('university mathematics II: groups, complex maps, curvature, Collatz, Fourier, logic, Cantor, Newton, heat and Euler', () => {
  const a = load('math/cyclic-subgroups'); assert.deepEqual(a.generated(12, 8), [0, 8, 4]); assert.equal(a.order(12, 8), 3); assert.equal(a.index(12, 8), 4); assert.equal(a.order(12, 0), 1); assert.equal(a.order(12, 5), 12); assert.deepEqual(a.generators(12), [1, 5, 7, 11]); assert.deepEqual(a.divisors(12), [1, 2, 3, 4, 6, 12]);
  for (let n = 2; n <= 24; n++) for (let g = 0; g < n; g++) { assert.equal(a.generated(n, g).length, a.order(n, g)); assert.equal(n % a.order(n, g), 0); }
  const c = load('math/complex-mapping'); assert.deepEqual(c.apply('square', 1, 1), [0, 2]); assert.deepEqual(c.apply('inverse', 0, 2), [0, -0.5]); assert.equal(c.apply('inverse', 0, 0), null); near(c.apply('exp', 0, Math.PI)[0], -1); near(c.apply('exp', 0, Math.PI)[1], 0); assert.deepEqual(c.derivative('square', 1, 0.5), [2, 1]);
  near(c.derivative('inverse', 0, 1)[0], 1); near(c.derivative('inverse', 0, 1)[1], 0); near(c.derivative('inverse', 2, 0)[0], -0.25); assert.equal(c.modulus([3, 4]), 5); near(c.argument([0, 2]), 90); near(c.argument([-1, 0]), 180);
  const k = load('math/curvature-circle'); assert.equal(k.curvature(0.5, 0), 1); assert.equal(k.radius(0.5, 0), 1); assert.deepEqual(k.centre(0.5, 0), [0, 1]); near(k.curvature(1, 1), 2 / 5 ** 1.5); assert.equal(k.radius(0, 1), Infinity); assert.equal(k.centre(0, 1), null); near(k.centre(1, 1)[0], -4); near(k.centre(1, 1)[1], 3.5); assert.equal(k.curvature(-1, 0), -2);
  { const [cx, cy] = k.centre(1, 1); near(Math.hypot(1 - cx, 1 - cy), k.radius(1, 1)); }
  const z = load('math/collatz-orbits'); assert.deepEqual(z.orbit(6), [6, 3, 10, 5, 16, 8, 4, 2, 1]); assert.equal(z.steps(27), 111); assert.equal(z.peak(27), 9232); assert.equal(z.steps(1), 0); assert.equal(z.longest(10), 9); assert.equal(z.longest(200), 171); assert.equal(z.steps(171), 124);
  const w = load('math/fourier-square-wave'); near(w.partial(1, Math.PI / 2), 4 / Math.PI); near(w.partial(2, Math.PI / 2), 4 / Math.PI * (1 - 1 / 3)); near(w.energy(1), 8 / Math.PI ** 2); assert.ok(w.energy(25) > 0.99 && w.energy(25) < 1); assert.ok(w.error(25) < w.error(5) && w.error(5) < w.error(1));
  near(w.partial(200, Math.PI / 2), 1, 0.01); assert.ok(w.overshoot(25) > 1.17 && w.overshoot(25) < 1.19); assert.equal(w.square(1), 1); assert.equal(w.square(-1), -1);
  const t = load('math/truth-tables'); assert.deepEqual(t.table('imp'), [true, false, true, true]); assert.equal(t.equivalent('imp', 'ornot'), true); assert.equal(t.equivalent('imp', 'contra'), true); assert.equal(t.equivalent('imp', 'conv'), false); assert.equal(t.equivalent('nand', 'demorgan'), true); assert.equal(t.equivalent('nor', 'demorgan2'), true);
  assert.equal(t.equivalent('iff', 'both'), true); assert.equal(t.tautology('taut'), true); assert.equal(t.contradiction('absurd'), true); assert.equal(t.tautology('imp'), false); assert.equal(t.equivalent('and', 'demorgan'), false);
  const s = load('math/cantor-set'); { const one = s.intervals(1); assert.equal(one.length, 2); near(one[0][1], 1 / 3); near(one[1][0], 2 / 3); assert.equal(one[0][0], 0); assert.equal(one[1][1], 1); } assert.equal(s.intervals(5).length, 32); assert.equal(s.count(7), 128); near(s.length(2), 4 / 9); near(s.removed(2), 5 / 9); assert.equal(s.contains(0.25, 7), true); assert.equal(s.contains(0.5, 1), false); assert.equal(s.contains(1 / 3, 7), true);
  near(s.intervals(4).reduce((sum, [x, y]) => sum + y - x, 0), s.length(4));
  const m = load('math/newton-iteration'); assert.equal(m.step(2, 1), 1.5); assert.equal(m.iterate(2, 1, 2).length, 3); near(m.iterate(2, 1, 2)[2], 17 / 12); near(m.iterate(2, 1, 6)[6], Math.SQRT2, 1e-15); assert.equal(m.digits(2, Math.SQRT2), 16); assert.equal(m.digits(2, 1.5), 1); assert.ok(m.digits(2, m.iterate(2, 1, 4)[4]) >= 11); near(m.bisect(2, 0, 2, 40), Math.SQRT2, 1e-9);
  const h = load('math/heat-equation'); assert.equal(h.decay(1, 0), 1); near(h.decay(3, 1), h.decay(1, 1) ** 9); near(h.halfLife(1), Math.log(2) / (0.1 * Math.PI ** 2)); near(h.decay(2, h.halfLife(2)), 0.5); near(h.u('mode1', 0.5, 0), 1); near(h.u('mix', 0.5, 0), 0.5); near(h.u('mix', 0, 3), 0); near(h.u('mix', 1, 3), 0, 1e-12);
  { const dx = 1e-4, dt = 1e-5, x = 0.3, time = 0.7, ut = (h.u('mix', x, time + dt) - h.u('mix', x, time - dt)) / (2 * dt), uxx = (h.u('mix', x + dx, time) - 2 * h.u('mix', x, time) + h.u('mix', x - dx, time)) / dx ** 2; near(ut, h.ALPHA * uxx, 1e-5); }
  const e = load('math/euler-characteristic'); for (const name of ['tetrahedron', 'cube', 'octahedron', 'dodecahedron', 'icosahedron', 'prism']) { assert.equal(e.characteristic(name), 2); assert.equal(e.genus(name), 0); }
  assert.equal(e.characteristic('torus'), 0); assert.equal(e.genus('torus'), 1); assert.equal(e.characteristic('doubletorus'), -2); assert.equal(e.genus('doubletorus'), 2);
});

test('early physics: heat flow, shadows, forces, energy, magnets, motion, circuits, heating, measurement', () => {
  const h = load('physics/heat-flows'); assert.deepEqual(h.temps(80, 20, 0), [80, 20]); assert.equal(h.final(80, 20), 50); near(h.temps(80, 20, 500)[0], 50, 1e-6); near(h.temps(80, 20, 3)[0] + h.temps(80, 20, 3)[1], 100); assert.equal(h.direction(20, 80), 'second to first'); assert.equal(h.direction(5, 5), 'none');
  const s = load('physics/shadow-length'); near(s.shadow(5, 1.5, 3), 4.5 / 3.5); assert.equal(s.shadow(2, 3, 4), Infinity); assert.equal(s.shadow(4, 2, 3), 3); assert.ok(s.shadow(3, 1.5, 3) > s.shadow(6, 1.5, 3));
  const f = load('physics/balanced-forces'); assert.equal(f.net(6, 2), 4); assert.equal(f.outcome(3, 3), 'no change in motion'); assert.equal(f.outcome(1, 4), 'speeds up to the left');
  const e = load('physics/falling-energy'); const r = e.energy(1, 10, 40); near(r.y, 6); near(r.stored, 58.8); near(r.moving, 39.2); near(r.total, 98); near(r.speed, Math.sqrt(78.4)); for (const pc of [0, 25, 100]) { const q = e.energy(2, 7, pc); near(q.stored + q.moving, q.total); }
  const m = load('physics/compass-field'); assert.deepEqual(m.field(2, 0), [1, 0]); near(m.field(0, 2)[0], -1); near(m.angle(0, 2), 180); near(m.field(1, 1)[0], 1 / Math.sqrt(10)); near(m.field(1, 1)[1], 3 / Math.sqrt(10)); assert.equal(m.field(0, 0), null); assert.deepEqual(m.field(-3, 0), [1, 0]); assert.equal(m.force('N', 'N'), 'repel'); assert.equal(m.force('N', 'S'), 'attract');
  const d = load('physics/distance-speed-time'); assert.equal(d.distance(5, 8), 40); assert.equal(d.travelled(5, 8, 0), 40); assert.equal(d.stopTime(5, 1), 5); assert.equal(d.travelled(5, 8, 1), 12.5); assert.equal(d.speedAt(5, 8, 1), 0); assert.equal(d.speedAt(5, 2, 1), 3); assert.equal(d.stopTime(5, 0), Infinity);
  const c = load('physics/series-parallel'); const se = c.circuit('series', 6, 6, 12); near(se.current, 1 / 3); near(se.bulbs[0].volts, 2); near(se.bulbs[1].volts, 4); near(se.power, 2); near(se.bulbs[0].power + se.bulbs[1].power, se.power);
  const pa = c.circuit('parallel', 6, 6, 12); near(pa.total, 4); near(pa.current, 1.5); near(pa.bulbs[0].power, 6); near(pa.bulbs[1].power, 3); near(pa.bulbs[0].current + pa.bulbs[1].current, pa.current);
  const w = load('physics/heating-curve'); assert.deepEqual(w.stages(), [42, 376, 794, 3054]); near(w.state(21).temperature, -10); assert.equal(w.state(209).temperature, 0); near(w.state(209).melted, 0.5); near(w.state(585).temperature, 50); near(w.state(1924).boiled, 0.5); near(w.state(3074).temperature, 110); assert.equal(w.state(0).phase, 'solid (ice)');
  const u = load('physics/measurement-uncertainty'); assert.equal(u.uncertainty(1), 0.5); near(u.relative(47, 1), 50 / 47); assert.equal(u.significant(47, 1), 50); assert.equal(u.significant(0.012345, 2), 0.012); assert.equal(u.significant(1234, 2), 1200); assert.equal(u.scientific(0.047), '4.7 × 10^-2'); assert.equal(u.convert(47, 1e-3), 0.047);
});

test('secondary and university physics I: induction, collisions, Carnot, waves, pipes, quarks, the box', () => {
  const f = load('physics/faraday-induction'); near(f.emf(50, 20, 0, 0.5, 0.5), -0.1); assert.equal(Math.abs(f.emf(50, 20, 0.3, 0.3, 0.5)), 0); near(f.emf(100, 20, 0.5, 0, 0.5), 0.2); near(f.flux(0.5, 20), 1e-3);
  const c = load('physics/collision-lab'); const [a, b] = c.collide(2, 6, 4, -1, 1); near(a, -10 / 3); near(b, 11 / 3); near(c.kinetic(2, a, 4, b), c.kinetic(2, 6, 4, -1)); const [x, y] = c.collide(2, 6, 4, -1, 0); near(x, 4 / 3); near(y, 4 / 3);
  for (const e of [0, 0.3, 0.7, 1]) { const [p, q] = c.collide(3, 5, 7, -2, e); near(c.momentum(3, p, 7, q), c.momentum(3, 5, 7, -2)); near(q - p, e * (5 - -2)); assert.ok(c.kinetic(3, p, 7, q) <= c.kinetic(3, 5, 7, -2) + 1e-9); }
  assert.equal(c.approaching(6, -1), true); assert.equal(c.approaching(1, 3), false);
  const k = load('physics/carnot-engine'); assert.equal(k.limit(800, 300), 0.625); assert.deepEqual(k.flows(1000, 0.625), {work: 625, waste: 375}); near(k.entropy(800, 300, 1000, 0.625), 0); near(k.entropy(800, 300, 1000, 0.35), -1.25 + 650 / 300); assert.equal(k.possible(800, 300, 0.7), false); assert.equal(k.possible(800, 300, 0.625), true); assert.equal(k.limit(300, 300), 0); assert.ok(k.entropy(800, 300, 1000, 0.7) < 0);
  const w = load('physics/em-spectrum'); near(w.wavelength(5e14), 5.99584916e-7, 1e-15); near(w.photon(5e14), 2.0678, 1e-4); assert.equal(w.band(5e14), 'visible light'); assert.equal(w.band(1e8), 'radio waves'); assert.equal(w.band(1e10), 'microwaves'); assert.equal(w.band(1e13), 'infrared'); assert.equal(w.band(1e16), 'ultraviolet'); assert.equal(w.band(1e18), 'X-rays'); assert.equal(w.band(1e20), 'gamma rays'); assert.equal(w.scientific(299792458), '3 × 10^8');
  const p = load('physics/pipe-flow'); assert.equal(p.speed(20, 5, 2), 8); near(p.flow(20, 2), 4); near(p.flow(5, 8), 4); assert.equal(p.drop(20, 5, 2), 30000); assert.equal(p.drop(20, 20, 2), 0); assert.ok(p.drop(5, 20, 2) < 0);
  const q = load('physics/quark-charges'); assert.deepEqual(['proton', 'neutron', 'piplus', 'piminus', 'kplus', 'lambda', 'omega', 'deltapp'].map(q.charge), [1, 0, 1, -1, 1, 0, -1, 2]); assert.equal(q.baryonNumber('proton'), 1); assert.equal(q.baryonNumber('piplus'), 0); assert.equal(q.PARTICLES.length, 17);
  assert.equal(q.PARTICLES.filter(row => row[1] === 'quark').length, 6); assert.equal(q.PARTICLES.filter(row => row[1] === 'lepton').length, 6); assert.equal(q.kind('kplus'), 'meson (a quark and an antiquark)');
  const z = load('physics/particle-in-a-box'); near(z.energy(1, 1), 0.37603, 1e-4); near(z.energy(2, 1), 4 * z.energy(1, 1)); near(z.energy(1, 0.5), 4 * z.energy(1, 1)); near(z.probability(3, 0, 1), 1); near(z.probability(1, 1 / 3, 2 / 3), 1 / 3 + Math.sqrt(3) / (2 * Math.PI)); near(z.probability(2, 0, 0.5), 0.5); assert.equal(z.nodes(4), 3);
  near(z.photon(2, 1, 1), 1239.841984 / (3 * z.energy(1, 1))); { let sum = 0; for (let i = 0; i < 20000; i++) sum += z.density(3, (i + 0.5) / 20000) / 20000; near(sum, 1, 1e-6); }
});

test('university physics II: Lorentz transforms, band gaps, microstates, black holes, force range, qubits', () => {
  const l = load('physics/lorentz-transform'); near(l.gamma(0.6), 1.25); const [x, t] = l.transform(0.6, 2, 3); near(x, 0.25); near(t, 2.25); near(l.interval(x, t), l.interval(2, 3)); near(l.addVelocities(0.6, 0.5), 1.1 / 1.3); assert.ok(l.addVelocities(0.9, 0.9) < 1);
  assert.equal(l.kind(2, 3), 'time-like'); assert.equal(l.kind(3, 2), 'space-like'); assert.equal(l.kind(2, 2), 'light-like'); for (const v of [-0.9, -0.3, 0.45, 0.9]) { const [a, b] = l.transform(v, -1.5, 2.75); near(l.interval(a, b), l.interval(-1.5, 2.75), 1e-9); const [c, d] = l.transform(-v, a, b); near(c, -1.5); near(d, 2.75); }
  const g = load('physics/band-gap'); near(g.cutoff(1.12), 1107.0, 0.05); assert.equal(g.light(1.12), 'infrared'); assert.equal(g.light(5.47), 'ultraviolet'); near(g.factor(1.12, 300), Math.exp(-1.12 / (2 * 8.617333262e-5 * 300))); assert.ok(g.factor(0.67, 300) > g.factor(1.12, 300)); assert.ok(g.growth(1.12, 300, 400) > 100); near(g.thermal(300), 0.025852, 1e-6);
  const m = load('physics/counting-microstates'); assert.equal(m.multiplicity(10, 5), 252); assert.equal(m.total(10), 1024); assert.equal(m.multiplicity(40, 20), 137846528820); near(m.entropy(10, 5), Math.log(252)); near(m.near(10, 0.1), 672 / 1024); assert.equal(m.entropy(10, 0), 0);
  for (const n of [2, 7, 40]) { let sum = 0; for (let k = 0; k <= n; k++) sum += m.multiplicity(n, k); assert.equal(sum, 2 ** n); } assert.ok(m.near(40, 0.1) > m.near(10, 0.1));
  const b = load('physics/black-hole-time'); near(b.radius(10), 29.53); near(b.rate(3), Math.sqrt(2 / 3)); assert.equal(b.escape(4), 0.5); near(b.redshift(4 / 3), 2); near(b.lostPerDay(2), 86400 * (1 - Math.SQRT1_2)); assert.ok(b.rate(1.05) < b.rate(20)); assert.equal(b.scientific(29.53), '29.53'); assert.equal(b.scientific(2.953e10), '2.95 × 10^10');
  const r = load('physics/force-range'); near(r.range('pion'), 197.3269804 / 139.57); near(r.range('w'), 0.002455, 1e-6); assert.equal(r.range('photon'), Infinity); near(r.suppression('pion', r.range('pion')), Math.exp(-1)); assert.equal(r.suppression('photon', 3), 1); near(r.potential('photon', 2), 0.5);
  const q = load('physics/qubit-gates'), P = (theta, phi, gate) => q.probabilities(q.apply(gate, q.state(theta, phi)));
  near(P(0, 0, 'none')[0], 1); near(P(0, 0, 'H')[0], 0.5); near(P(0, 0, 'X')[1], 1); near(P(90, 0, 'H')[0], 1); near(P(90, 180, 'H')[1], 1); near(P(90, 90, 'H')[0], 0.5); near(P(60, 0, 'Z')[0], 0.75);
  { const B = q.bloch(q.state(90, 0)); near(B[0], 1); near(B[1], 0); near(B[2], 0); const C = q.bloch(q.state(90, 90)); near(C[1], 1); const Z = q.bloch(q.apply('Z', q.state(90, 0))); near(Z[0], -1); const H = q.bloch(q.apply('H', q.state(0, 0))); near(H[0], 1); near(H[2], 0); }
  for (const gate of ['H', 'X', 'Z', 'none']) for (const [theta, phi] of [[30, 45], [120, 300], [180, 0]]) { const pr = P(theta, phi, gate); near(pr[0] + pr[1], 1); const B = q.bloch(q.apply(gate, q.state(theta, phi))); near(Math.hypot(...B), 1); }
});

test('rainbow traces agree with independent turning angles and the visible bow limits', async () => {
  const { angularRadius, causticHeight, radians, skyElevation, traceRay, visibleHalfArc, waterIndex } =
    await import('../web/physics/rainbow-ray-tracing/optics.mjs');

  const sodiumIndex = waterIndex(589.3);
  near(sodiumIndex, 1.33335, 0.00001);
  for (const wavelength of [400, 485, 560, 589.3, 650, 700]) {
    const index = waterIndex(wavelength);
    for (const reflections of [1, 2]) {
      const peak = causticHeight(index, reflections);
      const radius = angularRadius(peak, index, reflections);
      for (let step = 0; step < 200; step++) {
        const height = step / 200;
        const ray = traceRay(height, index, reflections);
        assert.equal(ray.points.length, reflections + 2);
        for (const point of ray.points) near(Math.hypot(...point), 1, 1e-11);
        near(ray.points[0][1], height);
        near(Math.hypot(...ray.outgoing), 1, 1e-11);
        near(Math.atan2(Math.abs(ray.outgoing[1]), -ray.outgoing[0]),
          angularRadius(height, index, reflections), 1e-10);
        assert.ok(ray.power >= 0 && ray.power <= 1);
      }
      const normalReflectance = ((index - 1) / (index + 1)) ** 2;
      near(traceRay(0, index, reflections).power,
        (1 - normalReflectance) ** 2 * normalReflectance ** reflections);
      for (const direction of [-1, 1]) {
        const neighbour = angularRadius(peak + direction * 0.001, index, reflections);
        assert.ok(reflections === 1 ? neighbour < radius : neighbour > radius);
      }
      near(skyElevation(radius, 10 * radians, 0), radius - 10 * radians);
      near(skyElevation(radius, 10 * radians, visibleHalfArc(radius, 10 * radians)), 0);
      near(visibleHalfArc(radius, 0), Math.PI / 2);
      assert.equal(visibleHalfArc(radius, 60 * radians), 0);
    }
  }

  const causticDegrees = (nm, reflections) => {
    const index = waterIndex(nm);
    return angularRadius(causticHeight(index, reflections), index, reflections) / radians;
  };
  near(causticDegrees(700, 1), 42.4, 0.1);
  near(causticDegrees(700, 2), 50.2, 0.1);
  assert.ok(causticDegrees(700, 1) > causticDegrees(400, 1));
  assert.ok(causticDegrees(700, 2) < causticDegrees(400, 2));
});

test('Labov store observations keep all four Table 13.1 categories and their denominators', async () => {
  const { STORES, observations, largestChange } = await import('../web/language/department-store-r/model.mjs');
  assert.equal(STORES.map(store => store.interviews).reduce((sum, n) => sum + n), 264);
  for (const word of ['floor', 'fourth']) {
    for (const mode of ['pronounced', 'coverage']) {
      const stores = observations(word, mode);
      for (const store of stores) {
        for (const row of store.replies) {
          assert.equal(row.present + row.absent + row.doubtful + row.missing, store.interviews);
          assert.equal(row.whole, mode === 'pronounced' ? row.present + row.absent : store.interviews);
          assert.equal(row.proportion, row.part / row.whole);
        }
      }
    }
  }
  const [first, repeat] = observations('floor', 'pronounced')[1].replies;
  assert.deepEqual([first.present, first.whole, repeat.present, repeat.whole, repeat.missing], [48, 110, 31, 51, 74]);
  assert.deepEqual(observations('fourth', 'coverage')[0].replies.map(row => row.doubtful), [4, 4]);
  near(largestChange(observations('floor', 'pronounced'), 'pronounced').points, 17.147950089126556, 1e-9);
  assert.equal(largestChange(observations('fourth', 'pronounced'), 'pronounced').name, 'Saks');
  const coverage = largestChange(observations('floor', 'coverage'), 'coverage');
  assert.equal(coverage.name, 'Macy’s');
  near(coverage.points, -47.2, 1e-10);
});

test('finite source shadows agree with independent ray interception and point-source limits', async () => {
  const { blockerRadius, circleOverlap, lampView, shadowEdges } = await import('../web/physics/soft-shadow/geometry.mjs');
  near(circleOverlap(1, 1, 1), 2 * Math.PI / 3 - Math.sqrt(3) / 2);
  near(circleOverlap(2, 3, 0), 4 * Math.PI);
  near(circleOverlap(2, 3, 5), 0);
  for (const distance of [30, 50, 80]) {
    const expected = blockerRadius * 100 / distance;
    near(shadowEdges(0, distance).inner, expected);
    near(shadowEdges(0, distance).outer, expected);
    assert.equal(lampView(0, distance, expected - 0.001).visible, 0);
    assert.equal(lampView(0, distance, expected + 0.001).visible, 1);
    for (const radius of [1, 6, 14]) {
      const edges = shadowEdges(radius, distance);
      if (edges.inner > 0) near(lampView(radius, distance, edges.inner).visible, 0, 1e-8);
      near(lampView(radius, distance, edges.outer).visible, 1, 1e-8);
      for (const point of [0, 4, 11, 17, 30, 56]) {
        const view = lampView(radius, distance, point);
        near(view.visible, lampView(radius, distance, -point).visible);
        assert.ok(view.visible >= 0 && view.visible <= 1);
        let illuminated = 0, total = 0;
        // Each grid point stands for the same source area. Test the light ray
        // at the blocker directly, independently of circle intersection areas.
        const samples = 220;
        const f = distance / 100;
        for (let row = 0; row < samples; row++) {
          const y = radius * (2 * (row + 0.5) / samples - 1);
          for (let col = 0; col < samples; col++) {
            const x = radius * (2 * (col + 0.5) / samples - 1);
            if (x * x + y * y > radius * radius) continue;
            total++;
            const hitX = (1 - f) * x + f * point;
            const hitY = (1 - f) * y;
            if (hitX * hitX + hitY * hitY > blockerRadius * blockerRadius) illuminated++;
          }
        }
        near(view.visible, illuminated / total, 0.0015);
      }
    }
  }
  // A wider lamp can remain partly visible at the centre beyond the umbra.
  near(lampView(14, 30, 0).visible, 1 - (6 / 0.7 / 14) ** 2);
  assert.equal(lampView(14, 30, 0).kind, 'partial');
  assert.equal(lampView(1, 50, 0).kind, 'dark');
  assert.equal(lampView(1, 50, 56).kind, 'lit');
});

test('Wonderland samples retain chapter offsets and distinguish cumulative from local diversity', async () => {
  const { tokenize, traceWords, frequentForms } = await import('../web/language/word-samples/counts.mjs');
  const book = JSON.parse(fs.readFileSync(path.join(root, 'language/word-samples/corpus.json'), 'utf8'));
  const sizes = [2157, 2115, 1702, 2658, 2172, 2609, 2307, 2493, 2294, 2038, 1898, 2127];
  assert.equal(book.chapters.length, sizes.length);
  assert.equal(book.chapters.reduce((sum, chapter) => sum + chapter.illustrations.length, 0), 41);
  assert.deepEqual(tokenize("Rabbit rabbit’s rabbit's rabbit-hole").map(word => word.form),
    ['rabbit', "rabbit's", "rabbit's", 'rabbit', 'hole']);
  assert.deepEqual(tokenize('Alice ALICE', true).map(word => word.form), ['Alice', 'ALICE']);
  for (const [index, chapter] of book.chapters.entries()) {
    for (const keepCase of [false, true]) {
      const tokens = tokenize(chapter.text, keepCase);
      assert.equal(tokens.length, sizes[index]);
      const first = Math.floor(tokens.length / 2);
      const words = tokens.slice(first, first + 80);
      for (const word of words) assert.equal(chapter.text.slice(word.start, word.end), word.text);
      const trace = traceWords(words);
      for (const count of [1, 24, 25, 26, 80]) {
        const forms = words.slice(0, count).map(word => word.form);
        const types = new Set(forms).size;
        const state = trace[count - 1];
        assert.equal(state.ratio, types / count);
        assert.equal(state.first, forms.indexOf(forms[count - 1]));
        assert.equal(state.count, forms.filter(form => form === forms[count - 1]).length);
        const windows = [];
        for (let i = 25; i <= count; i++) windows.push(new Set(forms.slice(i - 25, i)).size);
        assert.equal(state.meanLocalRatio, windows.length ? windows.reduce((a, b) => a + b, 0) / (25 * windows.length) : null);
      }
    }
    for (const figure of chapter.illustrations) {
      assert.ok(figure.offset >= 0 && figure.offset <= chapter.text.length);
      for (const link of [figure.file, figure.large]) assert.ok(fs.existsSync(path.join(root, link.slice('/app/'.length))), link);
    }
  }
  const opening = tokenize(book.chapters[0].text).slice(0, 25);
  assert.equal(traceWords(opening)[24].types, 23);
  assert.deepEqual(frequentForms(opening, 25).slice(0, 2), [['to', 2], ['of', 2]]);
});

test('circular arrangement classes agree with explicit necklaces and bracelets', async () => {
  const { analyse } = await import('../web/math/circular-arrangements/symmetry.mjs');
  // Independently rotate and reverse literal strings and count equivalence classes.
  const rotations = word => Array.from({ length: word.length }, (_, i) => word.slice(i) + word.slice(0, i));
  for (let n = 3; n <= 12; n++) {
    for (const flip of [false, true]) {
      const classes = Array.from({ length: n + 1 }, () => new Set());
      const populations = Array(n + 1).fill(0);
      for (let bits = 0; bits < 2 ** n; bits++) {
        const word = bits.toString(2).padStart(n, '0');
        const k = [...word].filter(bit => bit === '1').length;
        const views = rotations(word);
        if (flip) views.push(...rotations([...word].reverse().join('')));
        classes[k].add(views.sort()[0]);
        populations[k]++;
      }
      for (let k = 0; k <= n; k++) {
        const pattern = Array.from({ length: n }, (_, i) => Number(i < k));
        const result = analyse(pattern, false, flip);
        assert.equal(result.labelled, populations[k]);
        assert.equal(result.classes, classes[k].size);
        assert.equal(result.orbitSize * result.stabilizer, result.results.length);
      }
    }
  }
  const alternating = analyse([0, 1, 0, 1, 0, 1], false, false);
  assert.deepEqual(alternating.results.map(row => row.fixedCount), [20, 0, 2, 0, 2, 0]);
  assert.equal(alternating.orbitSize, 2);
  assert.equal(alternating.classes, 4);
  const guests = Array.from({ length: 8 }, (_, i) => i);
  assert.equal(analyse(guests, true, false).classes, 5040);
  assert.equal(analyse(guests, true, true).classes, 2520);
});

test('every registered activity has its page, script and a return link to its module', () => {
  const registry = JSON.parse(fs.readFileSync(path.join(root, 'activities', 'registry.json'), 'utf8'));
  const curriculum = fs.readdirSync(path.join(root, '..', 'data', 'curriculum')).map(f => fs.readFileSync(path.join(root, '..', 'data', 'curriculum', f), 'utf8')).join('');
  assert.ok(Object.keys(registry).length >= 28);
  for (const [node, links] of Object.entries(registry)) {
    assert.ok(curriculum.includes('"id": "' + node + '"') || curriculum.includes('"id":"' + node + '"'), node);
    for (const {href, label} of links) {
      assert.match(href, /^\/app\/(math|physics|language|radiology)\/[a-z0-9-]+\/index\.html$/); assert.ok(label.length > 8);
      const dir = path.join(root, href.replace('/app/', '').replace('/index.html', ''));
      const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
      assert.ok(html.includes('href="/app/#/node/' + node + '"'), href); assert.ok(html.includes('role="status"'), href); assert.equal(html.includes('<canvas'), html.includes('role="img"'), href);
      assert.ok(fs.existsSync(path.join(dir, 'lab.js')), href);
      // Every control has a label.
      for (const id of [...html.matchAll(/<(?:input|select)[^>]* id="([a-z0-9-]+)"/g)].map(x => x[1])) assert.ok(html.includes('for="' + id + '"'), href + ' ' + id);
    }
  }
});

test('DIAPIX-FL preserves all case-sensitive source rows and transparent vowel medians', async () => {
  const model = await import('../web/language/vowel-formant-map/data.mjs');
  const folder = path.join(root, 'language/vowel-formant-map');
  const packed = fs.readFileSync(path.join(folder, 'vowels.txt.gz'));
  const raw = require('node:zlib').gunzipSync(packed);
  const metadata = JSON.parse(fs.readFileSync(path.join(folder, 'source.json')));
  const hash = require('node:crypto').createHash('sha256').update(raw).digest('hex');
  assert.equal(hash, '787f99e8d2aa6e0025ba2a864a1f797d1270a5dfafd3cfd06eb76740090a38b6');
  assert.equal(raw.length, 2582403);
  assert.equal(metadata.sourceSHA256, hash);
  assert.equal(metadata.sourceMD5, require('node:crypto').createHash('md5').update(raw).digest('hex'));
  const tokens = model.readTokens(raw.toString('utf8'));
  assert.equal(tokens.length, 55978);
  assert.equal(tokens[0].word, 'theres');
  assert.deepEqual([tokens[0].f1, tokens[0].f2, tokens[0].row], [439, 1970, 1]);
  assert.equal(new Set(tokens.map(model.speakerKey)).size, 20);
  const filters = {speaking:'',l1:'',vowel:'',speaker:'',word:''};
  assert.deepEqual(model.selectTokens(tokens, filters), tokens);
  assert.equal(model.selectTokens(tokens, {...filters,speaking:'Sp',vowel:'I'}).length, 4963);
  assert.equal(model.selectTokens(tokens, {...filters,speaking:'Sp',vowel:'i'}).length, 764);
  assert.equal(model.selectTokens(tokens, {...filters,speaking:'En',l1:'En'}).length, 8537);
  assert.equal(model.selectTokens(tokens, {...filters,speaking:'Sp',l1:'Sp'}).length, 21278);
  const groups = model.summaries(tokens, 'tokens');
  assert.equal(groups.length, 44);
  assert.equal(groups.reduce((n,row)=>n+row.tokens,0), tokens.length);
  assert.ok(groups.every(row=>row.speakers===10));
  const byId = new Map(groups.map(row=>[row.id,row]));
  assert.deepEqual([byId.get('En|En|ih').tokens,byId.get('En|En|ih').f1,byId.get('En|En|ih').f2], [1603,447,2002]);
  assert.deepEqual([byId.get('En|Sp|ih').tokens,byId.get('En|Sp|ih').f1,byId.get('En|Sp|ih').f2], [2154,368,2356]);
  const equalSpeakers = new Map(model.summaries(tokens, 'speakers').map(row=>[row.id,row]));
  assert.deepEqual([equalSpeakers.get('En|Sp|ih').f1,equalSpeakers.get('En|Sp|ih').f2], [368.25,2363.75]);
  assert.deepEqual([equalSpeakers.get('Sp|En|I').f1,equalSpeakers.get('Sp|En|I').f2], [396,2586.25]);
  assert.equal(model.comparison(byId.get('Sp|Sp|u'),byId.get('Sp|Sp|i'),'f1'),'tie');
  assert.equal(model.comparison(byId.get('En|En|ih'),byId.get('En|Sp|ih'),'f1'),'first');
  assert.equal(model.comparison(byId.get('En|En|ih'),byId.get('En|Sp|ih'),'f2'),'second');
  assert.equal(model.median([8,1,3,2]), 2.5);
  const box={left:0,right:300,top:0,bottom:210};
  assert.deepEqual(model.plotPosition(1000,2400,box),{x:100,y:100});
  assert.ok(model.plotPosition(500,3000,box).x<model.plotPosition(500,1000,box).x);
  assert.ok(model.plotPosition(1000,2000,box).y>model.plotPosition(500,2000,box).y);
});

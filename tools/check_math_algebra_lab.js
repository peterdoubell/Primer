#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/math-algebra-lab.js');
const ints = n => Array.from({ length: n }, (_, j) => j);
const near = (a, b) => assert.ok(Number.isFinite(a) && Math.abs(a - b) < 1e-10, a + ' != ' + b);
// This oracle treats a table as a labelled binary function, without calling
// the runtime axiom, decoding, inverse, or generation helpers.
function finiteOracle(table) {
  const names = ints(table.length), op = (a, b) => table[a][b];
  const closed = names.every(a => names.every(b => names.includes(op(a, b))));
  const associative = closed && names.every(a => names.every(b => names.every(c => op(op(a, b), c) === op(a, op(b, c)))));
  const identities = names.filter(e => names.every(a => op(e, a) === a && op(a, e) === a));
  const inverse = identities.length === 1 && names.every(a => names.some(b => op(a, b) === identities[0] && op(b, a) === identities[0]));
  return { closed, associative, identities, group: closed && associative && inverse };
}
let tables = 0, groups = 0;
for (let code = 0; code < 19683; code++) {
  let remainder = code; const digits = []; for (let i = 0; i < 9; i++) { digits.push(remainder % 3); remainder = Math.floor(remainder / 3); }
  const table = [digits.slice(0, 3), digits.slice(3, 6), digits.slice(6)];
  const expected = finiteOracle(table), actual = lab.groupAxioms(lab.decodeTable(code));
  assert.deepEqual(actual.table, table); assert.equal(actual.valid, expected.group);
  assert.equal(actual.associativity.length === 0, expected.associative); assert.deepEqual(actual.identities, expected.identities);
  for (const w of actual.associativity) { assert.equal(table[table[w.a][w.b]][w.c], w.left); assert.equal(table[w.a][table[w.b][w.c]], w.right); assert.notEqual(w.left, w.right); }
  if (actual.valid) groups++; tables++;
}
assert.equal(groups, 3, 'Exactly three labelled group tables exist on three elements.');
assert.equal(lab.groupAxioms([[0, 2], [1, 0]]).valid, false);
assert.equal(lab.groupAxioms([[0, 2], [1, 0]]).closure.length, 1);
assert.throws(() => lab.groupAxioms([[0, 1], [0]]), RangeError);
assert.throws(() => lab.decodeTable(19683), RangeError);
assert.equal(lab.axiomsModel({ axiomsSystem: 'positive' }).valid, false);
assert.equal(lab.axiomsModel({ axiomsSystem: 'integers' }).valid, true);
assert.equal(lab.axiomsModel({ axiomsSystem: 'rationals' }).valid, true);
function subgroupsExhaustive(table) {
  const n = table.length, output = [];
  for (let mask = 1; mask < 2 ** n; mask += 2) {
    const members = ints(n).filter(j => Math.floor(mask / 2 ** j) % 2);
    if (members.every(a => members.every(b => members.includes(table[a][b]))) && members.every(a => members.some(b => table[a][b] === 0 && table[b][a] === 0))) output.push(members);
  }
  return output.map(a => a.join(',')).sort();
}
let cyclic = 0;
for (let n = 2; n <= 20; n++) for (let a = 0; a < n; a++) {
  const d = lab.groupModel({ groupKind: 'cyclic', groupMod: n, generator: a });
  let value = 0, order = 0; do { value = (value + a) % n; order++; } while (value !== 0);
  assert.equal(d.order, order); assert.equal((a + d.inverse) % n, 0);
  assert.equal(new Set(d.cosets.flatMap(c => c.members)).size, n); assert.equal(d.cosets.length * d.order, n);
  for (const c of d.cosets) { assert.equal(c.members.length, order); assert.deepEqual(c.members, d.powers.map(h => (c.representative + h) % n).sort((x, y) => x - y)); }
  if (a === 0 && n <= 12) assert.deepEqual(d.subgroups.map(h => h.join(',')).sort(), subgroupsExhaustive(d.table));
  cyclic++;
}
const klein = lab.groupModel({ groupKind: 'klein', generator: 1 });
assert.deepEqual(klein.orders, [1, 2, 2, 2]); assert.deepEqual(klein.subgroups.map(h => h.join(',')).sort(), subgroupsExhaustive(klein.table));
assert.deepEqual(lab.groupModel({ groupKind: 'cyclic', groupMod: 4 }).orders, [1, 4, 2, 4]);
// Independent S4 oracle enumerates all 4^4 image tuples then retains bijections.
const permutations = [];
for (let code = 0; code < 256; code++) { const p = ints(4).map(j => Math.floor(code / 4 ** (3 - j)) % 4); if (new Set(p).size === 4) permutations.push(p); }
assert.deepEqual(lab.S4, permutations);
function orderOracle(p) { let images = ints(p.length), count = 0; do { images = images.map(i => p[i]); count++; } while (!images.every((x, i) => x === i)); return count; }
let compositions = 0, powers = 0;
for (let a = 0; a < 24; a++) for (let b = 0; b < 24; b++) {
  const d = lab.permutationModel({ permutation: a, secondPermutation: b });
  assert.deepEqual(d.sigmaTau, permutations[b].map(i => permutations[a][i]));
  assert.deepEqual(d.tauSigma, permutations[a].map(i => permutations[b][i]));
  assert.equal(d.order, orderOracle(permutations[a])); compositions++;
}
for (let a = 0; a < 24; a++) for (let r = 0; r <= 12; r++) {
  let expected = ints(4); for (let j = 0; j < r; j++) expected = expected.map(i => permutations[a][i]);
  assert.deepEqual(lab.permutationModel({ permutation: a, permutationPower: r }).selectedPower, expected); powers++;
}
const orderCounts = permutations.reduce((counts, p) => { const o = orderOracle(p); counts[o] = (counts[o] || 0) + 1; return counts; }, {});
assert.deepEqual(orderCounts, { 1: 1, 2: 9, 3: 8, 4: 6 }); assert.equal(lab.permutationModel({}).orderFour.length, 6);
let ringStates = 0;
for (let n = 2; n <= 19; n++) for (let c = 0; c < n; c++) {
  const d = lab.ringModel({ ringMod: n, coefficient: c });
  const units = ints(n).filter(a => ints(n).some(b => a * b % n === 1));
  const divisors = ints(n).filter(a => a && ints(n).some(b => b && a * b % n === 0));
  assert.deepEqual(d.units, units); assert.deepEqual(d.zeroDivisors, divisors);
  assert.deepEqual(d.solutions, ints(n).filter(x => c * x % n === 0));
  assert.equal(d.prime, !ints(n).some(divisor => divisor > 1 && divisor < n && n % divisor === 0));
  for (const a of ints(n)) for (const b of ints(n)) { assert.equal(d.addition[a][b], (a + b) % n); assert.equal(d.multiplication[a][b], a * b % n); }
  if (c === 0) {
    assert.equal(finiteOracle(d.addition).group, true);
    for (const x of ints(n)) for (const y of ints(n)) {
      assert.equal(d.addition[x][y], d.addition[y][x]);
      assert.equal(d.multiplication[x][1], x); assert.equal(d.multiplication[1][x], x);
      for (const z of ints(n)) {
        assert.equal(d.multiplication[d.multiplication[x][y]][z], d.multiplication[x][d.multiplication[y][z]]);
        assert.equal(d.multiplication[x][d.addition[y][z]], d.addition[d.multiplication[x][y]][d.multiplication[x][z]]);
        assert.equal(d.multiplication[d.addition[x][y]][z], d.addition[d.multiplication[x][z]][d.multiplication[y][z]]);
      }
    }
  }
  if (c === 0 && n <= 10) {
    const ideals = [];
    for (let mask = 1; mask < 2 ** n; mask += 2) { const I = ints(n).filter(j => Math.floor(mask / 2 ** j) % 2); if (I.every(a => I.every(b => I.includes(((a - b) % n + n) % n))) && I.every(a => ints(n).every(r => I.includes(a * r % n)))) ideals.push(I.join(',')); }
    assert.deepEqual(d.ideals.map(I => I.members.join(',')).sort(), ideals.sort());
  }
  ringStates++;
}
assert.deepEqual(lab.ringModel({ ringMod: 12, coefficient: 3 }).solutions, [0, 4, 8]);
assert.deepEqual(lab.ringModel({ ringMod: 12, coefficient: 3 }).image, [0, 3, 6, 9]);
assert.deepEqual(lab.ringModel({ ringMod: 6 }).zeroDivisors, [2, 3, 4]);
let integers = 0;
for (let k = -6; k <= 6; k++) for (let m = -18; m <= 18; m++) {
  const d = lab.integerModel({ multiplier: k, targetInteger: m });
  // All possible inverse candidates in this bounded target range lie here
  // when k!=0. This independently checks examples, not the infinite proof.
  const candidates = Array.from({ length: 73 }, (_, j) => j - 36).filter(x => k * x === m);
  assert.equal(d.hasPreimage, !!candidates.length); assert.equal(d.injective, k !== 0); assert.equal(d.onto, k === 1 || k === -1);
  if (k && candidates.length) assert.equal(d.inverseValue, candidates[0]);
  d.arrows.forEach(p => assert.equal(p.target, k * p.source));
  const graph = d.panels[0], targets = graph.nodes.filter(p => p.key.startsWith('b'));
  assert.equal(targets.length, new Set(d.domain.map(n => k * n)).size);
  for (const edge of graph.edges) { const a = graph.nodes.find(p => p.key === edge.from), b = graph.nodes.find(p => p.key === edge.to); assert.ok(Number(b.label) === Number(a.label) * k); }
  integers++;
}
const sylow = lab.sylowModel({});
assert.deepEqual(sylow.admissible5, sylow.candidate5.filter(n => n % 5 === 1)); assert.deepEqual(sylow.admissible3, sylow.candidate3.filter(n => n % 3 === 1));
assert.equal(new Set(sylow.pairs.map(p => p.a + ':' + p.b)).size, 15);
for (const p of sylow.pairs) { assert.equal((10 * p.a + 6 * p.b) % 15, p.n); for (const q of sylow.pairs) { const r = sylow.pairs[(p.n + q.n) % 15]; assert.equal(r.a, (p.a + q.a) % 3); assert.equal(r.b, (p.b + q.b) % 5); } }
let quotients = 0;
for (const ambient of ['S3', 'C12']) for (const choice of [0, 1, 2]) {
  const d = lab.quotientModel({ quotientGroup: ambient, subgroupChoice: choice });
  assert.ok(subgroupsExhaustive(d.table).includes([...d.subgroup].sort((a, b) => a - b).join(',')));
  const normal = ints(d.n).every(g => {
    const inv = ints(d.n).find(h => d.table[g][h] === 0 && d.table[h][g] === 0);
    return d.subgroup.every(h => d.subgroup.includes(d.table[d.table[g][h]][inv]));
  });
  assert.equal(d.normal, normal);
  if (normal) { assert.equal(finiteOracle(d.quotientTable).group, true); for (const a of ints(d.n)) for (const b of ints(d.n)) { const A = d.left.findIndex(c => c.members.includes(a)), B = d.left.findIndex(c => c.members.includes(b)), R = d.left.findIndex(c => c.members.includes(d.table[a][b])); assert.equal(d.quotientTable[A][B], R); } }
  else { assert.ok(d.failures.length); for (const w of d.failures) assert.ok(new Set(w.a.flatMap(a => w.b.map(b => d.left.findIndex(c => c.members.includes(d.table[a][b]))))).size > 1); }
  quotients++;
}
const matAdd = (a, b, p) => a.map((v, j) => (v + b[j]) % p);
const matMul = (a, b, p) => [(a[0] * b[0] + a[1] * b[2]) % p, (a[0] * b[1] + a[1] * b[3]) % p, (a[2] * b[0] + a[3] * b[2]) % p, (a[2] * b[1] + a[3] * b[3]) % p];
let fields = 0;
for (const p of [2, 3, 5, 7]) for (const fieldMap of ['scalar', 'zero', 'zeroRing']) for (const a of ints(p)) {
  const d = lab.fieldModel({ fieldPrime: String(p), fieldMap, idealGenerator: a });
  for (const x of ints(p)) for (const y of ints(p)) { assert.deepEqual(d.images[(x + y) % p], matAdd(d.images[x], d.images[y], p)); assert.deepEqual(d.images[x * y % p], matMul(d.images[x], d.images[y], p)); }
  assert.equal(d.unital, fieldMap !== 'zero'); assert.equal(d.targetNonzero, fieldMap !== 'zeroRing'); assert.equal(d.injective, fieldMap === 'scalar');
  assert.deepEqual(d.ideal, a ? ints(p) : [0]); if (a) assert.equal(d.inverse * a % p, 1); fields++;
}
for (const c of lab.controls) for (const bad of [undefined, null, '', ' ', true, false, [], {}, NaN, Infinity, 'bad']) assert.equal(lab.normalize({ [c.key]: bad })[c.key], lab.initial[c.key]);
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
  fire(name, extra = {}) { (this.events[name] || []).forEach(handler => handler({ target: this, ...extra })); }
  all() { return [this, ...this.children.filter(c => c.nodeType === 1).flatMap(c => c.all())]; }
}
globalThis.document = { createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag), createTextNode: value => new Text(value) };
assert.equal(lab.render({ props: { scenario: 'math.5.abstract' } }), null); assert.equal(lab.render({ props: { scenario: lab.SCENARIO, extra: true } }), null);
let speech;
const root = lab.render({ renderer: 'math-algebra-lab', props: { scenario: lab.SCENARIO } }, { speakButton: provider => { speech = provider; return new Element('button'); } });
const all = () => root.all(), input = key => all().find(e => e.attributes['data-algebra-control'] === key), action = key => all().find(e => e.attributes['data-algebra-action'] === key), state = () => JSON.parse(root.attributes['data-algebra-state']);
let mountedStates = 0, svgCells = 0;
function mounted() {
  const elements = all(), d = lab.build(state()); assert.equal(elements.filter(e => e.tagName === 'svg').length, 2); assert.match(speech(), /Finite pictures do not prove infinite/); assert.ok(speech().includes(d.station));
  for (const c of lab.controls) { const widget = input(c.key), label = elements.find(e => e.tagName === 'label' && e.attributes.for === widget.attributes.id), hidden = Boolean(c.stations && !c.stations.includes(d.station)); assert.equal(Boolean(label.hidden), hidden); assert.equal(Boolean(widget.disabled), hidden); }
  const svgs = elements.filter(e => e.tagName === 'svg');
  d.panels.forEach((p, j) => {
    const parts = svgs[j].all();
    if (p.kind === 'table') { const entries = parts.filter(e => e.attributes['data-algebra-entry']); assert.equal(entries.length, p.table.length ** 2); for (const e of entries) { const [a, b] = e.attributes['data-algebra-entry'].split(':').map(Number); assert.equal(e.textContent, p.names[p.table[a][b]]); near(Number(e.attributes.x), 95 + 290 / p.table.length * (b + .5)); near(Number(e.attributes.y), 64 + 290 / p.table.length * (a + .65)); } svgCells += entries.length; }
    if (p.kind === 'graph') { const nodes = parts.filter(e => e.attributes['data-algebra-node'] != null), edges = parts.filter(e => e.attributes['data-algebra-edge'] != null); assert.equal(nodes.length, p.nodes.length); assert.equal(edges.length, p.edges.length); p.edges.forEach((edge, k) => { assert.equal(edges[k].attributes['data-algebra-from'], edge.from); assert.equal(edges[k].attributes['data-algebra-to'], edge.to); }); }
    if (p.kind === 'points') { const points = parts.filter(e => e.attributes['data-algebra-point'] != null); assert.equal(points.length, p.points.length); assert.equal(parts.filter(e => e.tagName === 'polyline').length, 0); points.forEach((e, i) => { near(Number(e.attributes.cx), 55 + 370 * (p.points[i].x - p.xRange[0]) / (p.xRange[1] - p.xRange[0])); near(Number(e.attributes.cy), 330 - 260 * (p.points[i].y - p.yRange[0]) / (p.yRange[1] - p.yRange[0])); }); }
  });
  for (const e of elements) for (const [key, value] of Object.entries(e.attributes)) { assert.doesNotMatch(value, /NaN|Infinity/); if (['x', 'cx', 'x1', 'x2'].includes(key)) assert.ok(Number(value) >= 0 && Number(value) <= 480); if (['y', 'cy', 'y1', 'y2'].includes(key)) assert.ok(Number(value) >= 0 && Number(value) <= 390); }
  mountedStates++;
}
for (const c of lab.controls) {
  input('station').value = c.stations ? c.stations[0] : 'A1'; input('station').fire('change');
  for (const value of c.options ? c.options.map(o => o.value) : [c.min, c.max]) { input(c.key).value = String(value); input(c.key).fire('change'); mounted(); }
  if (!c.options) { const slider = all().find(e => e.attributes['data-algebra-range'] === c.key); slider.value = String(c.min); slider.fire('input'); assert.equal(state()[c.key], c.min); mounted(); }
  action('reset').fire('click'); assert.deepEqual(state(), lab.initial);
}
for (const [key] of lab.fixtures) { action(key).fire('click'); mounted(); }
action('reset').fire('click'); const draft = input('tableCode'); draft.value = '100.4'; draft.fire('input'); assert.equal(state().tableCode, 8229); assert.equal(draft.value, '100.4'); draft.fire('blur'); assert.equal(state().tableCode, 100); draft.value = ''; draft.fire('blur'); assert.equal(state().tableCode, 8229); draft.value = '19682'; draft.fire('keydown', { key: 'Enter' }); assert.equal(state().tableCode, 19682); draft.value = '1'; draft.fire('keydown', { key: 'Escape' }); assert.equal(draft.value, '19682'); assert.equal(state().tableCode, 19682);
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true'); action('reset').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'false'); assert.deepEqual(state(), lab.initial);
const joined = [], published = [];
globalThis.window = { PrimerLessonStateBus: { join: (key, view, receive) => joined.push({ key, view, receive }), publish: (key, source, values) => { published.push({ key, source, values }); for (const target of joined) if (target.key === key && target.view !== source) target.receive(values); } } };
const first = lab.render({ props: { scenario: lab.SCENARIO } }), second = lab.render({ props: { scenario: lab.SCENARIO } }); assert.equal(published.length, 0);
first.setModelState({ station: 'A4', ringMod: 19, coefficient: 0, permutation: 23, multiplier: -6 }); assert.equal(published.length, 1); assert.equal(published[0].key, 'math.5.abstract'); assert.deepEqual(JSON.parse(first.attributes['data-algebra-state']), JSON.parse(second.attributes['data-algebra-state'])); assert.equal(Object.keys(published[0].values).length, Object.keys(lab.initial).length);
second.setModelState({ station: 'A8', fieldPrime: '7' }, false, true); assert.equal(published.length, 1);
first.all().find(e => e.attributes['data-algebra-action'] === 'reset').fire('click'); assert.equal(published.length, 2); assert.deepEqual(JSON.parse(second.attributes['data-algebra-state']), lab.initial);
delete globalThis.window;
console.log('Verified ' + tables + ' exhaustive three-element operation tables (' + groups + ' groups), ' + cyclic + ' cyclic element/subgroup/coset states, Klein subgroup enumeration, ' + compositions + ' independent S4 compositions, ' + powers + ' powers, six four-cycles, ' + ringStates + ' modular ring/kernel states, ' + integers + ' integer-map examples with separate universal proofs, all 225 CRT products, ' + quotients + ' normal/nonnormal quotient states, ' + fields + ' matrix field-map/ideal states, ' + mountedStates + ' mounted states and ' + svgCells + ' exact rendered table cells. Draft/blur/Enter/Escape, sliders, all fixtures, live speech, exact resets and complete-state bus propagation passed.');

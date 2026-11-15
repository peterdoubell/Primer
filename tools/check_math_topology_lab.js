#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/math-topology-lab.js');
const TAU = 2 * Math.PI;
const near = (a, b, tol = 1e-10) => assert.ok(Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= tol * Math.max(1, Math.abs(b)), `${a} != ${b}`);
const pop = n => n.toString(2).split('').filter(c => c === '1').length;
// A separate set implementation, using actual point arrays and membership,
// supplies the oracle; runtime bitwise union/intersection is not reused.
const subsets = Array.from({ length: 8 }, (_, mask) => [0, 1, 2].filter(j => Math.floor(mask / 2 ** j) % 2));
const same = (a, b) => a.length === b.length && a.every(v => b.includes(v));
const union = lists => [0, 1, 2].filter(p => lists.some(s => s.includes(p)));
const intersect = (a, b) => a.filter(v => b.includes(v));
let familyStates = 0, topologyCount = 0, continuousStates = 0, covers = 0, cofinite = 0, sine = 0, meshes = 0, inverses = 0, circles = 0;
for (let code = 0; code <= 255; code++) {
  const actual = lab.finiteAxioms(code), selected = subsets.filter((_, j) => Math.floor(code / 2 ** j) % 2);
  const contains = set => selected.some(t => same(t, set));
  let unionsPass = true, intersectionsPass = true;
  for (let sub = 0; sub < 2 ** selected.length; sub++) { const u = union(selected.filter((_, j) => Math.floor(sub / 2 ** j) % 2)); if (!contains(u)) unionsPass = false; }
  for (const a of selected) for (const b of selected) if (!contains(intersect(a, b))) intersectionsPass = false;
  const valid = contains([]) && contains([0, 1, 2]) && unionsPass && intersectionsPass;
  assert.equal(actual.valid, valid); assert.equal(actual.unions.length === 0, unionsPass); assert.equal(actual.intersections.length === 0, intersectionsPass);
  assert.equal(actual.subfamilyCount, 2 ** pop(code));
  for (const witness of actual.unions) { assert.equal(contains(subsets[witness.result]), false); assert.deepEqual(union(witness.members.map(i => subsets[i])), subsets[witness.result]); }
  if (valid) topologyCount++; familyStates++;
}
assert.equal(topologyCount, 29, 'The known count of labelled topologies on three points is 29.');
const invalid = lab.finiteModel({ familyMask: 135 }); assert.deepEqual(invalid.opens, [0, 1, 2, 7]); assert.deepEqual(invalid.unions[0], { members: [1, 2], result: 3 }); assert.equal(invalid.intersections.length, 0);
assert.equal(lab.finiteModel({ familyMask: 139 }).valid, true); assert.equal(lab.finiteModel({ familyMask: 139 }).opens.includes(6), false, 'Complement of {a} need not be open.');
for (const domainName of Object.keys(lab.topologyCodes)) for (const targetName of Object.keys(lab.topologyCodes)) for (let code = 0; code < 27; code++) {
  const d = lab.continuityModel({ domainTopology: domainName, targetTopology: targetName, mapCode: code });
  const mapping = Array.from({ length: 3 }, (_, j) => Math.floor(code / 3 ** j) % 3), domain = d.domain.map(mask => subsets[mask]), target = d.target.map(mask => subsets[mask]);
  const preimages = target.map(v => [0, 1, 2].filter(x => v.includes(mapping[x])));
  const continuous = preimages.every(p => domain.some(u => same(u, p))), bijective = new Set(mapping).size === 3;
  const inverseContinuous = bijective ? domain.every(u => target.some(v => same(v, u.map(x => mapping[x]).sort()))) : null;
  assert.deepEqual(d.mapping, mapping); assert.equal(d.continuous, continuous); assert.equal(d.bijective, bijective); assert.equal(d.inverseContinuous, inverseContinuous); assert.equal(d.homeomorphism, continuous && bijective && inverseContinuous);
  d.preimages.forEach((p, j) => assert.deepEqual(subsets[p.preimage], preimages[j]));
  if (continuous && bijective && d.targetHausdorff) assert.equal(d.inverseContinuous, true, 'Finite compact–Hausdorff theorem.'); continuousStates++;
}
assert.equal(lab.continuityModel({ domainTopology: 'discrete', targetTopology: 'indiscrete', mapCode: 21 }).inverseContinuous, false);
for (let N = 2; N <= 80; N++) for (const m of [2, 6, 16]) {
  const d = lab.coverModel({ coverN: N, coverMesh: m }); near(d.witness, .5 / N); assert.ok(d.witness > 0 && d.witness < 1 / N);
  for (const p of d.selected) assert.equal(d.witness > p.start && d.witness < p.end, false);
  assert.equal(d.finiteUnion.start, Math.min(...d.selected.map(p => p.start))); assert.equal(d.finiteUnion.startIncluded, false);
  for (let j = 0; j <= 512; j++) { const x = j / 512; assert.ok(d.closedCover.some(p => x > p.start && x < p.end)); }
  for (const x of [1e-7, .001, .123, .5, .999999]) { const n = Math.floor(1 / x) + 1; assert.ok(x > 1 / n && x < 1, 'Archimedean choice covers any test point; proof handles all x.'); }
  assert.equal(d.openIntervalCompact, false); assert.equal(d.closedIntervalCompact, true); covers++;
}
for (let a = 1; a <= 12; a++) for (let b = 1; b <= 12; b++) {
  const d = lab.cofiniteModel({ cofiniteA: a, cofiniteB: b });
  assert.equal(d.universe, 'infinite real line'); assert.ok(!d.excludedA.includes(d.witness) && !d.excludedB.includes(d.witness));
  assert.deepEqual(d.excludedUnion, [...new Set([...d.excludedA, ...d.excludedB])].sort((x, y) => x - y)); assert.equal(d.t1, true); assert.equal(d.hausdorff, false); assert.equal(d.compact, true); cofinite++;
}
for (const cycles of [2, 8, 24]) for (const y of [-1, -.5, 0, .5, 1]) for (const n of [1, 4, 20]) {
  const d = lab.sineModel({ sineCycles: cycles, sineTarget: y, sequenceN: n });
  d.graph.forEach(([x, value], j) => { const u = 1 + TAU * cycles * j / (48 * cycles); near(x, 1 / u); near(value, Math.sin(1 / x), 1e-11); assert.ok(x >= d.xMin && x > 0); });
  near(d.xMin, 1 / (1 + TAU * cycles)); assert.deepEqual(d.vertical, [[0, -1], [0, 1]]);
  d.sequence.forEach((p, j) => { near(Math.sin(1 / p.x), y, 1e-11); assert.equal(p.n, j + 1); if (j) assert.ok(p.x < d.sequence[j - 1].x); });
  assert.deepEqual(d.target, [0, y]); assert.equal(d.selected.n, n); assert.equal(d.connected, true); assert.equal(d.pathConnected, false); assert.equal(d.compact, true); sine++;
}
// An independent incidence builder verifies the actual indexed mesh, including
// every vertex link (a single cycle), not just an advertised V−E+F formula.
function verifyMesh(m, g) {
  const adjacency = m.vertices.map(() => new Set()), links = m.vertices.map(() => new Map()), edges = new Map();
  const faceKeys = new Set();
  for (const f of m.faces) {
    assert.equal(new Set(f).size, 3); assert.ok(f.every(i => Number.isInteger(i) && i >= 0 && i < m.vertices.length));
    const key = [...f].sort((a, b) => a - b).join(':'); assert.equal(faceKeys.has(key), false); faceKeys.add(key);
    const [a, b, c] = f.map(i => m.vertices[i]), ab = b.map((v, j) => v - a[j]), ac = c.map((v, j) => v - a[j]), cross = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]]; assert.ok(Math.hypot(...cross) > 1e-8, 'No zero-area triangle.');
    f.forEach((v, j) => { const u = f[(j + 1) % 3], w = f[(j + 2) % 3]; adjacency[v].add(u); adjacency[u].add(v);
      if (!links[v].has(u)) links[v].set(u, new Set()); if (!links[v].has(w)) links[v].set(w, new Set()); links[v].get(u).add(w); links[v].get(w).add(u);
      const edgeKey = [v, u].sort((a, b) => a - b).join(':'); if (!edges.has(edgeKey)) edges.set(edgeKey, []); edges.get(edgeKey).push(v < u ? 1 : -1);
    });
  }
  for (const signs of edges.values()) { assert.equal(signs.length, 2); assert.equal(signs[0] + signs[1], 0); }
  const connected = graph => { const visited = new Set(), stack = [graph.keys().next().value]; while (stack.length) { const v = stack.pop(); if (visited.has(v)) continue; visited.add(v); for (const u of graph.get(v)) stack.push(u); } return visited.size === graph.size; };
  assert.ok(connected(new Map(adjacency.map((neighbors, v) => [v, neighbors]))));
  for (const link of links) { assert.ok(link.size >= 3); for (const neighbors of link.values()) assert.equal(neighbors.size, 2); assert.ok(connected(link), 'Vertex link must be one circle, not disconnected cycles.'); }
  assert.equal(m.vertices.length - edges.size + m.faces.length, 2 - 2 * g); assert.deepEqual(m.counts, { V: m.vertices.length, E: edges.size, F: m.faces.length, chi: 2 - 2 * g });
  assert.ok(m.vertices.every(p => p.every(Number.isFinite))); return edges.size;
}
for (let g = 0; g <= 3; g++) for (const r of [1, 2]) {
  const m = lab.surfaceMesh(g, r); verifyMesh(m, g); const expectedCells = ((g ? 4 * g + 2 : 6) * 6 - 4 * g) * r ** 2; assert.equal(m.faces.length, expectedCells * 8);
  for (const stretch of [.5, 1, 2]) for (const bend of [-.75, 0, .75]) {
    const d = lab.surfaceModel({ genus: g, refinement: r, stretch, bend }); assert.equal(d.closed, true); assert.equal(d.oriented, true); near(d.jacobianDeterminant, stretch);
    d.vertices.forEach((p, j) => { near(p[0], stretch * m.vertices[j][0] + bend * m.vertices[j][1]); near(p[1], m.vertices[j][1]); near(p[2], m.vertices[j][2]); const back = lab.undeform(p, stretch, bend); back.forEach((v, k) => near(v, m.vertices[j][k])); });
    assert.equal(d.quotient.chi, 2 - 2 * g); assert.deepEqual(d.figureEight[0], [0, 0, 0]); assert.deepEqual(d.figureEight[64], [0, 0, 0]); assert.deepEqual(d.figureEight[128], [0, 0, 0]);
    // Affine transformation preserves barycentric points EXACTLY; the flat
    // displayed facets are the actual images, rather than curved-F chords.
    for (const f of m.faces.slice(0, 12)) { const p = [0, 1, 2].map(k => f.reduce((sum, v) => sum + m.vertices[v][k] / 3, 0)), image = lab.deform(p, stretch, bend); image.forEach((v, k) => near(v, f.reduce((sum, i) => sum + d.vertices[i][k] / 3, 0))); }
    inverses++;
  }
  meshes++;
}
for (const domain of ['halfopen', 'closed', 'quotient']) for (const logEpsilon of [-5, -3, -.5]) for (const angleFraction of [0, .25, .875]) {
  const d = lab.circleModel({ circleDomain: domain, logEpsilon, angleFraction }); const e = 10 ** logEpsilon;
  near(d.upper[0], Math.cos(e)); near(d.upper[1], Math.sin(e)); near(d.lower[0], Math.cos(e)); near(d.lower[1], -Math.sin(e)); near(d.imageDistance, Math.hypot(d.lower[0] - 1, d.lower[1])); near(d.inverseDistance, TAU - e);
  d.jumpSequence.forEach(p => { near(Math.cos(p.preimage), p.point[0]); near(Math.sin(p.preimage), p.point[1]); assert.ok(p.preimage > 5); });
  assert.equal(d.bijective, domain !== 'closed'); assert.equal(d.domainCompact, domain !== 'halfopen'); assert.equal(d.homeomorphism, domain === 'quotient'); assert.equal(d.inverseContinuous, domain === 'closed' ? null : domain === 'quotient');
  assert.deepEqual(d.preimages.seam, domain === 'closed' ? [0, TAU] : [0]); circles++;
}
for (const c of lab.controls) for (const bad of [undefined, null, '', ' ', true, false, [], {}, NaN, Infinity, -Infinity, 'bad']) assert.equal(lab.normalize({ [c.key]: bad })[c.key], lab.initial[c.key]);
assert.throws(() => lab.finiteAxioms(256), RangeError); assert.throws(() => lab.decodeMap(27), RangeError); assert.throws(() => lab.surfaceMesh(4), RangeError);
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
assert.equal(lab.render({ props: { scenario: 'math.5.topology' } }), null); assert.equal(lab.render({ props: { scenario: lab.SCENARIO, arbitrary: true } }), null); assert.equal(lab.render({ renderer: 'other', props: { scenario: lab.SCENARIO } }), null);
let speech;
const root = lab.render({ renderer: 'math-topology-lab', props: { scenario: lab.SCENARIO } }, { speakButton: provider => { speech = provider; return new Element('button'); } });
const all = () => root.all(), inputFor = key => all().find(e => e.attributes['data-topology-control'] === key), action = key => all().find(e => e.attributes['data-topology-action'] === key), state = () => JSON.parse(root.attributes['data-topology-state']);
function mounted() {
  const elements = all(), s = state(); assert.equal(elements.filter(e => e.tagName === 'svg').length, 2); assert.equal(elements.filter(e => e.tagName === 'table').length, 1);
  assert.ok(speech().includes(s.station)); assert.match(speech(), /Finite pictures do not prove infinite/);
  for (const e of elements) for (const [key, attr] of Object.entries(e.attributes)) {
    assert.doesNotMatch(attr, /NaN|Infinity/);
    if (key === 'points') for (const p of attr.split(' ').map(p => p.split(',').map(Number))) { assert.equal(p.length, 2); assert.ok(p[0] >= -1 && p[0] <= 481 && p[1] >= -1 && p[1] <= 341, 'SVG coordinate outside view box: ' + attr); }
    if (['cx', 'x'].includes(key)) assert.ok(Number(attr) >= -1 && Number(attr) <= 481);
    if (['cy', 'y'].includes(key)) assert.ok(Number(attr) >= -1 && Number(attr) <= 341);
  }
  for (const c of lab.controls) { const input = inputFor(c.key), label = elements.find(e => e.tagName === 'label' && e.attributes.for === input.attributes.id), hidden = Boolean(c.stations && !c.stations.includes(s.station)); assert.equal(Boolean(label.hidden), hidden); assert.equal(Boolean(input.disabled), hidden); }
  const d = lab.build(s).active;
  if (s.station === 'T5') {
    const graph = elements.find(e => e.attributes['data-topology-sine'] === 'graph'), vertical = elements.find(e => e.attributes['data-topology-sine'] === 'vertical');
    const gp = graph.attributes.points.split(' ').map(p => p.split(',').map(Number)); gp.forEach((p, j) => { near(p[0], 80 + 330 * d.graph[j][0]); near(p[1], 188 - 95 * d.graph[j][1]); assert.ok(p[0] > 80, 'Graph never reaches or bridges x=0.'); });
    assert.equal(vertical.attributes.points, '80,283 80,93');
  }
  if (s.station === 'T6') { assert.equal(elements.filter(e => e.attributes['data-topology-face']).length, d.faces.length); assert.equal(elements.filter(e => e.attributes['data-topology-crossing']).length, 1); }
  if (s.station === 'T7') { const lower = elements.find(e => e.attributes['data-topology-circle'] === 'lower'); near(Number(lower.attributes.cx), 240 + 100 * d.lower[0]); near(Number(lower.attributes.cy), 185 - 100 * d.lower[1]); }
}
let mountedControls = 0;
for (const c of lab.controls) {
  inputFor('station').value = c.stations ? c.stations[0] : 'T1'; inputFor('station').fire('change');
  for (const value of c.options ? c.options.map(o => o.value) : [c.min, c.max]) { inputFor(c.key).value = String(value); inputFor(c.key).fire('change'); mounted(); mountedControls++; }
  action('reset').fire('click'); assert.deepEqual(state(), lab.initial);
}
for (const key of ['missingunion', 'validchain', 'identityfail', 'homeomorphism', 'cover', 'cofinite', 'sine', 'genusthree', 'halfopen', 'surjection', 'quotient']) { action(key).fire('click'); mounted(); }
action('missingunion').fire('click'); assert.match(root.textContent, /\{a\} ∪ \{b\} = \{a,b\} is missing/);
action('identityfail').fire('click'); assert.match(root.textContent, /Inverse continuousno/);
action('genusthree').fire('click'); assert.match(root.textContent, /χ=−?\-?4|χ=-4/); assert.match(speech(), /Different CW cell decomposition/);
action('halfopen').fire('click'); assert.equal(all().filter(e => e.attributes['data-topology-proof-step']).length, 4); assert.match(speech(), /does not tend to the inverse 0/);
action('reset').fire('click'); const draft = inputFor('familyMask'); draft.value = '139.4'; draft.fire('input'); assert.equal(draft.value, '139.4'); assert.equal(state().familyMask, 135); draft.fire('blur'); assert.equal(state().familyMask, 139); assert.equal(draft.value, '139');
draft.value = ''; draft.fire('blur'); assert.equal(state().familyMask, 135); draft.value = '1e100'; draft.fire('change'); assert.equal(state().familyMask, 255);
draft.value = '129'; draft.fire('keydown', { key: 'Enter' }); assert.equal(state().familyMask, 129); draft.value = '143'; draft.fire('keydown', { key: 'Escape' }); assert.equal(draft.value, '129'); assert.equal(state().familyMask, 129);
action('enlarge').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'true'); action('reset').fire('click'); assert.equal(action('enlarge').attributes['aria-pressed'], 'false'); assert.deepEqual(state(), lab.initial); mounted();
const another = lab.render({ props: { scenario: lab.SCENARIO } }); assert.notEqual(root.attributes['aria-labelledby'], another.attributes['aria-labelledby']);
// Bus stub exercises complete-state propagation independently of the parent
// registry integration; join never publishes, peer receipt never echoes.
const joined = [], published = [];
globalThis.window = { PrimerLessonStateBus: { join: (key, view, receive) => joined.push({ key, view, receive }), publish: (key, source, values) => { published.push({ key, source, values }); for (const target of joined) if (target.key === key && target.view !== source) target.receive(values); } } };
const first = lab.render({ props: { scenario: lab.SCENARIO } }), second = lab.render({ props: { scenario: lab.SCENARIO } }); assert.equal(published.length, 0);
first.setModelState({ station: 'T6', genus: 3, refinement: 2, stretch: .5, bend: .75 }); assert.equal(published.length, 1); assert.deepEqual(JSON.parse(first.attributes['data-topology-state']), JSON.parse(second.attributes['data-topology-state'])); assert.equal(published[0].key, 'math.5.topology');
second.setModelState({ stretch: 2 }, false, true); assert.equal(published.length, 1);
first.all().find(e => e.attributes['data-topology-action'] === 'reset').fire('click'); assert.equal(published.length, 2); assert.deepEqual(JSON.parse(second.attributes['data-topology-state']), lab.initial);
delete globalThis.window;
console.log(`Verified ${familyStates} exhaustive open-family states (29 topologies), ${continuousStates} independent preimage maps, ${covers} cover/witness states, ${cofinite} infinite cofinite illustrations, ${sine} sine-closure states, ${meshes} closed oriented manifold meshes with every vertex link and Euler characteristic, ${inverses} exact affine deformation/inverse states, ${circles} circle/theorem states, ${mountedControls} mounted controls across all seven stations. Draft/blur/Enter/Escape, every fixture, live speech, no oscillation bridge, exact resets and complete-state bus propagation passed.`);

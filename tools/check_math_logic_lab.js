#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict'), lab = require('../web/math-logic-lab.js');
let functions = 0, relations = 0, decimals = 0, mounted = 0;
for (let n = 1; n <= 4; n++) {
  const subsets = 2 ** n;
  for (let code = 0; code < subsets ** n; code++) {
    const rows = Array.from({length: n}, (_, i) => Math.floor(code / subsets ** i) % subsets), actual = lab.diagonal(rows, n);
    const D = new Set(Array.from({length: n}, (_, i) => i).filter(i => !(rows[i] & 2 ** i)));
    assert.equal(actual.missing, [...D].reduce((sum, i) => sum + 2 ** i, 0));
    for (const c of actual.comparisons) { assert.notEqual(c.listedContains, c.diagonalContains); assert.equal(c.equal, false); }
    functions++;
  }
}
for (let n = 1; n <= 4; n++) for (let mask = 0; mask < 2 ** (n * n); mask++) {
  const a = lab.relation(n, mask), pairs = new Set(a.pairs.map(([x, y]) => x + ',' + y));
  const has = (x, y) => pairs.has(x + ',' + y), names = Array.from({length: n}, (_, i) => i);
  const oracle = {
    reflexive: names.every(x => has(x, x)),
    symmetric: names.every(x => names.every(y => !has(x, y) || has(y, x))),
    antisymmetric: names.every(x => names.every(y => x === y || !has(x, y) || !has(y, x))),
    transitive: names.every(x => names.every(y => names.every(z => !has(x, y) || !has(y, z) || has(x, z))))
  };
  assert.deepEqual(a.properties, oracle); assert.equal(a.relationCount, 2 ** (n * n));
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) assert.equal(a.table[i][j], has(i, j));
  for (const [kind, failures] of Object.entries(a.failures)) assert.equal(failures.length === 0, oracle[kind]);
  relations++;
}
for (let diagonal = 0; diagonal < 10; diagonal++) for (let index = 0; index < 8; index++) {
  const rows = Array(8).fill(String(diagonal).repeat(8)), a = lab.decimalDiagonal(rows);
  assert.ok(a.digits.every(d => d === '1' || d === '2')); assert.notEqual(a.digits[index], rows[index][index]); decimals++;
}
for (let bound = 0; bound <= 20; bound++) for (let witness = 0; witness <= 22; witness++) {
  const m = lab.build({station: 'compactness', bound, witness}); assert.equal(m.data.allSatisfied, witness > bound);
  assert.equal(m.data.constraints.length, bound + 1); assert.equal(m.data.canonicalWitness, bound + 1);
}
for (const theory of ['pa', 'infinite', 'true', 'weak', 'inconsistent']) {
  const m = lab.build({station: 'incomplete', theory, extension: 4}); assert.equal(m.data.applies, ['pa', 'infinite'].includes(theory));
  assert.equal(m.panels[1].nodes.length, m.data.applies ? 5 : 2);
}
assert.equal(lab.build({station: 'independence', statement: 'unknown'}).data.status, 'Unknown from the stated proof dependency');
assert.equal(lab.build({station: 'skolem', viewpoint: 'outside'}).data.externalBijectionRepresentedInM, false);
for (let depth = 1; depth <= 5; depth++) { const a = lab.build({station: 'consistency', ordinalDepth: depth}); assert.equal(a.data.ordinals.length, depth); assert.ok(a.data.ordinals.every(o => o !== 'ε₀')); }
class E {
  constructor(tag) { this.tagName = tag; this.nodeType = 1; this.attributes = {}; this.children = []; this.listeners = {}; this.value = ''; this.hidden = false; this.disabled = false; this.classList = {toggle: (name, on) => {const set = new Set((this.attributes.class || '').split(' ')); on ? set.add(name) : set.delete(name); this.attributes.class = [...set].join(' ');}}; }
  setAttribute(k, v) { this.attributes[k] = String(v); } getAttribute(k) { return this.attributes[k]; } removeAttribute(k) { delete this.attributes[k]; }
  append(...x) { this.children.push(...x); } replaceChildren(...x) { this.children = x; } addEventListener(k, f) { this.listeners[k] = f; } focus() { this.focused = true; }
  get textContent() { return this.children.map(x => x.textContent).join(''); } set textContent(v) { this.children = [{nodeType: 3, textContent: String(v)}]; }
  querySelector(selector) { const match = /^\[([^=]+)="([^"]+)"\]$/.exec(selector); return match ? all(this).find(e => e.attributes?.[match[1]] === match[2]) : undefined; }
}
const all = e => [e, ...(e.children || []).flatMap(c => c.nodeType === 1 ? all(c) : [])];
global.document = {createElement: t => new E(t), createElementNS: (_ns, t) => new E(t), createTextNode: t => ({nodeType: 3, textContent: String(t)})};
let spoken; const root = lab.render({props: {scenario: lab.scenario}}, {speakButton: f => { spoken = f; return new E('button'); }});
const find = (key, value) => all(root).find(e => e.attributes?.[key] === value);
function check() {
  const m = lab.build(JSON.parse(root.getAttribute('data-logic-state'))); assert.ok(root.textContent.includes(m.readout)); assert.ok(spoken().includes(m.boundary));
  for (const c of lab.controls) assert.equal(find('data-logic-control', c.key).disabled, Boolean(c.stations && !c.stations.includes(m.station)));
  for (let p = 0; p < m.panels.length; p++) if (m.panels[p].kind === 'table') {
    const t = find('data-logic-table', String(p)); assert.ok(t); assert.equal(all(t).filter(e => e.tagName === 'td').length, m.panels[p].cells.reduce((sum, r) => sum + r.length, 0));
  }
  if (m.station === 'relations') assert.equal(all(root).filter(e => e.attributes?.['data-logic-edge'] !== undefined).length, m.data.pairs.length);
  mounted++;
}
for (const [station] of lab.stations) {
  const stationInput = find('data-logic-control', 'station'); stationInput.value = station; stationInput.listeners.change(); check();
  for (const c of lab.controls.filter(c => c.key !== 'station' && (!c.stations || c.stations.includes(station)))) {
    for (const value of c.options ? c.options.map(o => o.value) : [c.min, c.max]) {
      const input = find('data-logic-control', c.key); input.value = String(value); input.listeners.change(); check();
    }
  }
}
find('data-logic-control', 'station').value = 'powerset'; find('data-logic-control', 'station').listeners.change();
const before = JSON.parse(root.getAttribute('data-logic-state')); find('data-logic-toggle', 'powerset:0:0').listeners.click();
assert.equal(JSON.parse(root.getAttribute('data-logic-state')).rows[0], before.rows[0] ^ 1); check();
const numeric = find('data-logic-control', 'size'), accepted = root.getAttribute('data-logic-state'); numeric.value = ''; numeric.listeners.change(); assert.equal(root.getAttribute('data-logic-state'), accepted); assert.equal(numeric.getAttribute('aria-invalid'), 'true');
find('data-logic-control', 'station').value = 'decimal'; find('data-logic-control', 'station').listeners.change();
const box = find('data-logic-decimals', ''); box.value = Array(8).fill('11111111').join('\n'); find('data-logic-action', 'decimals').listeners.click(); assert.equal(lab.build(JSON.parse(root.getAttribute('data-logic-state'))).data.prefix, '0.22222222'); check();
const retained = root.getAttribute('data-logic-state'); box.value = 'invalid'; find('data-logic-action', 'decimals').listeners.click(); assert.equal(root.getAttribute('data-logic-state'), retained);
find('data-logic-action', 'enlarge').listeners.click(); assert.equal(find('data-logic-action', 'enlarge').getAttribute('aria-pressed'), 'true');
find('data-logic-action', 'reset').listeners.click(); assert.deepEqual(JSON.parse(root.getAttribute('data-logic-state')), lab.initial); check();
assert.equal(lab.render({props: {scenario: 'other'}}), null);
console.log(`Verified ${functions} complete finite diagonal maps, ${relations} complete relation encodings, ${decimals} decimal cases and ${mounted} mounted logic states.`);

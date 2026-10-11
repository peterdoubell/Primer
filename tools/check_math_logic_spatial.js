#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
global.window = {};
window.PrimerMathLogicLab = require('../web/math-logic-lab.js');
require('../web/lesson-state.js'); require('../web/spatial-models.js'); require('../web/spatial-logic.js'); require('../web/spatial-module-objects.js');
const lab = window.PrimerMathLogicLab, spatial = window.PrimerSpatial;
const item = {props: {scenario: 'module.math.5.logic', family: 'logic-witness-geometry', mode: 'model', context: 'Exact logical witnesses.', lesson: 'Logic and Set Theory'}};
assert.ok(window.PrimerModuleObjects.ensure(item)); let states = 0, cells = 0, edges = 0;
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-12, a + ' != ' + b);
function check(raw) {
  const expected = lab.build(raw), actual = spatial.build(item.props.scenario, raw);
  assert.deepEqual(actual.logic.state, expected.state); assert.deepEqual(actual.logic.data, expected.data); assert.deepEqual(actual.logic.proof, expected.proof);
  assert.equal(actual.logic.panels.length, expected.panels.length);
  for (const p of actual.logic.panels) {
    const source = expected.panels[p.index]; assert.deepEqual(p.source, source);
    if (p.kind === 'table') {
      assert.equal(p.cells.length, source.cells.reduce((n, row) => n + row.length, 0));
      for (const cell of p.cells) {
        assert.equal(cell.value, source.cells[cell.row][cell.column]);
        assert.equal(p.values[cell.valueOrdinal], String(cell.value));
        near(cell.point[0], cell.row * p.rowGain); near(cell.point[1], cell.column * p.columnGain); near(cell.point[2], p.origin[2] + cell.valueOrdinal * p.valueGain); cells++;
      }
    } else {
      assert.deepEqual(p.edges.map(e => [e.from, e.to, e.label]), source.edges.map(e => [e.from, e.to, e.label]));
      const names = new Map(p.nodes.map(n => [n.id, n]));
      for (const n of p.nodes) { near(n.point[0], (n.x - p.xMin) * p.xGain); near(n.point[1], (n.y - p.yMin) * p.yGain); near(n.point[2], p.origin[2]); }
      for (const e of p.edges) {
        assert.ok(names.has(e.from) && names.has(e.to));
        if (e.from === e.to) assert.equal(e.path.length, 33);
        else assert.deepEqual(e.path, [names.get(e.from).point, names.get(e.to).point]);
        assert.ok(actual.primitives.some(q => q.fidelity_kind === 'logic_arrow' && q.from === e.from && q.to === e.to && q.panel === p.index)); edges++;
      }
    }
  }
  for (const p of actual.primitives) for (const point of p.points) assert.ok(point.every(Number.isFinite));
  assert.ok(actual.note.includes('do not measure cardinality')); states++;
}
for (const [station] of lab.stations) {
  check({station});
  for (const c of lab.controls.filter(c => c.key !== 'station' && (!c.stations || c.stations.includes(station)))) for (const value of c.options ? c.options.map(o => o.value) : [c.min, c.max]) check({station, [c.key]: value});
}
for (let mask = 0; mask < 512; mask++) check({station: 'relations', relationSize: 3, relationMask: mask});
check({station: 'powerset', rows: [0, 0, 0, 0, 0, 0]}); check({station: 'powerset', rows: [63, 63, 63, 63, 63, 63]});
const bus = window.PrimerLessonStateBus, keys = ['math.5.complex-analysis', 'phys.4.quantum', 'math.5.topology', 'phys.4.relativity', 'math.5.abstract', 'phys.5.quantum-info', 'math.5.logic', 'phys.4.em-maxwell', 'phys.5.gr-cosmo'];
const receivers = keys.map(key => ({key, isConnected: true, seen: []}));
receivers.forEach(r => bus.join(r.key, r, state => r.seen.push(state)));
for (const key of keys) bus.publish(key, {}, {owner: key});
receivers.forEach(r => assert.deepEqual(r.seen, [{owner: r.key}]));
const ignored = {isConnected: true, seen: []}; bus.join('untrusted', ignored, state => ignored.seen.push(state)); bus.publish('untrusted', {}, {secret: false}); assert.deepEqual(ignored.seen, []);
console.log(`Verified ${states} exact logic spatial states, ${cells} table cells, ${edges} directed edges and nine-key state isolation.`);

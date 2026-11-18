'use strict';
const Model = {
  UNIVERSE: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  SETS: {even: n => n % 2 === 0, odd: n => n % 2 === 1, three: n => n % 3 === 0, prime: n => [2, 3, 5, 7, 11].includes(n), big: n => n > 6, square: n => [1, 4, 9].includes(n)},
  members: name => Model.UNIVERSE.filter(Model.SETS[name]),
  union: (a, b) => Model.UNIVERSE.filter(n => Model.SETS[a](n) || Model.SETS[b](n)),
  intersection: (a, b) => Model.UNIVERSE.filter(n => Model.SETS[a](n) && Model.SETS[b](n)),
  difference: (a, b) => Model.UNIVERSE.filter(n => Model.SETS[a](n) && !Model.SETS[b](n)),
  complement: a => Model.UNIVERSE.filter(n => !Model.SETS[a](n)),
  // Number of subsets of a set with k members.
  subsets: k => 2 ** k,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [0, 13], y: [0, 2], grid: false}), A = Model.members(v.a), B = Model.members(v.b), both = Model.intersection(v.a, v.b), either = Model.union(v.a, v.b), list = s => s.length ? '{' + s.join(', ') + '}' : '∅ (empty)';
  for (const n of Model.UNIVERSE) { const inA = A.includes(n), inB = B.includes(n); p.point(n, 1, inA && inB ? '#6b3fa0' : inA ? '#215783' : inB ? '#c9631f' : '#c3ccd2', 15, !inA && !inB); p.text(String(n), n, 1, '#172533', n > 9 ? -9 : -5, 44); }
  return {sum: '|A ∪ B| = ' + A.length + ' + ' + B.length + ' − ' + both.length + ' = ' + either.length,
    rows: [['A', list(A), String(A.length)], ['B', list(B), String(B.length)], ['A ∩ B (in both)', list(both), String(both.length)], ['A ∪ B (in either)', list(either), String(either.length)], ['A \\ B (in A, not B)', list(Model.difference(v.a, v.b)), String(Model.difference(v.a, v.b).length)],
      ['Complement of A', list(Model.complement(v.a)), String(Model.complement(v.a).length)], ['Subsets of A', '2 to the power ' + A.length, String(Model.subsets(A.length))]],
    result: both.length ? 'Adding the sizes counts the ' + both.length + ' shared ' + (both.length === 1 ? 'member' : 'members') + ' twice, so subtract the intersection once. Purple is in both, blue only in A, orange only in B.' : 'The sets are disjoint, so the size of the union is just the two sizes added.'};
}
function start() {
  const ids = ["a", "b"];
  function draw() {
    const v = {};
    for (const id of ids) {
      const node = Kit.get(id); v[id] = node.type === 'range' ? node.valueAsNumber : node.value;
      if (node.type === 'range') Kit.say(id, v[id], String(v[id]));
    }
    const out = render(v);
    Kit.get('sum').textContent = out.sum || '';
    Kit.rows(Kit.get('rows'), out.rows); Kit.get('result').textContent = out.result;
  }
  Kit.bind(ids, draw);
}
if (typeof module === 'object') module.exports = Model; else start();

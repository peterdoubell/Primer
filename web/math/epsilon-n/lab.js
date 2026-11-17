'use strict';
const Model = {
  SEQUENCES: {inv: {a: n => 1 / n, limit: 0}, ratio: {a: n => (n + 1) / n, limit: 1}, alt: {a: n => (n % 2 ? -1 : 1) / n, limit: 0}, geo: {a: n => 0.5 ** n, limit: 0}},
  term: (name, n) => Model.SEQUENCES[name].a(n),
  gap: (name, n) => Math.abs(Model.term(name, n) - Model.SEQUENCES[name].limit),
  // Smallest N with |aₙ − L| < ε for all n ≥ N. The gap shrinks steadily for each of these sequences.
  threshold(name, eps) { let n = 1; while (Model.gap(name, n) >= eps - 1e-12) n++; return n; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const s = Model.SEQUENCES[v.seq], N = Model.threshold(v.seq, v.eps), p = Kit.plot(canvas, {x: [0, 41], y: [s.limit - 1.1, s.limit + 1.1], xlabel: 'n', ylabel: 'aₙ'});
  p.line(0, s.limit + v.eps, 41, s.limit + v.eps, '#3c7a4b', 1.5, [6, 5]); p.line(0, s.limit - v.eps, 41, s.limit - v.eps, '#3c7a4b', 1.5, [6, 5]); p.line(0, s.limit, 41, s.limit, '#172533', 1);
  if (N <= 40) p.line(N, s.limit - 1.1, N, s.limit + 1.1, '#963d18', 1.5, [3, 4]);
  for (let n = 1; n <= 40; n++) p.point(n, Model.term(v.seq, n), n >= N ? '#215783' : '#9aa6ae', 4);
  return {sum: 'ε = ' + v.eps + '  →  N = ' + N,
    rows: [['Limit L', String(s.limit)], ['Tolerance ε', String(v.eps)], ['Smallest N that works', String(N)], ['|a_N − L|', Kit.fmt(Model.gap(v.seq, N))], ['|a_(N−1) − L| (just too far)', N > 1 ? Kit.fmt(Model.gap(v.seq, N - 1)) : 'no earlier term']],
    result: 'From n = ' + N + ' onward every term lies inside the green band of width ε around ' + s.limit + '. Shrink ε and N grows, but there is always an N: that is what convergence means.'};
}
function start() {
  const ids = ["seq", "eps"];
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

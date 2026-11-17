'use strict';
const Model = {
  solve(a, b, c, d) {
    if (a === c) return {kind: b === d ? 'all' : 'none'};
    const x = (d - b) / (a - c); return {kind: 'one', x, y: a * x + b};
  },
  side: (m, k) => ((m === 0 ? '' : (m === 1 ? '' : m === -1 ? '−' : String(m).replace('-', '−')) + 'x') + (k === 0 ? (m === 0 ? '0' : '') : (m === 0 ? '' : k > 0 ? ' + ' : ' − ') + (m === 0 ? String(k).replace('-', '−') : Math.abs(k)))),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.solve(v.a, v.b, v.c, v.d), p = Kit.plot(canvas, {x: [-10, 10], y: [-30, 30]});
  p.curve(x => v.a * x + v.b, '#215783'); p.curve(x => v.c * x + v.d, '#963d18'); if (r.kind === 'one') { p.point(r.x, r.y, '#172533', 7); p.text('x = ' + Kit.fmt(r.x), r.x, r.y); }
  const start = Model.side(v.a, v.b) + ' = ' + Model.side(v.c, v.d);
  if (r.kind !== 'one') return {sum: start, rows: [['Start', start], ['Subtract ' + Model.side(v.c, 0) + ' from both sides', Model.side(0, v.b) + ' = ' + Model.side(0, v.d)]],
    result: r.kind === 'all' ? 'Both sides are the same line, so every value of x is a solution.' : 'The lines are parallel and never meet, so there is no solution.'};
  return {sum: start + '  →  x = ' + Kit.fmt(r.x),
    rows: [['Start', start], ['Collect x on the left', Model.side(v.a - v.c, v.b) + ' = ' + Model.side(0, v.d)], ['Collect numbers on the right', Model.side(v.a - v.c, 0) + ' = ' + Model.side(0, v.d - v.b)], ['Divide by ' + String(v.a - v.c).replace('-', '−'), 'x = ' + Kit.fmt(r.x)], ['Check: both sides equal', Kit.fmt(r.y)]],
    result: 'Do the same thing to both sides at every step. The lines cross at x = ' + Kit.fmt(r.x) + ', where both sides equal ' + Kit.fmt(r.y) + '.'};
}
function start() {
  const ids = ["a", "b", "c", "d"];
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

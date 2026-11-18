'use strict';
const Model = {
  solve(a, b, c) {
    if (a === 0) return null;
    const D = b * b - 4 * a * c, h = -b / (2 * a), k = c - b * b / (4 * a);
    if (D > 0) { const s = Math.sqrt(D), roots = [(-b - s) / (2 * a), (-b + s) / (2 * a)].sort((x, y) => x - y); return {D, h, k, kind: 'two', roots}; }
    if (D === 0) return {D, h, k, kind: 'one', roots: [h]};
    return {D, h, k, kind: 'complex', re: h, im: Math.sqrt(-D) / Math.abs(2 * a)};
  },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.solve(v.a, v.b, v.c), p = Kit.plot(canvas, {x: [-10, 10], y: [-30, 30]}), m = t => Kit.fmt(t).replace('-', '−');
  p.curve(x => v.a * x * x + v.b * x + v.c, '#215783');
  if (!r) return {sum: 'Not a quadratic', rows: [['a', '0']], result: 'With a = 0 the x² term vanishes and the equation is linear.'};
  p.point(r.h, r.k, '#3c7a4b', 6); p.text('vertex', r.h, r.k); if (r.roots) for (const x of r.roots) p.point(x, 0, '#963d18', 6); p.line(r.h, -30, r.h, 30, '#9aa6ae', 1, [5, 5]);
  const roots = r.kind === 'complex' ? m(r.re) + ' ± ' + Kit.fmt(r.im) + 'i' : r.roots.map(m).join(' and ');
  return {sum: 'x = ' + roots,
    rows: [['Discriminant b² − 4ac', m(r.D)], ['Number of real roots', r.kind === 'two' ? '2' : r.kind === 'one' ? '1 (repeated)' : '0'], ['Roots from the formula', roots], ['Vertex', '(' + m(r.h) + ', ' + m(r.k) + ')'],
      ['Completed square', m(v.a) + '(x ' + (r.h < 0 ? '+ ' : '− ') + Kit.fmt(Math.abs(r.h)) + ')² ' + (r.k < 0 ? '− ' : '+ ') + Kit.fmt(Math.abs(r.k))], ['Axis of symmetry', 'x = ' + m(r.h)]],
    result: r.kind === 'two' ? 'The discriminant is positive, so the parabola crosses the x-axis twice. The roots sit the same distance either side of the axis of symmetry.' : r.kind === 'one' ? 'The discriminant is zero, so the parabola just touches the x-axis at its vertex.' : 'The discriminant is negative, so the parabola never reaches the x-axis. The roots are complex numbers.'};
}
function start() {
  const ids = ["a", "b", "c"];
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

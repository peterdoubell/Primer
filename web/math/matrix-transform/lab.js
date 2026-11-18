'use strict';
const Model = {
  det: (a, b, c, d) => a * d - b * c,
  trace: (a, b, c, d) => a + d,
  apply: (a, b, c, d, x, y) => [a * x + b * y, c * x + d * y],
  eigen(a, b, c, d) {
    const t = a + d, disc = t * t - 4 * (a * d - b * c);
    return disc >= 0 ? {real: true, values: [(t + Math.sqrt(disc)) / 2, (t - Math.sqrt(disc)) / 2]} : {real: false, re: t / 2, im: Math.sqrt(-disc) / 2};
  },
  inverse(a, b, c, d) { const D = a * d - b * c; return D ? [d / D, -b / D, -c / D, a / D].map(x => x + 0) : null; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-7, 7], y: [-7, 7]}), D = Model.det(v.a, v.b, v.c, v.d), e = Model.eigen(v.a, v.b, v.c, v.d), inv = Model.inverse(v.a, v.b, v.c, v.d), m = t => Kit.fmt(t).replace('-', '−');
  const square = [[0, 0], [1, 0], [1, 1], [0, 1]], image = square.map(([x, y]) => Model.apply(v.a, v.b, v.c, v.d, x, y));
  square.forEach((q, i) => { const n = square[(i + 1) % 4]; p.line(q[0], q[1], n[0], n[1], '#9aa6ae', 2); });
  image.forEach((q, i) => { const n = image[(i + 1) % 4]; p.line(q[0], q[1], n[0], n[1], '#215783', 3); });
  p.arrow(0, 0, v.a, v.c, '#963d18'); p.arrow(0, 0, v.b, v.d, '#3c7a4b'); p.text('column 1', v.a, v.c); p.text('column 2', v.b, v.d);
  return {sum: 'determinant = ' + m(D),
    rows: [['Where (1, 0) goes', '(' + m(v.a) + ', ' + m(v.c) + ')'], ['Where (0, 1) goes', '(' + m(v.b) + ', ' + m(v.d) + ')'], ['Determinant ad − bc', m(D)], ['Trace a + d', m(Model.trace(v.a, v.b, v.c, v.d))],
      ['Eigenvalues', e.real ? e.values.map(m).join(' and ') : m(e.re) + ' ± ' + Kit.fmt(e.im) + 'i'], ['Inverse', inv ? '[' + inv.slice(0, 2).map(m).join(', ') + ' ; ' + inv.slice(2).map(m).join(', ') + ']' : 'none']],
    result: D === 0 ? 'The determinant is 0: the unit square is flattened onto a line or a point, so the matrix cannot be undone.' : 'The unit square (grey) becomes a parallelogram of area ' + Kit.fmt(Math.abs(D)) + (D < 0 ? ', flipped over because the determinant is negative.' : '.') + (e.real ? ' The eigenvalues multiply to the determinant and add to the trace.' : ' Complex eigenvalues mean no direction is kept: the matrix turns everything.')};
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

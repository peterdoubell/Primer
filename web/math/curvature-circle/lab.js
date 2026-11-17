'use strict';
const Model = {
  // Signed curvature of y = ax² at x: y″ / (1 + y′²)^(3/2).
  curvature: (a, x) => 2 * a / (1 + (2 * a * x) ** 2) ** 1.5,
  radius: (a, x) => { const k = Model.curvature(a, x); return k ? 1 / Math.abs(k) : Infinity; },
  // Centre of the osculating circle, or null on a straight line.
  centre(a, x) { if (!a) return null; const d = 2 * a * x, y = a * x * x, s = (1 + d * d) / (2 * a); return [x - d * s, y + s]; },
  tangent: (a, x) => 2 * a * x,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const y = v.a * v.x * v.x, k = Model.curvature(v.a, v.x), R = Model.radius(v.a, v.x), c = Model.centre(v.a, v.x), slope = Model.tangent(v.a, v.x), p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5]}), m = n => Kit.fmt(n).replace('-', '−');
  p.curve(t => v.a * t * t, '#215783'); p.curve(t => y + slope * (t - v.x), '#9aa6ae', -5, 5, 1.5);
  if (c && R < 60) { for (let i = 0; i < 180; i++) { const t0 = i * Math.PI / 90, t1 = (i + 1) * Math.PI / 90; p.line(c[0] + R * Math.cos(t0), c[1] + R * Math.sin(t0), c[0] + R * Math.cos(t1), c[1] + R * Math.sin(t1), '#963d18', 2); } p.line(v.x, y, c[0], c[1], '#963d18', 1, [5, 5]); p.point(c[0], c[1], '#963d18', 4); }
  p.point(v.x, y, '#172533', 6);
  return {sum: 'κ = ' + m(k) + (Number.isFinite(R) ? '   radius = ' + Kit.fmt(R) : ''),
    rows: [['Point', '(' + m(v.x) + ', ' + m(y) + ')'], ['Slope of the tangent', m(slope)], ['Curvature κ', m(k)], ['Radius of curvature 1/|κ|', Number.isFinite(R) ? Kit.fmt(R) : 'infinite'], ['Centre of the circle', c ? '(' + m(c[0]) + ', ' + m(c[1]) + ')' : 'none'], ['Curvature at the vertex', m(Model.curvature(v.a, 0))]],
    result: v.a === 0 ? 'A straight line has curvature 0 everywhere: it does not turn, and no circle fits it.' : 'The parabola turns fastest at its vertex, where κ = 2a = ' + m(2 * v.a) + ', and straightens further out. The red circle shares the curve’s position, tangent and curvature at the point.'};
}
function start() {
  const ids = ["a", "x"];
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

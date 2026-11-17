'use strict';
const Model = {
  SURFACES: {bowl: {f: (x, y) => x * x + y * y, fx: (x, y) => 2 * x, fy: (x, y) => 2 * y}, saddle: {f: (x, y) => x * x - y * y, fx: (x, y) => 2 * x, fy: (x, y) => -2 * y}, product: {f: (x, y) => x * y, fx: (x, y) => y, fy: (x, y) => x}},
  value: (name, x, y) => Model.SURFACES[name].f(x, y),
  gradient: (name, x, y) => [Model.SURFACES[name].fx(x, y), Model.SURFACES[name].fy(x, y)],
  // Rate of change of f in the direction at the given angle from the x-axis.
  directional(name, x, y, degrees) { const [gx, gy] = Model.gradient(name, x, y), t = degrees * Math.PI / 180; return gx * Math.cos(t) + gy * Math.sin(t); },
  steepest: (name, x, y) => Math.hypot(...Model.gradient(name, x, y)),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-2.6, 2.6], y: [-2.6, 2.6], xlabel: 'x', ylabel: 'y'}), [gx, gy] = Model.gradient(v.surface, v.x, v.y), t = v.angle * Math.PI / 180, m = n => Kit.fmt(n).replace('-', '−');
  const cell = 0.2, w = Math.abs(p.X(cell) - p.X(0)) + 1, h = Math.abs(p.Y(cell) - p.Y(0)) + 1;
  for (let x = -2.5; x < 2.5 - 1e-9; x += cell) for (let y = -2.5; y < 2.5 - 1e-9; y += cell) { const z = Math.max(-1, Math.min(1, Model.value(v.surface, x + cell / 2, y + cell / 2) / 8)); p.ctx.fillStyle = z >= 0 ? 'rgba(150,61,24,' + (0.08 + 0.6 * z) + ')' : 'rgba(33,87,131,' + (0.08 - 0.6 * z) + ')'; p.ctx.fillRect(p.X(x), p.Y(y + cell), w, h); }
  const scale = 0.35; p.arrow(v.x, v.y, v.x + gx * scale, v.y + gy * scale, '#172533'); p.arrow(v.x, v.y, v.x + Math.cos(t) * 0.9, v.y + Math.sin(t) * 0.9, '#3c7a4b', 2); p.point(v.x, v.y, '#172533', 5);
  return {sum: '∇f = (' + m(gx) + ', ' + m(gy) + ')',
    rows: [['f(x, y)', m(Model.value(v.surface, v.x, v.y))], ['∂f/∂x (slope going east)', m(gx)], ['∂f/∂y (slope going north)', m(gy)], ['Gradient', '(' + m(gx) + ', ' + m(gy) + ')'], ['Steepest slope', Kit.fmt(Model.steepest(v.surface, v.x, v.y))], ['Slope in the chosen direction', m(Model.directional(v.surface, v.x, v.y, v.angle))]],
    result: gx === 0 && gy === 0 ? 'The gradient is zero here: a critical point. For the bowl it is a minimum; for the other two it is a saddle.' : 'The black arrow is the gradient: the uphill direction. The slope in any other direction (green) is the gradient dotted with that direction, so it is never steeper. Red shading is high, blue is low.'};
}
function start() {
  const ids = ["surface", "x", "y", "angle"];
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

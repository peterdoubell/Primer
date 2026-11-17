'use strict';
const Model = {
  SHAPES: {circle: 0, triangle: 3, square: 4, rectangle: 4, pentagon: 5, hexagon: 6},
  sides: shape => Model.SHAPES[shape],
  corners: shape => Model.SHAPES[shape],
  // Corner points of the drawing, in a box from -1 to 1.
  points(shape) {
    if (shape === 'circle') return [];
    if (shape === 'rectangle') return [[-1, -0.55], [1, -0.55], [1, 0.55], [-1, 0.55]];
    const n = Model.SHAPES[shape], turn = shape === 'square' ? Math.PI / 4 : -Math.PI / 2;
    return Array.from({length: n}, (_, i) => [Math.cos(turn + 2 * Math.PI * i / n), Math.sin(turn + 2 * Math.PI * i / n)]);
  },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const ctx = canvas.getContext('2d'), cx = canvas.width / 2, cy = canvas.height / 2, r = canvas.height * 0.38, points = Model.points(v.shape);
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.lineWidth = 5; ctx.strokeStyle = '#215783'; ctx.fillStyle = '#dbe8f2'; ctx.beginPath();
  if (!points.length) ctx.arc(cx, cy, r, 0, 2 * Math.PI); else points.forEach(([x, y], i) => i ? ctx.lineTo(cx + r * x, cy + r * y) : ctx.moveTo(cx + r * x, cy + r * y));
  ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#963d18'; for (const [x, y] of points) { ctx.beginPath(); ctx.arc(cx + r * x, cy + r * y, 8, 0, 2 * Math.PI); ctx.fill(); }
  const n = Model.sides(v.shape);
  return {sum: v.shape[0].toUpperCase() + v.shape.slice(1),
    rows: Object.keys(Model.SHAPES).map(shape => [shape, String(Model.sides(shape)), String(Model.corners(shape))]),
    result: n ? 'A ' + v.shape + ' has ' + n + ' straight sides and ' + n + ' corners. A shape with straight sides has as many corners as sides.' : 'A circle has no straight sides and no corners. It is one curved line.'};
}
function start() {
  const ids = ["shape"];
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

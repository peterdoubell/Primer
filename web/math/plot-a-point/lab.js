'use strict';
const Model = {
  quadrant(x, y) {
    if (!x && !y) return 'at the origin'; if (!y) return 'on the x-axis'; if (!x) return 'on the y-axis';
    return 'in the ' + (x > 0 ? (y > 0 ? 'first' : 'fourth') : (y > 0 ? 'second' : 'third')) + ' quadrant';
  },
  distance: (x, y) => Math.hypot(x, y),
  reflectX: (x, y) => [x, -y], reflectY: (x, y) => [-x, y],
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-7, 7], y: [-7, 7], xlabel: 'x', ylabel: 'y'}), fx = Model.reflectX(v.x, v.y), fy = Model.reflectY(v.x, v.y);
  p.line(v.x, 0, v.x, v.y, '#963d18', 2, [6, 5]); p.line(0, v.y, v.x, v.y, '#963d18', 2, [6, 5]); p.line(0, 0, v.x, v.y, '#9aa6ae', 1.5);
  p.point(fx[0], fx[1], '#215783', 5, true); p.point(fy[0], fy[1], '#3c7a4b', 5, true); p.point(v.x, v.y, '#963d18', 7); p.text(('(' + v.x + ', ' + v.y + ')').replace(/-/g, '−'), v.x, v.y);
  return {sum: ('(' + v.x + ', ' + v.y + ')').replace(/-/g, '−'),
    rows: [['Where is it?', Model.quadrant(v.x, v.y)], ['Distance from the origin', Kit.fmt(Model.distance(v.x, v.y))], ['Mirror image in the x-axis', '(' + fx.join(', ') + ')'], ['Mirror image in the y-axis', '(' + fy.join(', ') + ')']],
    result: 'Go ' + Math.abs(v.x) + (v.x < 0 ? ' left' : ' right') + ', then ' + Math.abs(v.y) + (v.y < 0 ? ' down' : ' up') + '. The point is ' + Model.quadrant(v.x, v.y) + '.'};
}
function start() {
  const ids = ["x", "y"];
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

'use strict';
const Model = {
  add: (u, w) => [u[0] + w[0], u[1] + w[1]],
  dot: (u, w) => u[0] * w[0] + u[1] * w[1],
  length: u => Math.hypot(u[0], u[1]),
  // Angle between the vectors in degrees; null if either is the zero vector.
  angle(u, w) { const d = Model.length(u) * Model.length(w); return d ? Math.acos(Math.max(-1, Math.min(1, Model.dot(u, w) / d))) * 180 / Math.PI : null; },
  // Signed length of the shadow of u on w.
  projection(u, w) { const l = Model.length(w); return l ? Model.dot(u, w) / l : null; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const u = [v.ux, v.uy], w = [v.vx, v.vy], s = Model.add(u, w), angle = Model.angle(u, w), p = Kit.plot(canvas, {x: [-11, 11], y: [-11, 11]}), m = t => Kit.fmt(t).replace('-', '−');
  p.arrow(0, 0, u[0], u[1], '#215783'); p.arrow(0, 0, w[0], w[1], '#3c7a4b'); p.line(u[0], u[1], s[0], s[1], '#3c7a4b', 2, [6, 5]); p.arrow(0, 0, s[0], s[1], '#963d18');
  p.text('u', u[0], u[1]); p.text('v', w[0], w[1]); p.text('u + v', s[0], s[1]);
  const dot = Model.dot(u, w);
  return {sum: 'u + v = (' + m(s[0]) + ', ' + m(s[1]) + ')   u · v = ' + m(dot),
    rows: [['u + v', '(' + m(s[0]) + ', ' + m(s[1]) + ')'], ['Length of u', Kit.fmt(Model.length(u))], ['Length of v', Kit.fmt(Model.length(w))], ['Length of u + v', Kit.fmt(Model.length(s))], ['Dot product u · v', m(dot)],
      ['Angle between u and v', angle === null ? 'undefined for a zero vector' : Kit.fmt(angle) + '°'], ['Shadow of u along v', Model.projection(u, w) === null ? 'undefined' : m(Model.projection(u, w))]],
    result: angle === null ? 'The zero vector has no direction, so the angle is not defined.' : dot === 0 ? 'The dot product is 0, so the vectors are perpendicular.' : 'The dot product is ' + (dot > 0 ? 'positive: the vectors point broadly the same way.' : 'negative: the vectors point broadly opposite ways.') + ' The length of u + v is never more than the two lengths added.'};
}
function start() {
  const ids = ["ux", "uy", "vx", "vy"];
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

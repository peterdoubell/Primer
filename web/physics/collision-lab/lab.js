'use strict';
const Model = {
  // Coefficient of restitution e: relative speed after = e × relative speed before.
  collide(m1, v1, m2, v2, e) {
    const p = m1 * v1 + m2 * v2, total = m1 + m2;
    return [(p + m2 * e * (v2 - v1)) / total, (p + m1 * e * (v1 - v2)) / total];
  },
  momentum: (m1, v1, m2, v2) => m1 * v1 + m2 * v2,
  kinetic: (m1, v1, m2, v2) => m1 * v1 * v1 / 2 + m2 * v2 * v2 / 2,
  // They only collide if cart 1 (on the left) is catching up with cart 2.
  approaching: (v1, v2) => v1 > v2,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const hit = Model.approaching(v.v1, v.v2), [a, b] = hit ? Model.collide(v.m1, v.v1, v.m2, v.v2, v.e) : [v.v1, v.v2], p = Kit.plot(canvas, {x: [-14, 14], y: [0, 4], grid: false}), m = n => Kit.fmt(n, 3).replace('-', '−');
  const row = (y, u1, u2, label) => { p.line(-14, y - 0.35, 14, y - 0.35, '#9aa6ae', 1); p.point(-3, y, '#215783', 6 + v.m1 * 1.6); p.point(3, y, '#963d18', 6 + v.m2 * 1.6); if (u1) p.arrow(-3, y + 0.6, -3 + u1, y + 0.6, '#215783'); if (u2) p.arrow(3, y + 0.6, 3 + u2, y + 0.6, '#963d18'); p.text(label, -14, y + 0.6, '#172533', 4, 0); };
  row(2.7, v.v1, v.v2, 'before'); row(0.8, a, b, 'after');
  const k0 = Model.kinetic(v.m1, v.v1, v.m2, v.v2), k1 = Model.kinetic(v.m1, a, v.m2, b);
  return {sum: hit ? 'After: ' + m(a) + ' m/s and ' + m(b) + ' m/s' : 'The carts do not collide',
    rows: [['Velocity of cart 1 (m/s)', m(v.v1), m(a)], ['Velocity of cart 2 (m/s)', m(v.v2), m(b)], ['Total momentum (kg·m/s)', m(Model.momentum(v.m1, v.v1, v.m2, v.v2)), m(Model.momentum(v.m1, a, v.m2, b))], ['Total kinetic energy (J)', m(k0), m(k1)], ['Kinetic energy lost (J)', '—', m(Math.max(0, k0 - k1))]],
    result: !hit ? 'Cart 1 is not catching up with cart 2, so nothing changes.' : v.e === 1 ? 'An elastic collision: both momentum and kinetic energy are the same before and after.' : 'Momentum is unchanged, but ' + m(k0 - k1) + ' J of kinetic energy has become heat, sound and deformation.' + (v.e === 0 ? ' The carts stick together and move as one.' : '')};
}
function start() {
  const ids = ["m1", "v1", "m2", "v2", "e"];
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

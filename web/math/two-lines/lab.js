'use strict';
const Model = {
  // Lines y = m1 x + k1 and y = m2 x + k2.
  solve(m1, k1, m2, k2) {
    if (m1 === m2) return k1 === k2 ? {kind: 'same'} : {kind: 'parallel'};
    const x = (k2 - k1) / (m1 - m2);
    return {kind: 'one', x, y: m1 * x + k1};
  },
};
function start() {
  const canvas = Kit.get('graph'), eq = (m, k) => 'y = ' + Kit.fmt(m) + 'x ' + (k < 0 ? '− ' : '+ ') + Kit.fmt(Math.abs(k));
  function draw() {
    const [m1, k1, m2, k2] = ['m1', 'k1', 'm2', 'k2'].map(Kit.num);
    Kit.say('m1', m1, 'slope ' + m1); Kit.say('k1', k1, 'intercept ' + k1); Kit.say('m2', m2, 'slope ' + m2); Kit.say('k2', k2, 'intercept ' + k2);
    const p = Kit.plot(canvas, {x: [-10, 10], y: [-10, 10]});
    p.curve(v => m1 * v + k1, '#215783'); p.curve(v => m2 * v + k2, '#963d18');
    const s = Model.solve(m1, k1, m2, k2);
    if (s.kind === 'one' && Math.abs(s.x) <= 10 && Math.abs(s.y) <= 10) { p.point(s.x, s.y, '#172533'); p.text('(' + Kit.fmt(s.x, 3) + ', ' + Kit.fmt(s.y, 3) + ')', s.x, s.y); }
    Kit.rows(Kit.get('rows'), [['Blue line', eq(m1, k1)], ['Orange line', eq(m2, k2)],
      ['Set them equal', Kit.fmt(m1) + 'x + ' + Kit.fmt(k1) + ' = ' + Kit.fmt(m2) + 'x + ' + Kit.fmt(k2)],
      ['Collect x', s.kind === 'one' ? Kit.fmt(m1 - m2) + 'x = ' + Kit.fmt(k2 - k1) : '0 = ' + Kit.fmt(k2 - k1)]]);
    Kit.get('result').textContent = s.kind === 'one' ? 'One solution: x = ' + Kit.fmt(s.x) + ', y = ' + Kit.fmt(s.y) + '. The lines cross once because their slopes differ.'
      : s.kind === 'parallel' ? 'No solution. The slopes are equal and the intercepts differ, so the lines are parallel and never meet.'
      : 'Infinitely many solutions. Both equations describe the same line.';
    canvas.setAttribute('aria-label', 'Two lines: ' + eq(m1, k1) + ' and ' + eq(m2, k2) + '. ' + Kit.get('result').textContent);
  }
  Kit.bind(['m1', 'k1', 'm2', 'k2'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

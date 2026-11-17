'use strict';
const Model = {
  // Net force, positive to the right.
  net: (right, left) => right - left,
  outcome(right, left) { const n = right - left; return n > 0 ? 'speeds up to the right' : n < 0 ? 'speeds up to the left' : 'no change in motion'; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const n = Model.net(v.right, v.left), p = Kit.plot(canvas, {x: [-14, 14], y: [-2, 3], grid: false});
  p.line(-14, -1, 14, -1, '#172533', 2); p.line(-1.5, 0, 1.5, 0, '#8a6d3b', 90);
  if (v.right) p.arrow(-1.6 - v.right, 0.4, -1.6, 0.4, '#215783', 5); if (v.left) p.arrow(1.6 + v.left, 0.4, 1.6, 0.4, '#963d18', 5);
  if (n) p.arrow(0, 2.3, n, 2.3, '#3c7a4b', 5); p.text(n ? 'overall force' : 'forces balance', n ? n / 2 : 0, 2.3, '#172533', -40, -12);
  return {sum: 'Overall force: ' + Math.abs(n) + (n ? (n > 0 ? ' to the right' : ' to the left') : ''),
    rows: [['Push to the right', String(v.right)], ['Push to the left', String(v.left)], ['Overall force', n ? Math.abs(n) + (n > 0 ? ' to the right' : ' to the left') : '0 (balanced)'], ['What the box does', Model.outcome(v.right, v.left)]],
    result: n ? 'The pushes do not balance, so the box speeds up in the direction of the bigger push.' : 'The pushes balance. A still box stays still, and a moving box keeps moving the same way. It takes an unbalanced force to start or stop motion.'};
}
function start() {
  const ids = ["right", "left"];
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

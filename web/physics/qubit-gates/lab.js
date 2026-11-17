'use strict';
const Model = {
  // State cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩ as [[re, im], [re, im]].
  state(thetaDeg, phiDeg) { const t = thetaDeg * Math.PI / 360, f = phiDeg * Math.PI / 180; return [[Math.cos(t), 0], [Math.sin(t) * Math.cos(f), Math.sin(t) * Math.sin(f)]]; },
  apply(gate, [a, b]) {
    const s = Math.SQRT1_2;
    if (gate === 'X') return [b, a];
    if (gate === 'Z') return [a, [-b[0], -b[1]]];
    if (gate === 'H') return [[s * (a[0] + b[0]), s * (a[1] + b[1])], [s * (a[0] - b[0]), s * (a[1] - b[1])]];
    return [a, b];
  },
  // Probabilities of measuring 0 and 1.
  probabilities: ([a, b]) => [a[0] ** 2 + a[1] ** 2, b[0] ** 2 + b[1] ** 2],
  // Bloch vector (x, y, z).
  bloch([a, b]) { return [2 * (a[0] * b[0] + a[1] * b[1]), 2 * (a[0] * b[1] - a[1] * b[0]), a[0] ** 2 + a[1] ** 2 - b[0] ** 2 - b[1] ** 2]; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const before = Model.state(v.theta, v.phi), after = Model.apply(v.gate, before), P0 = Model.probabilities(before), P1 = Model.probabilities(after), B0 = Model.bloch(before), B1 = Model.bloch(after), p = Kit.plot(canvas, {x: [-1.5, 1.5], y: [-1.5, 1.5], grid: false}), f = n => Kit.fmt(Math.abs(n) < 1e-12 ? 0 : n, 3).replace('-', '−');
  for (let i = 0; i < 120; i++) p.line(Math.cos(i * Math.PI / 60), Math.sin(i * Math.PI / 60), Math.cos((i + 1) * Math.PI / 60), Math.sin((i + 1) * Math.PI / 60), '#9aa6ae', 1.5);
  p.line(-1, 0, 1, 0, '#d8dfe4', 1); p.line(0, -1, 0, 1, '#d8dfe4', 1); p.text('|0⟩', 0, 1, '#172533', -10, -10); p.text('|1⟩', 0, -1, '#172533', -10, 22); p.text('x', 1, 0, '#172533', 8, 4);
  p.arrow(0, 0, B0[0], B0[2], '#215783'); p.arrow(0, 0, B1[0], B1[2], '#963d18'); p.text('before', B0[0], B0[2], '#215783'); p.text('after', B1[0], B1[2], '#963d18', 8, 14);
  return {sum: 'P(0) = ' + f(P1[0]) + ', P(1) = ' + f(P1[1]) + ' after the gate',
    rows: [['Chance of measuring 0', f(P0[0]), f(P1[0])], ['Chance of measuring 1', f(P0[1]), f(P1[1])], ['Bloch vector x', f(B0[0]), f(B1[0])], ['Bloch vector y', f(B0[1]), f(B1[1])], ['Bloch vector z', f(B0[2]), f(B1[2])]],
    result: 'The arrow shows the state on the Bloch sphere, seen from the side (x across, z up; y points into the page). X swaps the poles, Z reverses x and y, and H exchanges the z and x directions. The phase φ changes nothing if you measure straight away, but it changes what H does: that is interference.'};
}
function start() {
  const ids = ["theta", "phi", "gate"];
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

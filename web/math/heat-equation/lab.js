'use strict';
const Model = {
  ALPHA: 0.1,
  // [mode number, starting size] pairs.
  INITIAL: {mode1: [[1, 1]], mode2: [[2, 1]], mode3: [[3, 1]], mix: [[1, 1], [3, 0.5]]},
  decay: (k, t) => Math.exp(-Model.ALPHA * k * k * Math.PI ** 2 * t),
  halfLife: k => Math.log(2) / (Model.ALPHA * k * k * Math.PI ** 2),
  // Solution of u_t = α u_xx with u = 0 at both ends.
  u: (name, x, t) => Model.INITIAL[name].reduce((sum, [k, size]) => sum + size * Model.decay(k, t) * Math.sin(k * Math.PI * x), 0),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [0, 1], y: [-1.6, 1.6], xlabel: 'position x', ylabel: 'temperature'});
  p.curve(x => Model.u(v.start, x, 0), '#9aa6ae', 0, 1, 2); p.curve(x => Model.u(v.start, x, v.t), '#963d18', 0, 1, 3);
  const middle = Model.u(v.start, 0.5, v.t);
  return {sum: 'Temperature at the middle: ' + Kit.fmt(Math.abs(middle) < 1e-9 ? 0 : middle, 3).replace('-', '−'),
    rows: Model.INITIAL[v.start].map(([k, size]) => ['sin(' + (k === 1 ? '' : k) + 'πx)', String(size), Kit.fmt(size * Model.decay(k, v.t), 3), Kit.fmt(Model.halfLife(k), 3)]),
    result: 'Mode k decays like e to the power −αk²π²t, so a mode with three times as many wiggles dies nine times as fast. Sharp detail vanishes first and the profile smooths toward the slowest mode. Grey is the start, red is now (α = ' + Model.ALPHA + ').'};
}
function start() {
  const ids = ["start", "t"];
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

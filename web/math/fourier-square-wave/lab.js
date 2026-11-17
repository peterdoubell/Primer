'use strict';
const Model = {
  // Square wave of height 1 and period 2π: (4/π) Σ sin((2j+1)x) / (2j+1).
  partial(terms, x) { let sum = 0; for (let j = 0; j < terms; j++) sum += Math.sin((2 * j + 1) * x) / (2 * j + 1); return 4 / Math.PI * sum; },
  square: x => Math.sin(x) >= 0 ? 1 : -1,
  // Share of the wave’s mean square captured by the first terms (Parseval).
  energy(terms) { let sum = 0; for (let j = 0; j < terms; j++) sum += 1 / (2 * j + 1) ** 2; return 8 / Math.PI ** 2 * sum; },
  // Root-mean-square distance between the wave and the partial sum.
  error: terms => Math.sqrt(Math.max(0, 1 - Model.energy(terms))),
  // Highest value of the partial sum, sampled finely across half a period.
  overshoot(terms) { let top = 0; for (let i = 1; i < 4000; i++) top = Math.max(top, Model.partial(terms, i * Math.PI / 4000)); return top; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-3.5, 3.5], y: [-1.5, 1.5]});
  p.line(-Math.PI, -1, 0, -1, '#9aa6ae', 2); p.line(0, -1, 0, 1, '#9aa6ae', 2); p.line(0, 1, Math.PI, 1, '#9aa6ae', 2); p.curve(x => Model.partial(v.terms, x), '#215783');
  return {sum: v.terms + (v.terms === 1 ? ' term' : ' terms') + ': root-mean-square error ' + Kit.fmt(Model.error(v.terms), 3),
    rows: [['Sine terms used', String(v.terms)], ['Highest frequency', String(2 * v.terms - 1)], ['Share of the energy captured', Kit.fmt(100 * Model.energy(v.terms), 4) + '%'], ['Root-mean-square error', Kit.fmt(Model.error(v.terms), 3)], ['Highest point of the sum', Kit.fmt(Model.overshoot(v.terms), 4)]],
    result: 'The mean-square error falls toward 0 as terms are added: the sums converge to the square wave in that sense. But the peak beside each jump stays near 1.18, about 9% of the jump too high. Convergence on average is not convergence at every point (the Gibbs phenomenon).'};
}
function start() {
  const ids = ["terms"];
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

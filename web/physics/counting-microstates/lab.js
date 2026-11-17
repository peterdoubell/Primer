'use strict';
const Model = {
  // Number of microstates with k heads among n coins.
  multiplicity(n, k) { if (k < 0 || k > n) return 0; let c = 1; for (let i = 1; i <= Math.min(k, n - k); i++) c = c * (n - i + 1) / i; return Math.round(c); },
  total: n => 2 ** n,
  probability: (n, k) => Model.multiplicity(n, k) / Model.total(n),
  // Entropy in units of Boltzmann’s constant: S/k = ln Ω.
  entropy: (n, k) => Math.log(Model.multiplicity(n, k)),
  // Chance of landing within the given fraction of N either side of half heads.
  near(n, fraction) { let sum = 0; for (let k = 0; k <= n; k++) if (Math.abs(k - n / 2) <= fraction * n) sum += Model.probability(n, k); return sum; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const k = Math.min(v.k, v.n), top = Model.multiplicity(v.n, Math.floor(v.n / 2)), p = Kit.plot(canvas, {x: [-1, v.n + 1], y: [0, top * 1.12], xlabel: 'heads', ylabel: 'microstates'});
  for (let i = 0; i <= v.n; i++) p.line(i, 0, i, Model.multiplicity(v.n, i), i === k ? '#963d18' : '#215783', 10);
  return {sum: 'Ω = ' + Model.multiplicity(v.n, k) + (Model.multiplicity(v.n, k) === 1 ? ' microstate' : ' microstates') + ' for ' + k + ' heads',
    rows: [['Microstates for this macrostate, Ω', String(Model.multiplicity(v.n, k))], ['All microstates, 2 to the power N', String(Model.total(v.n))], ['Probability of this macrostate', Kit.fmt(Model.probability(v.n, k), 3)], ['Entropy S ÷ k = ln Ω', Kit.fmt(Model.entropy(v.n, k), 4)], ['Chance of being within 10% of N of an even split', Kit.fmt(100 * Model.near(v.n, 0.1), 3) + '%']],
    result: 'Every single sequence is equally likely, but an even split can happen in far more ways than all heads. As N grows the peak sharpens: with the numbers of atoms in real matter, anything but the most probable macrostate is never seen. That is why entropy increases.'};
}
function start() {
  const ids = ["n", "k"];
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

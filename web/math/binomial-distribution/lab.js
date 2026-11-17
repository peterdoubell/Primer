'use strict';
const Model = {
  choose(n, k) { if (k < 0 || k > n) return 0; let c = 1; for (let i = 1; i <= Math.min(k, n - k); i++) c = c * (n - i + 1) / i; return Math.round(c); },
  pmf: (n, p, k) => Model.choose(n, k) * p ** k * (1 - p) ** (n - k),
  cdf(n, p, k) { let total = 0; for (let i = 0; i <= Math.min(k, n); i++) total += Model.pmf(n, p, i); return total; },
  mean: (n, p) => n * p,
  variance: (n, p) => n * p * (1 - p),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const k = Math.min(v.k, v.n), top = Math.max(...Array.from({length: v.n + 1}, (_, i) => Model.pmf(v.n, v.p, i))), p = Kit.plot(canvas, {x: [-1, 31], y: [0, top * 1.15], xlabel: 'successes', ylabel: 'probability'});
  for (let i = 0; i <= v.n; i++) p.line(i, 0, i, Model.pmf(v.n, v.p, i), i === k ? '#963d18' : i < k ? '#215783' : '#9aa6ae', 12);
  p.line(Model.mean(v.n, v.p), 0, Model.mean(v.n, v.p), top * 1.1, '#3c7a4b', 1.5, [5, 5]);
  return {sum: 'P(X = ' + k + ') = ' + Kit.fmt(Model.pmf(v.n, v.p, k)),
    rows: [['Ways to choose ' + k + ' of ' + v.n, String(Model.choose(v.n, k))], ['P(exactly ' + k + ')', Kit.fmt(Model.pmf(v.n, v.p, k))], ['P(at most ' + k + ')', Kit.fmt(Model.cdf(v.n, v.p, k))], ['P(more than ' + k + ')', Kit.fmt(Math.max(0, 1 - Model.cdf(v.n, v.p, k)))],
      ['Mean np', Kit.fmt(Model.mean(v.n, v.p))], ['Variance np(1 − p)', Kit.fmt(Model.variance(v.n, v.p))], ['Standard deviation', Kit.fmt(Math.sqrt(Model.variance(v.n, v.p)))]],
    result: 'The bars are tallest near the mean (green line) at np = ' + Kit.fmt(Model.mean(v.n, v.p)) + '. As n grows the shape approaches the bell curve, and the share of successes settles near p: the law of large numbers.'};
}
function start() {
  const ids = ["n", "p", "k"];
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

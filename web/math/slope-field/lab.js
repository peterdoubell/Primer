'use strict';
const Model = {
  LAWS: {
    growth: {label: "y′ = k·y", f: (y, k) => k * y, exact: (t, y0, k) => y0 * Math.exp(k * t), note: 'The rate is proportional to the amount, so the solution is exponential.'},
    cooling: {label: "y′ = −k·(y − 2)", f: (y, k) => -k * (y - 2), exact: (t, y0, k) => 2 + (y0 - 2) * Math.exp(-k * t), note: 'The solution relaxes towards the equilibrium y = 2 (Newton cooling).'},
    logistic: {label: "y′ = k·y·(1 − y/4)", f: (y, k) => k * y * (1 - y / 4), exact: (t, y0, k) => 4 / (1 + (4 / y0 - 1) * Math.exp(-k * t)), note: 'Growth slows as y nears the carrying capacity 4.'},
  },
  euler(f, y0, k, h, end) { const out = [[0, y0]]; let y = y0; for (let t = 0; t < end - 1e-9; t += h) { y += h * f(y, k); out.push([Math.min(t + h, end), y]); } return out; },
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const law = Model.LAWS[Kit.get('law').value], k = Kit.num('k'), y0 = Kit.num('y0'), h = Kit.num('h'), end = 5;
    Kit.say('k', k, 'k = ' + k); Kit.say('y0', y0, 'y(0) = ' + y0); Kit.say('h', h, 'step = ' + h);
    const p = Kit.plot(canvas, {x: [0, end], y: [0, 6], xlabel: 't', ylabel: 'y'});
    for (let t = 0.25; t < end; t += 0.5) for (let y = 0.25; y < 6; y += 0.5) { const s = law.f(y, k), d = 0.17 / Math.hypot(1, s); p.line(t - d, y - d * s, t + d, y + d * s, '#9aa5ad', 1.5); }
    p.curve(t => law.exact(t, y0, k), '#215783');
    const path = Model.euler(law.f, y0, k, h, end);
    path.forEach(([t, y], i) => { if (i) p.line(path[i - 1][0], path[i - 1][1], t, y, '#963d18', 2); p.point(t, y, '#963d18', 3); });
    const last = path[path.length - 1][1], truth = law.exact(end, y0, k);
    Kit.rows(Kit.get('rows'), [['Equation', law.label], ['Exact y(5)', Kit.fmt(truth)], ['Euler y(5) with step ' + h, Kit.fmt(last)], ['Euler error', Kit.fmt(Math.abs(last - truth), 3)]]);
    Kit.get('result').textContent = law.note + ' Short grey dashes show the slope at each point; the blue curve follows them exactly. Orange is Euler\'s method, which takes straight steps: halving the step roughly halves its error.';
    canvas.setAttribute('aria-label', 'Slope field for ' + law.label + ' with exact and Euler solutions. ' + law.note);
  }
  Kit.bind(['law', 'k', 'y0', 'h'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

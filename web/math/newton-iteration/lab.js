'use strict';
const Model = {
  step: (a, x) => (x + a / x) / 2,
  iterate(a, x0, steps) { const out = [x0]; for (let i = 0; i < steps; i++) out.push(Model.step(a, out[i])); return out; },
  error: (a, x) => Math.abs(x - Math.sqrt(a)),
  // Decimal digits that agree with the true root, capped by double precision.
  digits(a, x) { const e = Model.error(a, x) / Math.sqrt(a); return e < 1e-16 ? 16 : Math.max(0, Math.floor(-Math.log10(e))); },
  // Bisection on [lo, hi] for comparison: the bracket halves each step.
  bisect(a, lo, hi, steps) { for (let i = 0; i < steps; i++) { const mid = (lo + hi) / 2; if (mid * mid > a) hi = mid; else lo = mid; } return (lo + hi) / 2; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const xs = Model.iterate(v.a, v.x0, 6), p = Kit.plot(canvas, {x: [-0.6, 6.6], y: [0, 17.5], xlabel: 'step', ylabel: 'correct digits'});
  xs.forEach((x, i) => { p.line(i, 0, i, Model.digits(v.a, x), '#215783', 26); p.point(i, Model.digits(v.a, Model.bisect(v.a, 0, Math.max(v.a, 1), i * 1)), '#963d18', 4); });
  return {sum: '√' + v.a + ' ≈ ' + Kit.fmt(xs[6], 16),
    rows: xs.map((x, i) => [String(i), Kit.fmt(x, 16), Model.error(v.a, x) < 1e-15 ? 'below 1e-15' : Kit.fmt(Model.error(v.a, x), 3), String(Model.digits(v.a, x))]),
    result: 'Once the estimate is close, the error is roughly squared at every step, so the correct digits double: quadratic convergence. Bisection (red dots) gains only about one digit every three or four steps. The machine stores about 16 digits, so no method can do better than that here.'};
}
function start() {
  const ids = ["a", "x0"];
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

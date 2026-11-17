'use strict';
const Model = {
  apply(name, re, im) {
    if (name === 'square') return [re * re - im * im, 2 * re * im];
    if (name === 'exp') return [Math.exp(re) * Math.cos(im), Math.exp(re) * Math.sin(im)];
    const r2 = re * re + im * im; return r2 ? [re / r2, -im / r2] : null;
  },
  // f′(z): 2z, −1/z² and eᶻ.
  derivative(name, re, im) {
    if (name === 'square') return [2 * re, 2 * im];
    if (name === 'exp') return Model.apply('exp', re, im);
    const w = Model.apply('inverse', re, im); return w ? [-(w[0] * w[0] - w[1] * w[1]), -2 * w[0] * w[1]] : null;
  },
  modulus: z => Math.hypot(z[0], z[1]),
  argument: z => Math.atan2(z[1], z[0]) * 180 / Math.PI,
  text: z => (Kit.fmt(z[0]) + (z[1] < 0 ? ' − ' : ' + ') + Kit.fmt(Math.abs(z[1])) + 'i').replace(/^-/, '−'),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const z = [v.re, v.im], w = Model.apply(v.f, v.re, v.im), d = Model.derivative(v.f, v.re, v.im), p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5], xlabel: 'real', ylabel: 'imaginary'}), r = Model.modulus(z);
  for (let i = 0; i < 180; i++) { const t0 = i * Math.PI / 90, t1 = (i + 1) * Math.PI / 90, a = [r * Math.cos(t0), r * Math.sin(t0)], b = [r * Math.cos(t1), r * Math.sin(t1)]; p.line(a[0], a[1], b[0], b[1], '#8fb6d6', 1.5);
    const fa = Model.apply(v.f, a[0], a[1]), fb = Model.apply(v.f, b[0], b[1]); if (fa && fb && Model.modulus(fa) < 20 && Model.modulus(fb) < 20) p.line(fa[0], fa[1], fb[0], fb[1], '#e3b89c', 2); }
  p.point(z[0], z[1], '#215783', 6); p.text('z', z[0], z[1]); if (w) { p.point(w[0], w[1], '#963d18', 6); p.text('w', w[0], w[1]); }
  if (!w) return {sum: 'w is not defined', rows: [['z', '0']], result: '1/z has a pole at z = 0: the values grow without bound as z approaches 0.'};
  return {sum: 'w = ' + Model.text(w),
    rows: [['z', Model.text(z)], ['w = f(z)', Model.text(w)], ['Distance of w from 0', Kit.fmt(Model.modulus(w))], ['Angle of w', Kit.fmt(Model.argument(w)).replace('-', '−') + '°'], ['f′(z)', Model.text(d)], ['Local stretch |f′(z)|', Kit.fmt(Model.modulus(d))], ['Local turn', Model.modulus(d) ? Kit.fmt(Model.argument(d)).replace('-', '−') + '°' : 'undefined']],
    result: Model.modulus(d) === 0 ? 'The derivative is 0 here, so the map is not angle-preserving at this point: z² doubles angles at the origin.' : 'Near z the map multiplies small displacements by f′(z): it stretches them by ' + Kit.fmt(Model.modulus(d)) + ' and turns them through ' + Kit.fmt(Model.argument(d)).replace('-', '−') + '°. Angles between curves are kept. The pale blue circle through z maps to the orange curve.'};
}
function start() {
  const ids = ["f", "re", "im"];
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

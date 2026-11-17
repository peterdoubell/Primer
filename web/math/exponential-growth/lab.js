'use strict';
const Model = {
  value: (a, b, x) => a * b ** x,
  log: (b, y) => Math.log(y) / Math.log(b),
  // Time for the quantity to double (b > 1) or halve (b < 1); null when b = 1.
  changeTime: b => b === 1 ? null : Math.log(b > 1 ? 2 : 0.5) / Math.log(b),
  kind: b => b > 1 ? 'growth' : b < 1 ? 'decay' : 'constant',
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const a = Kit.num('start'), b = Kit.num('base'), x = Kit.num('x');
    Kit.say('start', a, 'a = ' + a); Kit.say('base', b, 'b = ' + b); Kit.say('x', x, 'x = ' + x);
    const top = Math.max(4, Model.value(a, b, b >= 1 ? 6 : -2) * 1.05);
    const p = Kit.plot(canvas, {x: [-2, 6], y: [0, top], xlabel: 'x', ylabel: 'y = a·bˣ'});
    p.curve(v => Model.value(a, b, v), '#215783');
    const y = Model.value(a, b, x);
    p.line(x, 0, x, y, '#963d18', 2, [5, 4]); p.line(-2, y, x, y, '#963d18', 2, [5, 4]); p.point(x, y);
    Kit.rows(Kit.get('rows'), [-1, 0, 1, 2, 3].map(step => ['x = ' + (x + step), Model.value(a, b, x + step), step === -1 ? '—' : '× ' + Kit.fmt(b)]));
    const t = Model.changeTime(b), kind = Model.kind(b);
    Kit.get('result').textContent = kind === 'constant' ? 'With b = 1 the quantity never changes.'
      : 'Exponential ' + kind + ': each step of 1 in x multiplies y by ' + Kit.fmt(b) + '. The quantity ' + (b > 1 ? 'doubles' : 'halves') + ' every ' + Kit.fmt(t) + ' units of x. Inverse: x = log base ' + Kit.fmt(b) + ' of (y / a) = ' + Kit.fmt(Model.log(b, y / a)) + '.';
    canvas.setAttribute('aria-label', 'Graph of y = ' + a + ' times ' + b + ' to the power x. ' + Kit.get('result').textContent);
  }
  Kit.bind(['start', 'base', 'x'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

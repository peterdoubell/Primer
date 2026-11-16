'use strict';
const Model = {
  mul: ([a, b], [c, d]) => [a * c - b * d, a * d + b * c],
  mod: ([a, b]) => Math.hypot(a, b),
  arg: ([a, b]) => Math.atan2(b, a) * 180 / Math.PI,
  show: ([a, b]) => Number(a.toFixed(3)) + (b < 0 ? ' − ' : ' + ') + Math.abs(Number(b.toFixed(3))) + 'i',
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const z = [Kit.num('zr'), Kit.num('zi')], w = [Kit.num('wr'), Kit.num('wi')], zw = Model.mul(z, w);
    for (const [id, v] of [['zr', z[0]], ['zi', z[1]], ['wr', w[0]], ['wi', w[1]]]) Kit.say(id, v, String(v));
    const span = Math.max(4, Math.ceil(Model.mod(zw)) + 1), p = Kit.plot(canvas, {x: [-span * 1.4, span * 1.4], y: [-span, span], xlabel: 'real', ylabel: 'imaginary'});
    p.arrow(0, 0, z[0], z[1], '#215783'); p.text('z', z[0], z[1], '#215783'); p.arrow(0, 0, w[0], w[1], '#963d18'); p.text('w', w[0], w[1], '#963d18');
    p.arrow(0, 0, zw[0], zw[1], '#172533', 4); p.text('zw', zw[0], zw[1]);
    Kit.rows(Kit.get('rows'), [['z', Model.show(z), Kit.fmt(Model.mod(z)), Kit.fmt(Model.arg(z)) + '°'], ['w', Model.show(w), Kit.fmt(Model.mod(w)), Kit.fmt(Model.arg(w)) + '°'],
      ['z × w', Model.show(zw), Kit.fmt(Model.mod(zw)), Kit.fmt(Model.arg(zw)) + '°']]);
    Kit.get('result').textContent = 'Multiplying complex numbers multiplies their lengths (' + Kit.fmt(Model.mod(z)) + ' × ' + Kit.fmt(Model.mod(w)) + ' = ' + Kit.fmt(Model.mod(zw)) + ') and adds their angles. Multiplying by i turns a number through 90°.';
    canvas.setAttribute('aria-label', 'Complex plane showing z, w and their product. ' + Kit.get('result').textContent);
  }
  Kit.bind(['zr', 'zi', 'wr', 'wi'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

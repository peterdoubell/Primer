'use strict';
const Model = {
  EXACT: {0: ['0', '1', '0'], 30: ['1/2', '√3/2', '√3/3'], 45: ['√2/2', '√2/2', '1'], 60: ['√3/2', '1/2', '√3'], 90: ['1', '0', 'undefined']},
  trig(degrees) {
    const d = ((degrees % 360) + 360) % 360, rad = d * Math.PI / 180;
    const snap = v => Math.abs(v) < 1e-12 ? 0 : v;
    const sin = snap(Math.sin(rad)), cos = snap(Math.cos(rad));
    return {degrees: d, radians: rad, sin, cos, tan: cos === 0 ? null : snap(sin / cos), quadrant: d % 90 === 0 ? 0 : Math.floor(d / 90) + 1};
  },
  reference(degrees) { const d = ((degrees % 360) + 360) % 360; return d <= 90 ? d : d <= 180 ? 180 - d : d <= 270 ? d - 180 : 360 - d; },
  exact(degrees) {
    const t = Model.trig(degrees), ref = Model.EXACT[Model.reference(degrees)];
    if (!ref) return null;
    const sign = (v, s) => s === '0' || s === 'undefined' ? s : (v < 0 ? '−' : '') + s;
    return {sin: sign(t.sin, ref[0]), cos: sign(t.cos, ref[1]), tan: t.tan === null ? 'undefined' : sign(t.tan, ref[2])};
  },
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const t = Model.trig(Kit.num('angle')), exact = Model.exact(t.degrees);
    Kit.say('angle', t.degrees, t.degrees + '° = ' + Kit.fmt(t.radians / Math.PI) + 'π rad');
    const p = Kit.plot(canvas, {x: [-1.9, 1.9], y: [-1.25, 1.25], xlabel: 'x = cos θ', ylabel: 'y = sin θ'});
    p.curve(v => Math.sqrt(1 - v * v), '#6b7780', -1, 1, 2); p.curve(v => -Math.sqrt(1 - v * v), '#6b7780', -1, 1, 2);
    p.line(0, 0, t.cos, t.sin, '#172533', 3);
    p.line(t.cos, 0, t.cos, t.sin, '#963d18', 4); p.line(0, 0, t.cos, 0, '#215783', 4);
    p.point(t.cos, t.sin, '#172533'); p.text('(' + Kit.fmt(t.cos, 3) + ', ' + Kit.fmt(t.sin, 3) + ')', t.cos, t.sin);
    Kit.rows(Kit.get('rows'), [
      ['sin θ (orange height)', Kit.fmt(t.sin), exact ? exact.sin : '—'],
      ['cos θ (blue width)', Kit.fmt(t.cos), exact ? exact.cos : '—'],
      ['tan θ = sin θ / cos θ', t.tan === null ? 'undefined' : Kit.fmt(t.tan), exact ? exact.tan : '—'],
    ]);
    const where = t.quadrant ? 'Quadrant ' + t.quadrant + ': sine is ' + (t.sin > 0 ? 'positive' : 'negative') + ' and cosine is ' + (t.cos > 0 ? 'positive' : 'negative') + '.' : 'The point lies on an axis.';
    Kit.get('result').textContent = where + ' Reference angle ' + Model.reference(t.degrees) + '°. sin²θ + cos²θ = ' + Kit.fmt(t.sin * t.sin + t.cos * t.cos) + '.';
    canvas.setAttribute('aria-label', 'Unit circle with the point at ' + t.degrees + ' degrees. ' + Kit.get('result').textContent);
  }
  Kit.bind(['angle'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

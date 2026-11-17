'use strict';
const Model = {
  // Schwarzschild radius of one solar mass in kilometres: 2GM/c².
  RS_SUN: 2.953,
  radius: solarMasses => Model.RS_SUN * solarMasses,
  // Rate of a clock hovering at r, compared with a clock far away (non-rotating mass).
  rate: ratio => Math.sqrt(1 - 1 / ratio),
  // Seconds lost per day by the hovering clock.
  lostPerDay: ratio => 86400 * (1 - Model.rate(ratio)),
  // Escape speed as a fraction of c.
  escape: ratio => Math.sqrt(1 / ratio),
  // Factor by which light climbing out to infinity is stretched in wavelength.
  redshift: ratio => 1 / Model.rate(ratio),
  scientific(value) { const e = Math.floor(Math.log10(value)); return e > 5 ? (Math.round(value / 10 ** e * 100) / 100) + ' × 10^' + e : String(Math.round(value * 100) / 100); },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const M = 10 ** v.mass, rs = Model.radius(M), p = Kit.plot(canvas, {x: [0, 20], y: [0, 1.1], xlabel: 'distance ÷ Schwarzschild radius', ylabel: 'clock rate'});
  p.line(1, 0, 1, 1.1, '#172533', 2, [5, 5]); p.curve(r => Model.rate(r), '#215783', 1.0001, 20); p.point(v.ratio, Model.rate(v.ratio), '#963d18', 7); p.text('horizon', 1, 1, '#172533', 6, 0);
  return {sum: 'Your clock runs at ' + Kit.fmt(100 * Model.rate(v.ratio), 4) + '% of the far-away rate',
    rows: [['Mass', Model.scientific(M) + ' solar masses'], ['Schwarzschild radius', Model.scientific(rs) + ' km'], ['Your distance from the centre', Model.scientific(rs * v.ratio) + ' km'], ['Clock rate compared with far away', Kit.fmt(Model.rate(v.ratio), 4)], ['Seconds lost each day', Kit.fmt(Model.lostPerDay(v.ratio), 4)], ['Escape speed', Kit.fmt(Model.escape(v.ratio), 3) + ' c'], ['Light sent outward is stretched by', Kit.fmt(Model.redshift(v.ratio), 4) + ' times']],
    result: 'The Schwarzschild radius grows in step with the mass: about 3 km for each solar mass. The clock rate depends only on how many Schwarzschild radii away you hover. At the horizon the rate reaches zero and the escape speed reaches c. These figures are for a non-rotating mass and an observer held in place, not one in orbit or falling in.'};
}
function start() {
  const ids = ["mass", "ratio"];
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

'use strict';
const Model = {
  C: 299792458, H: 6.62607015e-34, EV: 1.602176634e-19,
  wavelength: frequency => Model.C / frequency,
  photon: frequency => Model.H * frequency / Model.EV,
  period: frequency => 1 / frequency,
  // Conventional band edges by wavelength in metres; the boundaries are not sharp.
  BANDS: [[1e-11, 'gamma rays'], [1e-8, 'X-rays'], [3.8e-7, 'ultraviolet'], [7.5e-7, 'visible light'], [1e-3, 'infrared'], [1, 'microwaves'], [Infinity, 'radio waves']],
  band(frequency) { const w = Model.wavelength(frequency); return Model.BANDS.find(([edge]) => w < edge)[1]; },
  scientific(value) { const e = Math.floor(Math.log10(value)); return (Math.round(value / 10 ** e * 100) / 100) + ' × 10^' + e; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const f = 10 ** v.power, w = Model.wavelength(f), p = Kit.plot(canvas, {x: [0, 3], y: [-1.6, 1.6], grid: false});
  p.line(0, 0, 3, 0, '#172533', 1.5); p.curve(x => Math.sin(2 * Math.PI * x), '#b3261e', 0, 3); p.curve(x => 0.45 * Math.sin(2 * Math.PI * x), '#215783', 0, 3, 2);
  p.arrow(0, -1.3, 1, -1.3, '#172533', 2); p.text('one wavelength = ' + Model.scientific(w) + ' m', 0, -1.3, '#172533', 4, -8); p.text('electric field', 0.25, 1, '#b3261e', 8, -12); p.text('magnetic field (at right angles)', 1.25, 0.45, '#215783', 8, -10);
  return {sum: Model.band(f) + ': wavelength ' + Model.scientific(w) + ' m',
    rows: [['Frequency', Model.scientific(f) + ' Hz'], ['Wavelength', Model.scientific(w) + ' m'], ['Period', Model.scientific(Model.period(f)) + ' s'], ['Energy of one photon', Model.scientific(Model.photon(f)) + ' eV'], ['Band', Model.band(f)], ['Speed in a vacuum', '299 792 458 m/s (exact)']],
    result: 'Every electromagnetic wave travels at the same speed in a vacuum, so wavelength × frequency is always c. The electric and magnetic fields oscillate in step, at right angles to each other and to the direction of travel. Band boundaries are conventions, not sharp physical edges.'};
}
function start() {
  const ids = ["power"];
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

'use strict';
const Model = {
  H: 6.62607015e-34, MASS: 9.1093837015e-31, EV: 1.602176634e-19,
  // Energy in electronvolts for a box of the given width in nanometres.
  energy: (n, widthNm) => n * n * Model.H ** 2 / (8 * Model.MASS * (widthNm * 1e-9) ** 2) / Model.EV,
  // Normalised wavefunction on 0 ≤ x ≤ 1 (width taken as 1).
  psi: (n, x) => Math.SQRT2 * Math.sin(n * Math.PI * x),
  density: (n, x) => Model.psi(n, x) ** 2,
  // Probability of finding the electron between fractions a and b of the width.
  probability: (n, a, b) => (b - a) - (Math.sin(2 * n * Math.PI * b) - Math.sin(2 * n * Math.PI * a)) / (2 * n * Math.PI),
  nodes: n => n - 1,
  // Wavelength in nanometres of the photon emitted in a jump between two levels.
  photon: (from, to, widthNm) => 1239.841984 / (Model.energy(from, widthNm) - Model.energy(to, widthNm)),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [0, 1], y: [-1.6, 2.2], xlabel: 'position ÷ width'});
  p.curve(x => Model.density(v.n, x), '#963d18'); p.curve(x => Model.psi(v.n, x), '#215783', 0, 1, 2);
  p.text('probability density', 0.02, 2.05, '#963d18', 0, 0); p.text('wavefunction', 0.02, -1.45, '#215783', 0, 0);
  return {sum: 'E' + v.n + ' = ' + Kit.fmt(Model.energy(v.n, v.width)) + ' eV',
    rows: [1, 2, 3, 4, 5, 6].map(n => [(n === v.n ? '→ ' : '') + n, Kit.fmt(Model.energy(n, v.width)), String(Model.nodes(n))]),
    result: 'The energy grows as n² and shrinks as the box widens: squeezing the electron costs energy. The chance of finding it in the middle third is ' + Kit.fmt(100 * Model.probability(v.n, 1 / 3, 2 / 3), 3) + '%. ' + (v.n > 1 ? 'Dropping to the level below would emit a photon of wavelength ' + Kit.fmt(Model.photon(v.n, v.n - 1, v.width), 4) + ' nm.' : 'Even the lowest level has energy above zero: the electron can never be at rest.')};
}
function start() {
  const ids = ["n", "width"];
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

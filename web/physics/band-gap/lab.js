'use strict';
const Model = {
  // Band gaps near room temperature, in electronvolts.
  GAPS: {si: 1.12, ge: 0.67, gaas: 1.42, diamond: 5.47},
  NAMES: {si: 'Silicon', ge: 'Germanium', gaas: 'Gallium arsenide', diamond: 'Diamond'},
  K: 8.617333262e-5,
  // Boltzmann factor that governs the intrinsic carrier density: exp(−Eg / 2kT).
  factor: (gap, temperature) => Math.exp(-gap / (2 * Model.K * temperature)),
  // How many times the factor grows between two temperatures.
  growth: (gap, t1, t2) => Model.factor(gap, t2) / Model.factor(gap, t1),
  // Photons with a longer wavelength than this cannot lift an electron across the gap (nm).
  cutoff: gap => 1239.841984 / gap,
  light(gap) { const w = Model.cutoff(gap); return w < 380 ? 'ultraviolet' : w < 750 ? 'visible' : 'infrared'; },
  thermal: temperature => Model.K * temperature,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const gap = Model.GAPS[v.material], p = Kit.plot(canvas, {x: [200, 600], y: [-70, 0], xlabel: 'temperature (K)', ylabel: 'log₁₀ of the Boltzmann factor'});
  const colours = {si: '#215783', ge: '#3c7a4b', gaas: '#963d18', diamond: '#6b3fa0'};
  Object.keys(Model.GAPS).forEach((name, i) => { const at = 250 + i * 85; p.curve(T => Math.log10(Model.factor(Model.GAPS[name], T)), colours[name], 200, 600, name === v.material ? 4 : 1.5); p.text(Model.NAMES[name], at, Math.log10(Model.factor(Model.GAPS[name], at)), colours[name], 4, 18); });
  p.point(v.temperature, Math.log10(Model.factor(gap, v.temperature)), '#172533', 6);
  return {sum: Model.NAMES[v.material] + ': factor 10^' + Kit.fmt(Math.log10(Model.factor(gap, v.temperature)), 3).replace('-', '−') + ' at ' + v.temperature + ' K',
    rows: Object.keys(Model.GAPS).map(name => [(name === v.material ? '→ ' : '') + Model.NAMES[name], String(Model.GAPS[name]), Kit.fmt(Model.cutoff(Model.GAPS[name]), 4) + ' (' + Model.light(Model.GAPS[name]) + ')']),
    result: 'Thermal energy kT at ' + v.temperature + ' K is only ' + Kit.fmt(Model.thermal(v.temperature), 3) + ' eV, far below the gap, so very few electrons are free. But the number rises steeply: warming ' + Model.NAMES[v.material].toLowerCase() + ' from 300 K to 400 K multiplies the factor by about ' + Kit.fmt(Model.growth(gap, 300, 400), 3) + '. Diamond’s wide gap makes it an insulator. Doping, not heat, is what makes chips work.'};
}
function start() {
  const ids = ["material", "temperature"];
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

'use strict';
const Model = {
  // ħc in MeV·fm.
  HBARC: 197.3269804,
  // Rest energies in MeV.
  MASSES: {pion: 139.57, w: 80377, z: 91187.6, photon: 0},
  NAMES: {pion: 'Pion', w: 'W boson', z: 'Z boson', photon: 'Photon'},
  // Range ħ/(mc) in femtometres; unlimited for a massless carrier.
  range: name => Model.MASSES[name] ? Model.HBARC / Model.MASSES[name] : Infinity,
  // Yukawa potential relative to a Coulomb-like 1/r potential at the same distance.
  suppression: (name, r) => Model.MASSES[name] ? Math.exp(-r / Model.range(name)) : 1,
  // Shape of the potential, e^(−r/range)/r, in arbitrary units.
  potential: (name, r) => Model.suppression(name, r) / r,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const range = Model.range(v.carrier), p = Kit.plot(canvas, {x: [0, 5], y: [0, 6], xlabel: 'distance (fm)', ylabel: 'strength of the potential (arbitrary units)'}), f = n => Number.isFinite(n) ? Kit.fmt(n, 3) : 'unlimited';
  p.curve(r => 1 / r, '#9aa6ae', 0.1, 5, 1.5); p.curve(r => Model.potential(v.carrier, r), '#215783', 0.1, 5); p.point(v.r, Model.potential(v.carrier, v.r), '#963d18', 6); p.text('1/r (massless carrier)', 2.6, 0.5, '#7a8790', 0, -10);
  return {sum: Model.NAMES[v.carrier] + ': range ' + (Number.isFinite(range) ? Kit.fmt(range, 3) + ' fm' : 'unlimited'),
    rows: Object.keys(Model.MASSES).map(name => [(name === v.carrier ? '→ ' : '') + Model.NAMES[name], String(Model.MASSES[name]), f(Model.range(name))]),
    result: Number.isFinite(range) ? 'At ' + v.r + ' fm the potential is cut to ' + Kit.fmt(100 * Model.suppression(v.carrier, v.r), 3) + '% of what a massless carrier would give. The range is ħ ÷ (mass × c): about the size of a nucleus for the pion, and a thousand times smaller than a proton for the W and Z, which is why the weak force seems weak.' : 'The photon has no mass, so electromagnetism has unlimited range and its potential falls only as 1/r. (The gluon is also massless, but the strong force is short-ranged for a different reason: confinement.)'};
}
function start() {
  const ids = ["carrier", "r"];
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

'use strict';
const Model = {
  // Electric charge in thirds of the elementary charge, so the sums are exact.
  QUARKS: {u: 2, d: -1, s: -1, c: 2, b: -1, t: 2},
  HADRONS: {proton: ['u', 'u', 'd'], neutron: ['u', 'd', 'd'], piplus: ['u', 'anti-d'], piminus: ['d', 'anti-u'], kplus: ['u', 'anti-s'], lambda: ['u', 'd', 's'], omega: ['s', 's', 's'], deltapp: ['u', 'u', 'u']},
  thirds: quark => quark.startsWith('anti-') ? -Model.QUARKS[quark.slice(5)] : Model.QUARKS[quark],
  // Charge in units of e.
  charge: name => Model.HADRONS[name].reduce((sum, quark) => sum + Model.thirds(quark), 0) / 3,
  kind: name => Model.HADRONS[name].length === 3 ? 'baryon (three quarks)' : 'meson (a quark and an antiquark)',
  // Baryon number: +1/3 for each quark, −1/3 for each antiquark.
  baryonNumber: name => Model.HADRONS[name].reduce((sum, quark) => sum + (quark.startsWith('anti-') ? -1 : 1), 0) / 3,
  PARTICLES: [['up quark', 'quark', '+2/3', '1/2'], ['down quark', 'quark', '−1/3', '1/2'], ['charm quark', 'quark', '+2/3', '1/2'], ['strange quark', 'quark', '−1/3', '1/2'], ['top quark', 'quark', '+2/3', '1/2'], ['bottom quark', 'quark', '−1/3', '1/2'],
    ['electron', 'lepton', '−1', '1/2'], ['muon', 'lepton', '−1', '1/2'], ['tau', 'lepton', '−1', '1/2'], ['electron neutrino', 'lepton', '0', '1/2'], ['muon neutrino', 'lepton', '0', '1/2'], ['tau neutrino', 'lepton', '0', '1/2'],
    ['photon', 'force carrier', '0', '1'], ['gluon', 'force carrier', '0', '1'], ['W boson', 'force carrier', '±1', '1'], ['Z boson', 'force carrier', '0', '1'], ['Higgs boson', 'scalar', '0', '0']],
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const quarks = Model.HADRONS[v.hadron], q = Model.charge(v.hadron), p = Kit.plot(canvas, {x: [0, 4.6], y: [-1.2, 1.2], grid: false}), third = n => n === 2 ? '+2/3' : n === -2 ? '−2/3' : n === 1 ? '+1/3' : '−1/3';
  p.line(0.3, 0, 4.3, 0, '#172533', 1.5);
  quarks.forEach((quark, i) => { const t = Model.thirds(quark); p.line(1 + i * 1.1, 0, 1 + i * 1.1, t / 3, t > 0 ? '#b3261e' : '#215783', 60); p.text(quark + ' ' + third(t), 1 + i * 1.1, t / 3, '#172533', -26, t > 0 ? -10 : 22); });
  return {sum: quarks.join(' + ') + '  →  charge ' + (q > 0 ? '+' : q < 0 ? '−' : '') + Math.abs(q),
    rows: Model.PARTICLES,
    result: 'This particle is a ' + Model.kind(v.hadron) + ' with baryon number ' + Model.baryonNumber(v.hadron) + '. Quark charges come in thirds, yet every particle seen on its own has a whole-number charge, because quarks are never found alone. The table lists the 17 kinds of particle in the Standard Model.'};
}
function start() {
  const ids = ["hadron"];
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

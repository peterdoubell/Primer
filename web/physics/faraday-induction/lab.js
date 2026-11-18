'use strict';
const Model = {
  // Flux through one turn in webers, with the area given in cm².
  flux: (field, areaCm2) => field * areaCm2 * 1e-4,
  // Average emf in volts. The minus sign is Lenz’s law: the induced current opposes the change.
  emf: (turns, areaCm2, b1, b2, dt) => -turns * (Model.flux(b2, areaCm2) - Model.flux(b1, areaCm2)) / dt,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const e = Model.emf(v.turns, v.area, v.b1, v.b2, v.dt), p = Kit.plot(canvas, {x: [-0.5, 3], y: [-1.2, 1.2], xlabel: 'time (s)', ylabel: 'field (T)'}), m = n => Kit.fmt(n, 3).replace('-', '−');
  p.line(-0.5, v.b1, 0, v.b1, '#215783', 3); p.line(0, v.b1, v.dt, v.b2, '#963d18', 3); p.line(v.dt, v.b2, 3, v.b2, '#215783', 3);
  return {sum: 'Induced voltage ' + m(e) + ' V while the field changes',
    rows: [['Flux through one turn at the start', m(Model.flux(v.b1, v.area) * 1000) + ' mWb'], ['Flux through one turn at the end', m(Model.flux(v.b2, v.area) * 1000) + ' mWb'], ['Rate of change of field', m((v.b2 - v.b1) / v.dt) + ' T/s'], ['Induced voltage (average)', m(e) + ' V'], ['Before and after the change', '0 V']],
    result: v.b1 === v.b2 ? 'The field does not change, so no voltage is induced however strong it is.' : 'The voltage is the number of turns times the rate of change of flux. Making the change faster, the coil larger or the turns more numerous all raise it. The minus sign is Lenz’s law: the induced current makes a field that opposes the change. This is how generators and transformers work.'};
}
function start() {
  const ids = ["turns", "area", "b1", "b2", "dt"];
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

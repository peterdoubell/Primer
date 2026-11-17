'use strict';
const Model = {
  // One kilogram of water substance, starting as ice at −20 °C. Specific heats in kJ/(kg·K), latent heats in kJ/kg.
  ICE: 2.1, WATER: 4.18, STEAM: 2.0, FUSION: 334, VAPORISATION: 2260, START: -20,
  stages() { const a = Model.ICE * 20, b = a + Model.FUSION, c = b + Model.WATER * 100, d = c + Model.VAPORISATION; return [a, b, c, d]; },
  state(heat) {
    const [a, b, c, d] = Model.stages();
    if (heat < a) return {temperature: Model.START + heat / Model.ICE, phase: 'solid (ice)'};
    if (heat < b) return {temperature: 0, phase: 'melting: ice and water together', melted: (heat - a) / Model.FUSION};
    if (heat < c) return {temperature: (heat - b) / Model.WATER, phase: 'liquid (water)'};
    if (heat < d) return {temperature: 100, phase: 'boiling: water and steam together', boiled: (heat - c) / Model.VAPORISATION};
    return {temperature: 100 + (heat - d) / Model.STEAM, phase: 'gas (steam)'};
  },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const s = Model.state(v.heat), [a, b, c, d] = Model.stages(), p = Kit.plot(canvas, {x: [0, 3200], y: [-30, 180], xlabel: 'heat added (kJ)', ylabel: 'temperature (°C)'});
  p.curve(q => Model.state(q).temperature, '#215783'); p.point(v.heat, s.temperature, '#963d18', 7);
  const f = n => Kit.fmt(n, 4);
  return {sum: Kit.fmt(s.temperature, 3).replace('-', '−') + ' °C — ' + s.phase,
    rows: [['Warm the ice from −20 °C to 0 °C', f(a), 'rises'], ['Melt the ice', f(Model.FUSION), 'stays at 0 °C'], ['Warm the water from 0 °C to 100 °C', f(c - b), 'rises'], ['Boil the water', f(Model.VAPORISATION), 'stays at 100 °C'], ['Warm the steam', '2 for each degree', 'rises']],
    result: (s.melted !== undefined ? Kit.fmt(100 * s.melted, 3) + '% of the ice has melted. ' : s.boiled !== undefined ? Kit.fmt(100 * s.boiled, 3) + '% of the water has boiled. ' : '') + 'On the flat parts the heat is not raising the temperature: it is pulling the particles apart to change the state. Boiling takes nearly seven times as much heat as melting. Normal atmospheric pressure is assumed.'};
}
function start() {
  const ids = ["heat"];
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

'use strict';
const Model = {
  // Carnot limit; meaningful only when hot > cold.
  limit: (hot, cold) => hot > cold ? 1 - cold / hot : 0,
  flows(heat, efficiency) { const work = heat * efficiency; return {work, waste: heat - work}; },
  // Total entropy change of the two reservoirs for one cycle (J/K). It cannot be negative.
  entropy: (hot, cold, heat, efficiency) => -heat / hot + heat * (1 - efficiency) / cold,
  possible: (hot, cold, efficiency) => efficiency <= Model.limit(hot, cold) + 1e-12,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const limit = Model.limit(v.hot, v.cold), eff = v.real / 100, ideal = Model.flows(v.heat, limit), mine = Model.flows(v.heat, eff), ok = Model.possible(v.hot, v.cold, eff), p = Kit.plot(canvas, {x: [0, 7], y: [0, 2200], grid: false, ylabel: 'joules'}), f = n => Kit.fmt(n, 4).replace('-', '−');
  [['heat in', v.heat, '#b3261e'], ['ideal work', ideal.work, '#3c7a4b'], ['ideal waste', ideal.waste, '#215783'], ['this work', mine.work, ok ? '#3c7a4b' : '#9aa6ae'], ['this waste', mine.waste, ok ? '#215783' : '#9aa6ae']].forEach(([name, value, colour], i) => { p.line(1 + i * 1.25, 0, 1 + i * 1.25, value, colour, 60); p.text(name, 1 + i * 1.25, value, '#172533', -30, -10); });
  p.line(0.4, 0, 6.6, 0, '#172533', 2);
  const dS = Model.entropy(v.hot, v.cold, v.heat, eff);
  return {sum: 'Carnot limit ' + f(100 * limit) + '%',
    rows: [['Efficiency', f(100 * limit) + '%', v.real + '%'], ['Work out (J)', f(ideal.work), f(mine.work)], ['Waste heat (J)', f(ideal.waste), f(mine.waste)], ['Entropy change of the surroundings (J/K)', '0', f(dS)]],
    result: v.hot <= v.cold ? 'With no temperature difference no engine can produce work.' : ok ? 'This engine is allowed: its entropy change is ' + (Math.abs(dS) < 1e-9 ? 'zero, the ideal reversible case.' : 'positive, as the second law requires.') + ' Waste heat is unavoidable; only a colder sink or a hotter source raises the limit.' : 'This engine is impossible. It would beat the Carnot limit and lower the total entropy by ' + f(-dS) + ' J/K, which the second law forbids.'};
}
function start() {
  const ids = ["hot", "cold", "heat", "real"];
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

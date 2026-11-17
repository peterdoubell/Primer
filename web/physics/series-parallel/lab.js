'use strict';
const Model = {
  circuit(kind, volts, r1, r2) {
    if (kind === 'series') { const total = r1 + r2, current = volts / total; return {total, current, bulbs: [{volts: current * r1, current, power: current * current * r1}, {volts: current * r2, current, power: current * current * r2}], power: volts * current}; }
    const total = r1 * r2 / (r1 + r2), bulbs = [r1, r2].map(r => ({volts, current: volts / r, power: volts * volts / r}));
    return {total, current: volts / total, bulbs, power: volts * volts / total};
  },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const c = Model.circuit(v.kind, v.volts, v.r1, v.r2), top = Math.max(c.bulbs[0].power, c.bulbs[1].power), p = Kit.plot(canvas, {x: [0, 4], y: [0, top * 1.3], grid: false});
  c.bulbs.forEach((b, i) => { p.line(1.2 + i * 1.6, 0, 1.2 + i * 1.6, b.power, '#d99a00', 80); p.text('bulb ' + (i + 1) + ': ' + Kit.fmt(b.power, 3) + ' W', 1.2 + i * 1.6, b.power, '#172533', -44, -10); }); p.line(0.3, 0, 3.7, 0, '#172533', 2);
  const f = n => Kit.fmt(n, 3);
  return {sum: 'Battery current ' + f(c.current) + ' A',
    rows: [['Voltage (V)', f(c.bulbs[0].volts), f(c.bulbs[1].volts), f(v.volts)], ['Current (A)', f(c.bulbs[0].current), f(c.bulbs[1].current), f(c.current)], ['Resistance (Ω)', String(v.r1), String(v.r2), f(c.total)], ['Power (W)', f(c.bulbs[0].power), f(c.bulbs[1].power), f(c.power)]],
    result: v.kind === 'series' ? 'In series the same current passes through both bulbs and they share the battery voltage. The bulb with more resistance takes the larger share and is brighter. Remove one and both go out.' : 'In parallel each bulb gets the full battery voltage and its own current. The bulb with less resistance draws more current and is brighter. Remove one and the other stays lit.'};
}
function start() {
  const ids = ["kind", "volts", "r1", "r2"];
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

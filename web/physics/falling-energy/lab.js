'use strict';
const Model = {
  G: 9.8,
  // Air resistance is ignored.
  energy(mass, height, percent) {
    const y = height * (1 - percent / 100), stored = mass * Model.G * y, total = mass * Model.G * height, moving = total - stored;
    return {y, stored, moving, total, speed: Math.sqrt(2 * moving / mass)};
  },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const e = Model.energy(v.mass, v.height, v.fallen), p = Kit.plot(canvas, {x: [0, 6], y: [0, e.total * 1.2], grid: false});
  [['stored (height)', e.stored, '#215783'], ['motion', e.moving, '#963d18'], ['total', e.total, '#3c7a4b']].forEach(([name, value, colour], i) => { p.line(1.2 + i * 1.6, 0, 1.2 + i * 1.6, value, colour, 70); p.text(name, 1.2 + i * 1.6, e.total * 1.08, '#172533', -40, 0); });
  p.line(0.4, 0, 5.4, 0, '#172533', 2);
  return {sum: 'Height ' + Kit.fmt(e.y, 3) + ' m, speed ' + Kit.fmt(e.speed, 3) + ' m/s',
    rows: [['Stored energy (gravitational)', Kit.fmt(e.stored)], ['Energy of motion (kinetic)', Kit.fmt(e.moving)], ['Total', Kit.fmt(e.total)], ['Speed (m/s)', Kit.fmt(e.speed, 3)]],
    result: 'Energy is not used up: every joule lost from the stored energy appears as energy of motion. When the ball lands, that energy becomes sound and a little heat. Air resistance is ignored here.'};
}
function start() {
  const ids = ["mass", "height", "fallen"];
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

'use strict';
const Model = {
  DENSITY: 1000,
  // Continuity for an incompressible fluid: A1 v1 = A2 v2.
  speed: (a1, a2, v1) => v1 * a1 / a2,
  // Volume per second in litres per second, with area in cm² and speed in m/s.
  flow: (areaCm2, speed) => areaCm2 * 1e-4 * speed * 1000,
  // Bernoulli for a level pipe with no friction: pressure drop in pascals from section 1 to section 2.
  drop: (a1, a2, v1) => Model.DENSITY * (Model.speed(a1, a2, v1) ** 2 - v1 ** 2) / 2,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const v2 = Model.speed(v.a1, v.a2, v.v1), drop = Model.drop(v.a1, v.a2, v.v1), p = Kit.plot(canvas, {x: [0, 10], y: [-4, 4], grid: false}), h1 = Math.sqrt(v.a1) / 2.2, h2 = Math.sqrt(v.a2) / 2.2, f = n => Kit.fmt(n, 3).replace('-', '−');
  for (const s of [1, -1]) { p.line(0, s * h1, 3.5, s * h1, '#172533', 3); p.line(3.5, s * h1, 5.5, s * h2, '#172533', 3); p.line(5.5, s * h2, 10, s * h2, '#172533', 3); }
  p.arrow(0.6, 0, 0.6 + Math.min(v.v1 * 0.5, 2.6), 0, '#215783', 4); p.arrow(6, 0, 6 + Math.min(v2 * 0.5, 3.8), 0, '#963d18', 4);
  return {sum: 'Speed in the narrow section ' + f(v2) + ' m/s',
    rows: [['Area (cm²)', String(v.a1), String(v.a2)], ['Speed (m/s)', f(v.v1), f(v2)], ['Flow (litres per second)', f(Model.flow(v.a1, v.v1)), f(Model.flow(v.a2, v2))], ['Pressure compared with the wide section (kPa)', '0', f(-drop / 1000)]],
    result: v.a2 === v.a1 ? 'The pipe does not change width, so the speed and pressure stay the same.' : v.a2 < v.a1 ? 'The same volume passes every second, so a smaller area needs a higher speed. The water gains kinetic energy, and its pressure falls to pay for it (Bernoulli). Friction and height changes are ignored.' : 'The pipe widens, so the water slows down and its pressure rises.'};
}
function start() {
  const ids = ["a1", "a2", "v1"];
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

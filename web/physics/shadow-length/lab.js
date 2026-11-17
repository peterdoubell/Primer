'use strict';
const Model = {
  // Similar triangles: shadow / object = (distance + shadow) / lamp. No finite shadow unless the lamp is higher than the object.
  shadow: (lamp, object, distance) => lamp > object ? object * distance / (lamp - object) : Infinity,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const s = Model.shadow(v.lamp, v.object, v.distance), p = Kit.plot(canvas, {x: [-1, 17], y: [-1, 11], grid: false}), end = Number.isFinite(s) ? v.distance + s : 17;
  p.line(-1, 0, 17, 0, '#172533', 2); p.line(0, 0, 0, v.lamp, '#9aa6ae', 3); p.point(0, v.lamp, '#d99a00', 11); p.line(v.distance, 0, v.distance, v.object, '#215783', 10);
  if (Number.isFinite(s)) { p.line(0, v.lamp, end, 0, '#d99a00', 1.5, [6, 5]); p.line(v.distance, 0, Math.min(end, 17), 0, '#172533', 9); }
  return {sum: Number.isFinite(s) ? 'Shadow length ' + Kit.fmt(s, 3) : 'The shadow never ends',
    rows: [['Shadow length', Number.isFinite(s) ? Kit.fmt(s, 3) : 'endless'], ['Lamp higher than the object?', v.lamp > v.object ? 'yes' : 'no'], ['Shadow compared with the object', Number.isFinite(s) ? Kit.fmt(s / v.object, 3) + ' times as long' : '—']],
    result: Number.isFinite(s) ? 'The ray that just clears the top of the object marks the end of the shadow. A lower lamp or an object further away makes a longer shadow, like the sun late in the day.' : 'The lamp is not higher than the object, so the ray over the top never comes down to the ground.'};
}
function start() {
  const ids = ["lamp", "object", "distance"];
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

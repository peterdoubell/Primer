'use strict';
const Model = {
  RATE: 0.15,
  // Two equal objects in contact: each approaches the average.
  temps(a, b, minutes) { const mid = (a + b) / 2, k = Math.exp(-Model.RATE * minutes); return [mid + (a - mid) * k, mid + (b - mid) * k]; },
  final: (a, b) => (a + b) / 2,
  direction: (a, b) => a > b ? 'first to second' : a < b ? 'second to first' : 'none',
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const [x, y] = Model.temps(v.a, v.b, v.t), p = Kit.plot(canvas, {x: [0, 4], y: [0, 110], grid: false}), warm = n => n >= Model.final(v.a, v.b) ? '#b3261e' : '#215783';
  p.line(1.2, 0, 1.2, x, warm(v.a), 90); p.line(2.8, 0, 2.8, y, warm(v.b), 90); p.text(Kit.fmt(x, 3) + ' °C', 1.2, x, '#172533', -24, -10); p.text(Kit.fmt(y, 3) + ' °C', 2.8, y, '#172533', -24, -10); p.line(0.3, 0, 3.7, 0, '#172533', 2);
  if (v.a !== v.b) { const up = v.a > v.b; p.arrow(up ? 1.7 : 2.3, 55, up ? 2.3 : 1.7, 55, '#172533', 3); p.text('heat', 1.85, 55, '#172533', 0, -12); }
  return {sum: Kit.fmt(x, 3) + ' °C and ' + Kit.fmt(y, 3) + ' °C',
    rows: [['Which way does heat flow?', Model.direction(v.a, v.b)], ['First thing now', Kit.fmt(x, 3) + ' °C'], ['Second thing now', Kit.fmt(y, 3) + ' °C'], ['Where they will end up', Kit.fmt(Model.final(v.a, v.b), 3) + ' °C']],
    result: v.a === v.b ? 'They are already the same temperature, so no heat flows.' : 'Heat always flows from warm to cool, never the other way by itself. The warm thing cools and the cool thing warms until they match. (Two things of the same size and material are assumed.)'};
}
function start() {
  const ids = ["a", "b", "t"];
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

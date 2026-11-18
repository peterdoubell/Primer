'use strict';
const Model = {
  product: (a, b) => a * b,
  table: a => Array.from({length: 12}, (_, i) => [a + ' × ' + (i + 1), a * (i + 1)]),
  // The product as repeated addition.
  repeated: (a, b) => Array(a).fill(b).join(' + '),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [0, 13], y: [0, 13], grid: false});
  for (let row = 1; row <= v.a; row++) for (let col = 1; col <= v.b; col++) p.point(col, 13 - row, '#215783', 8);
  return {sum: v.a + ' × ' + v.b + ' = ' + Model.product(v.a, v.b),
    rows: Model.table(v.a).map(([fact, answer]) => [fact, String(answer)]),
    result: v.a + ' rows of ' + v.b + ' is ' + Model.repeated(v.a, v.b) + ' = ' + Model.product(v.a, v.b) + '. Turn the array on its side and it is ' + v.b + ' rows of ' + v.a + ': the same ' + Model.product(v.a, v.b) + '.'};
}
function start() {
  const ids = ["a", "b"];
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

'use strict';
const Model = {
  sign: (a, b) => a > b ? '>' : a < b ? '<' : '=',
  words: (a, b) => a > b ? a + ' is bigger than ' + b : a < b ? a + ' is smaller than ' + b : a + ' is the same as ' + b,
  difference: (a, b) => Math.abs(a - b),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [0, 21.5], y: [0.3, 2.7], grid: false});
  for (let i = 1; i <= v.a; i++) p.point(i, 2, '#215783', 9);
  for (let i = 1; i <= v.b; i++) p.point(i, 1, '#963d18', 9);
  p.text(String(v.a), Math.max(v.a, 0.2), 2, '#215783', 14, 6); p.text(String(v.b), Math.max(v.b, 0.2), 1, '#963d18', 14, 6);
  return {sum: v.a + ' ' + Model.sign(v.a, v.b) + ' ' + v.b,
    rows: [['Which is bigger?', v.a === v.b ? 'neither' : String(Math.max(v.a, v.b))], ['Which is smaller?', v.a === v.b ? 'neither' : String(Math.min(v.a, v.b))], ['How many more?', String(Model.difference(v.a, v.b))]],
    result: Model.words(v.a, v.b) + '. The open end of the sign always faces the bigger number.'};
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

'use strict';
const Model = {
  forward: n => Array.from({length: n}, (_, i) => i + 1),
  back: n => Array.from({length: n}, (_, i) => n - i),
  WORDS: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'],
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [0, 11], y: [0, 2], grid: false});
  for (let i = 1; i <= 10; i++) { p.point(i, 1, i <= v.n ? '#215783' : '#c3ccd2', 14, i > v.n); if (i <= v.n) p.text(String(i), i, 1, '#172533', -5, 40); }
  return {sum: v.n + ' — ' + Model.WORDS[v.n],
    rows: [['Counting up', Model.forward(v.n).join(', ') || 'nothing to count'], ['Counting back', Model.back(v.n).join(', ') || 'nothing to count'], ['One more', v.n < 10 ? String(v.n + 1) : '11'], ['One fewer', v.n > 0 ? String(v.n - 1) : 'none left to take']],
    result: 'The last number you say tells you how many there are: ' + Model.WORDS[v.n] + '.'};
}
function start() {
  const ids = ["n"];
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

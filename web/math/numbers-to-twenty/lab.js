'use strict';
const Model = {
  WORDS: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty'],
  split: n => ({tens: Math.floor(n / 10), ones: n % 10}),
  before: n => n - 1, after: n => n + 1,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [0, 12.5], y: [0, 3], grid: false});
  for (let i = 0; i < 20; i++) { const frame = Math.floor(i / 10), k = i % 10, x = 1 + (k % 5) + frame * 6, y = 2 - Math.floor(k / 5); p.point(x, y, i < v.n ? (frame ? '#963d18' : '#215783') : '#c3ccd2', 13, i >= v.n); }
  const s = Model.split(v.n);
  return {sum: v.n + ' — ' + Model.WORDS[v.n],
    rows: [['Tens', String(s.tens)], ['Ones', String(s.ones)], ['Number before', String(Model.before(v.n))], ['Number after', String(Model.after(v.n))]],
    result: v.n + ' is ' + s.tens + (s.tens === 1 ? ' ten' : ' tens') + ' and ' + s.ones + (s.ones === 1 ? ' one' : ' ones') + '. It comes after ' + Model.before(v.n) + ' and before ' + Model.after(v.n) + '.'};
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

'use strict';
const Model = {
  NAMES: {2: ['half', 'halves'], 3: ['third', 'thirds'], 4: ['quarter', 'quarters'], 8: ['eighth', 'eighths']},
  COUNT: ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'],
  gcd: (a, b) => b ? Model.gcd(b, a % b) : a,
  // [numerator, denominator] in lowest terms.
  simplest(n, d) { const g = Model.gcd(n, d) || 1; return [n / g, d / g]; },
  name(n, d) { if (n === d) return 'one whole'; if (n === 0) return 'nothing'; return Model.COUNT[n] + ' ' + Model.NAMES[d][n === 1 ? 0 : 1]; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const d = Number(v.parts), n = Math.min(v.shaded, d), p = Kit.plot(canvas, {x: [-0.2, 8.2], y: [0, 3], grid: false}), w = 8 / d, [sn, sd] = Model.simplest(n, d);
  for (let i = 0; i < d; i++) { if (i < n) for (let k = 0; k <= 30; k++) p.line(i * w + 0.03, 1 + k / 20, (i + 1) * w - 0.03, 1 + k / 20, '#8fb6d6', 6); p.line(i * w, 1, i * w, 2.5, '#172533', 2); }
  p.line(8, 1, 8, 2.5, '#172533', 2); p.line(0, 1, 8, 1, '#172533', 2); p.line(0, 2.5, 8, 2.5, '#172533', 2);
  return {sum: n + '/' + d + ' — ' + Model.name(n, d),
    rows: [['Equal parts in the whole', String(d)], ['Parts shaded', String(n)], ['Parts not shaded', String(d - n)], ['The same amount, written most simply', n === d ? '1' : n === 0 ? '0' : sn + '/' + sd]],
    result: n === d ? 'All ' + d + ' parts are shaded, so that is one whole.' : 'The parts must be equal. ' + (sd !== d && n ? n + '/' + d + ' is the same amount as ' + sn + '/' + sd + '.' : 'Here ' + n + ' of ' + d + ' equal parts are shaded.')};
}
function start() {
  const ids = ["parts", "shaded"];
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

'use strict';
const Model = {
  gcd: (a, b) => b ? Model.gcd(b, a % b) : a,
  fraction(p) { const g = Model.gcd(p, 100) || 1; return [p / g, 100 / g]; },
  decimal: p => p / 100,
  of: (p, whole) => Math.round(p * whole) / 100,
  increase: (p, whole) => Math.round((100 + p) * whole) / 100,
  decrease: (p, whole) => Math.round((100 - p) * whole) / 100,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const g = Kit.plot(canvas, {x: [-0.5, 10.5], y: [-0.5, 10.5], grid: false}), [n, d] = Model.fraction(v.p);
  for (let i = 0; i < 100; i++) { const x = i % 10, y = 9 - Math.floor(i / 10); if (i < v.p) for (let k = 1; k < 10; k++) g.line(x + 0.06, y + k / 10, x + 0.94, y + k / 10, '#8fb6d6', 4); }
  for (let i = 0; i <= 10; i++) { g.line(i, 0, i, 10, '#172533', 1); g.line(0, i, 10, i, '#172533', 1); }
  return {sum: v.p + '% of ' + v.whole + ' = ' + Kit.fmt(Model.of(v.p, v.whole), 6),
    rows: [['Percent', v.p + '%'], ['Fraction in lowest terms', d === 1 ? String(n) : n + '/' + d], ['Decimal', String(Model.decimal(v.p))], [v.p + '% of ' + v.whole, Kit.fmt(Model.of(v.p, v.whole), 6)],
      [v.whole + ' increased by ' + v.p + '%', Kit.fmt(Model.increase(v.p, v.whole), 6)], [v.whole + ' decreased by ' + v.p + '%', Kit.fmt(Model.decrease(v.p, v.whole), 6)]],
    result: 'To find ' + v.p + '% of an amount, multiply it by ' + Model.decimal(v.p) + '. An increase of ' + v.p + '% followed by a decrease of ' + v.p + '% does not return to the start, because the second percent is taken of a different amount.'};
}
function start() {
  const ids = ["p", "whole"];
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

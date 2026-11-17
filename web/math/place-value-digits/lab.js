'use strict';
const Model = {
  PLACES: ['thousands', 'hundreds', 'tens', 'ones'],
  digits: n => Model.PLACES.map((place, i) => { const unit = 10 ** (3 - i), digit = Math.floor(n / unit) % 10; return {place, digit, value: digit * unit}; }),
  expanded(n) { const parts = Model.digits(n).filter(d => d.value).map(d => d.value); return parts.length ? parts.join(' + ') : '0'; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const digits = Model.digits(v.n), p = Kit.plot(canvas, {x: [0, 5], y: [-1.5, 10], grid: false}), colours = ['#6b3fa0', '#963d18', '#3c7a4b', '#215783'];
  digits.forEach((d, i) => { for (let k = 0; k < d.digit; k++) p.point(i + 1, k + 1, colours[i], 8); p.text(d.place, i + 1, 0, '#172533', -30, 22); p.text(String(d.digit), i + 1, 0, colours[i], -5, 44); });
  p.line(0.4, 0.3, 4.6, 0.3, '#172533', 2);
  return {sum: String(v.n) + ' = ' + Model.expanded(v.n),
    rows: digits.map(d => [d.place, String(d.digit), String(d.value)]),
    result: 'Each place is worth ten times the place to its right. ' + (digits.some(d => d.digit === 0) && v.n > 9 ? 'A zero holds a place open so the other digits keep their value.' : 'Ten ones make one ten, ten tens make one hundred.')};
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

'use strict';
const Model = {
  gcd: (a, b) => b ? Model.gcd(b, a % b) : a,
  simplify(a, b) { const g = Model.gcd(a, b); return [a / g, b / g]; },
  share(total, a, b) { const part = total / (a + b); return {part, first: part * a, second: part * b}; },
  scale: (a, b, k) => [a * k, b * k],
  // The second quantity that keeps the ratio when the first is x.
  proportion: (a, b, x) => x * b / a,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const s = Model.share(v.total, v.a, v.b), [sa, sb] = Model.simplify(v.a, v.b), p = Kit.plot(canvas, {x: [-0.2, v.a + v.b + 0.2], y: [0, 3], grid: false});
  for (let i = 0; i < v.a + v.b; i++) { for (let k = 0; k <= 24; k++) p.line(i + 0.04, 1 + k / 20, i + 0.96, 1 + k / 20, i < v.a ? '#8fb6d6' : '#e3b89c', 5); p.line(i, 1, i, 2.2, '#172533', 1.5); }
  p.line(v.a + v.b, 1, v.a + v.b, 2.2, '#172533', 1.5); p.line(0, 1, v.a + v.b, 1, '#172533', 1.5); p.line(0, 2.2, v.a + v.b, 2.2, '#172533', 1.5);
  p.text(Kit.fmt(s.first), v.a / 2, 2.2, '#215783', -10, -10); p.text(Kit.fmt(s.second), v.a + v.b / 2, 2.2, '#963d18', -10, -10);
  return {sum: v.total + ' shared ' + v.a + ' : ' + v.b + ' gives ' + Kit.fmt(s.first) + ' and ' + Kit.fmt(s.second),
    rows: [1, 2, 3, 5, 10].map(k => ['× ' + k, String(v.a * k), String(v.b * k), String((v.a + v.b) * k)]),
    result: 'The ratio ' + v.a + ' : ' + v.b + (sa !== v.a ? ' simplifies to ' + sa + ' : ' + sb : ' is already in its simplest form') + '. There are ' + (v.a + v.b) + ' equal parts, so one part of ' + v.total + ' is ' + Kit.fmt(s.part) + '.'};
}
function start() {
  const ids = ["a", "b", "total"];
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

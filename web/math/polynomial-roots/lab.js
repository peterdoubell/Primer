'use strict';
const Model = {
  // Coefficients of a(x − r1)(x − r2)…, highest power first.
  expand(a, roots) { let c = [a]; for (const r of roots) { const n = [...c, 0]; for (let i = 0; i < c.length; i++) n[i + 1] -= r * c[i]; c = n; } return c; },
  value: (coefficients, x) => coefficients.reduce((sum, c) => sum * x + c, 0),
  text(coefficients) {
    const up = {0: '', 1: 'x', 2: 'x²', 3: 'x³'}, n = coefficients.length - 1; let out = '';
    coefficients.forEach((c, i) => { if (!c) return; const power = up[n - i], size = Math.abs(c), body = (size === 1 && power ? '' : size) + power; out += out ? (c < 0 ? ' − ' : ' + ') + body : (c < 0 ? '−' : '') + body; });
    return out || '0';
  },
  factored(a, roots) { return (a === 1 ? '' : a === -1 ? '−' : String(a).replace('-', '−')) + roots.map(r => r === 0 ? 'x' : '(x ' + (r < 0 ? '+ ' : '− ') + Math.abs(r) + ')').join(''); },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const roots = [v.r1, v.r2, v.r3], c = Model.expand(v.a, roots), p = Kit.plot(canvas, {x: [-5, 5], y: [-60, 60]});
  p.curve(x => Model.value(c, x), '#215783'); for (const r of roots) p.point(r, 0, '#963d18', 6); p.point(0, Model.value(c, 0), '#3c7a4b', 5);
  if (v.a === 0) return {sum: 'y = 0', rows: [['Leading coefficient', '0']], result: 'With a leading coefficient of 0 nothing is left: the polynomial is zero everywhere.'};
  const repeated = new Set(roots).size < 3;
  return {sum: 'y = ' + Model.text(c),
    rows: [['Factored form', Model.factored(v.a, roots)], ['Expanded form', Model.text(c)], ['Degree', '3'], ['Roots', [...new Set(roots)].sort((x, y) => x - y).join(', ').replace(/-/g, '−')], ['Crosses the y-axis at', String(c[3]).replace('-', '−')], ['Sum of the roots (−b ÷ a)', String(-c[1] / c[0]).replace('-', '−')]],
    result: 'As x grows large, y ' + (v.a > 0 ? 'rises' : 'falls') + ' on the right and ' + (v.a > 0 ? 'falls' : 'rises') + ' on the left, because the degree is odd.' + (repeated ? ' A repeated root makes the graph touch the axis there instead of passing straight through.' : '')};
}
function start() {
  const ids = ["a", "r1", "r2", "r3"];
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

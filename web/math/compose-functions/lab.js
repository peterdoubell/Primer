'use strict';
const Model = {
  FUNCTIONS: {double: x => 2 * x + 1, square: x => x * x, shift: x => x - 3, half: x => x / 2, abs: x => Math.abs(x)},
  apply: (name, x) => Model.FUNCTIONS[name](x),
  // (outer ∘ inner)(x) = outer(inner(x))
  compose: (outer, inner, x) => Model.apply(outer, Model.apply(inner, x)),
  // Do the two orders agree at every half step from -5 to 5?
  commute(f, g) { for (let x = -5; x <= 5; x += 0.5) if (Math.abs(Model.compose(f, g, x) - Model.compose(g, f, x)) > 1e-9) return false; return true; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-6, 6], y: [-10, 30]}), fg = Model.compose(v.f, v.g, v.x), gf = Model.compose(v.g, v.f, v.x);
  p.curve(x => Model.apply(v.f, x), '#215783'); p.curve(x => Model.apply(v.g, x), '#3c7a4b'); p.curve(x => Model.compose(v.f, v.g, x), '#963d18');
  p.point(v.x, Model.apply(v.f, v.x), '#215783'); p.point(v.x, Model.apply(v.g, v.x), '#3c7a4b'); p.point(v.x, fg, '#963d18'); p.text('f(g(x))', v.x, fg);
  return {sum: 'f(g(' + v.x + ')) = ' + Kit.fmt(fg) + '   g(f(' + v.x + ')) = ' + Kit.fmt(gf),
    rows: [['f(x)', Kit.fmt(Model.apply(v.f, v.x))], ['g(x)', Kit.fmt(Model.apply(v.g, v.x))], ['f(g(x)): g first, then f', Kit.fmt(fg)], ['g(f(x)): f first, then g', Kit.fmt(gf)]],
    result: Model.commute(v.f, v.g) ? 'For this pair the two orders give the same result at every input tried. That is unusual.' : 'Composition is not commutative: f(g(x)) and g(f(x)) are different functions. Blue is f, green is g and red is f(g(x)).'};
}
function start() {
  const ids = ["f", "g", "x"];
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

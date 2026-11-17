'use strict';
const Model = {
  // The closed intervals left after n steps.
  intervals(n) { let out = [[0, 1]]; for (let i = 0; i < n; i++) out = out.flatMap(([a, b]) => [[a, a + (b - a) / 3], [b - (b - a) / 3, b]]); return out; },
  count: n => 2 ** n,
  length: n => (2 / 3) ** n,
  removed: n => 1 - (2 / 3) ** n,
  // Is x (a fraction p/q in lowest terms, given as a number) left after n steps?
  contains: (x, n) => Model.intervals(n).some(([a, b]) => x >= a - 1e-12 && x <= b + 1e-12),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-0.03, 1.03], y: [-0.6, v.n + 0.9], grid: false});
  for (let k = 0; k <= v.n; k++) { for (const [a, b] of Model.intervals(k)) p.line(a, v.n - k, b, v.n - k, '#215783', 12); p.text('step ' + k, 0, v.n - k, '#172533', -4, -12); }
  return {sum: Model.count(v.n) + ' pieces, total length ' + Kit.fmt(Model.length(v.n)),
    rows: Array.from({length: v.n + 1}, (_, k) => [String(k), String(Model.count(k)), '1/' + 3 ** k, 2 ** k + '/' + 3 ** k + ' ≈ ' + Kit.fmt(Model.length(k), 3)]),
    result: 'After ' + v.n + ' steps, ' + Kit.fmt(100 * Model.removed(v.n), 4) + '% of the length has been removed, and in the limit all of it: the Cantor set has measure 0. Yet endpoints such as 0, 1, 1/3 and 2/3 are never removed, and the set has as many points as the whole interval. Size by counting and size by measure are different ideas.'};
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

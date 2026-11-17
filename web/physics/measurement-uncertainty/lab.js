'use strict';
const Model = {
  // Half the smallest division is the usual reading uncertainty of a scale.
  uncertainty: step => step / 2,
  relative: (reading, step) => 100 * Model.uncertainty(step) / reading,
  PREFIXES: [['kilometres', 1e-6], ['metres', 1e-3], ['centimetres', 0.1], ['millimetres', 1], ['micrometres', 1000]],
  convert: (mm, factor) => mm * factor,
  // Round to a number of significant figures.
  significant(value, figures) { if (!value) return 0; const power = figures - 1 - Math.floor(Math.log10(Math.abs(value))); return Math.round(value * 10 ** power) / 10 ** power; },
  scientific(value) { const e = Math.floor(Math.log10(Math.abs(value))); return (Math.round(value / 10 ** e * 1000) / 1000) + ' × 10^' + e; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const step = Number(v.step), u = Model.uncertainty(step), lo = Math.floor(v.reading / step) * step - 5 * step, hi = lo + 11 * step, p = Kit.plot(canvas, {x: [lo - step, hi + step], y: [-1.2, 1.6], grid: false});
  axis(p, lo, hi, step); p.line(v.reading - u, 0.6, v.reading + u, 0.6, '#e3b89c', 16); p.line(v.reading, 0.15, v.reading, 1.1, '#963d18', 3); p.text('mm (close-up of the ruler)', hi, 0, '#172533', -170, 44);
  return {sum: v.reading + ' mm ± ' + u + ' mm',
    rows: [['Result', v.reading + ' ± ' + u + ' mm'], ['Range it could lie in', (v.reading - u) + ' mm to ' + (v.reading + u) + ' mm'], ['Uncertainty as a percentage', Kit.fmt(Model.relative(v.reading, step), 3) + '%'],
      ...Model.PREFIXES.map(([name, factor]) => ['In ' + name, Model.scientific(Model.convert(v.reading, factor)) + ' ' + name]), ['To 1 significant figure', Model.significant(v.reading, 1) + ' mm']],
    result: 'The uncertainty is taken as half the smallest division. The same ± ' + u + ' mm matters much more for a short length than a long one: here it is ' + Kit.fmt(Model.relative(v.reading, step), 3) + '% of the reading. Changing the unit changes the number but not the length.'};
}
function start() {
  const ids = ["reading", "step"];
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

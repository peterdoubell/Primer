'use strict';
const Model = {
  line(x1, y1, x2, y2) {
    if (x1 === x2 && y1 === y2) return {kind: 'point'};
    if (x1 === x2) return {kind: 'vertical', x: x1};
    const m = (y2 - y1) / (x2 - x1); return {kind: 'line', m, b: y1 - m * x1, rise: y2 - y1, run: x2 - x1, perpendicular: m === 0 ? null : -1 / m};
  },
  equation(m, b) { const t = n => Kit.fmt(Math.abs(n)); return 'y = ' + (m === 0 ? Kit.fmt(b).replace('-', '−') : (m < 0 ? '−' : '') + (Math.abs(m) === 1 ? '' : t(m)) + 'x' + (b === 0 ? '' : (b < 0 ? ' − ' : ' + ') + t(b))); },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.line(v.x1, v.y1, v.x2, v.y2), p = Kit.plot(canvas, {x: [-8, 8], y: [-8, 8]}), m = t => Kit.fmt(t).replace('-', '−');
  if (r.kind === 'line') { p.curve(x => r.m * x + r.b, '#215783'); p.line(v.x1, v.y1, v.x2, v.y1, '#963d18', 2, [6, 5]); p.line(v.x2, v.y1, v.x2, v.y2, '#3c7a4b', 2, [6, 5]); }
  if (r.kind === 'vertical') p.line(r.x, -8, r.x, 8, '#215783', 3);
  p.point(v.x1, v.y1, '#172533', 6); p.point(v.x2, v.y2, '#172533', 6);
  if (r.kind === 'point') return {sum: 'One point only', rows: [['Points', 'the same point twice']], result: 'One point does not fix a line. Move one of the points.'};
  if (r.kind === 'vertical') return {sum: 'x = ' + m(r.x), rows: [['Run', '0'], ['Slope', 'undefined'], ['Equation', 'x = ' + m(r.x)]], result: 'The run is zero, so rise over run would divide by zero. A vertical line has no slope and its equation is x = ' + m(r.x) + '.'};
  return {sum: Model.equation(r.m, r.b),
    rows: [['Rise (change in y)', m(r.rise)], ['Run (change in x)', m(r.run)], ['Slope', m(r.m)], ['y-intercept', m(r.b)], ['Equation', Model.equation(r.m, r.b)], ['Slope of a parallel line', m(r.m)], ['Slope of a perpendicular line', r.perpendicular === null ? 'undefined (vertical)' : m(r.perpendicular)]],
    result: r.m === 0 ? 'The rise is zero, so the line is horizontal with slope 0.' : 'For every 1 across, the line goes ' + (r.m > 0 ? 'up ' : 'down ') + Kit.fmt(Math.abs(r.m)) + '. Perpendicular slopes multiply to −1.'};
}
function start() {
  const ids = ["x1", "y1", "x2", "y2"];
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

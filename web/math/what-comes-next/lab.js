'use strict';
const Model = {
  PATTERNS: {ab: {unit: ['red', 'blue']}, aab: {unit: ['red', 'red', 'blue']}, abc: {unit: ['red', 'blue', 'green']}, plus2: {first: 1, step: 2}, plus3: {first: 2, step: 3}},
  // Item at position i, counting from 1.
  term(kind, i) { const p = Model.PATTERNS[kind]; return p.unit ? p.unit[(i - 1) % p.unit.length] : p.first + (i - 1) * p.step; },
  sequence: (kind, n) => Array.from({length: n}, (_, i) => Model.term(kind, i + 1)),
  rule(kind) { const p = Model.PATTERNS[kind]; return p.unit ? 'Repeat ' + p.unit.join(', ') + ' again and again.' : 'Start at ' + p.first + ' and add ' + p.step + ' each time.'; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const items = Model.sequence(v.kind, v.n), next = Model.term(v.kind, v.n + 1), colours = {red: '#b3261e', blue: '#215783', green: '#3c7a4b'}, growing = typeof next === 'number';
  const p = Kit.plot(canvas, {x: [0, 12], y: [0, growing ? 36 : 2], grid: false});
  [...items, next].forEach((item, i) => {
    const last = i === items.length;
    if (growing) { p.line(i + 1, 0, i + 1, item, last ? '#9aa6ae' : '#215783', 18); p.text(last ? '?' : String(item), i + 1, item, '#172533', -6, -8); }
    else { p.point(i + 1, 1, last ? '#ffffff' : colours[item], 15); if (last) p.text('?', i + 1, 1, '#172533', -5, 6); }
  });
  return {sum: items.join(', ') + ', …',
    rows: items.map((item, i) => [String(i + 1), String(item)]),
    result: 'Rule: ' + Model.rule(v.kind) + ' So the next one is ' + next + '.'};
}
function start() {
  const ids = ["kind", "n"];
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

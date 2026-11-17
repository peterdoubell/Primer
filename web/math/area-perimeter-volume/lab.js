'use strict';
const Model = {
  measure(shape, a, b, c) {
    if (shape === 'rectangle') return [['Perimeter', '2 × (a + b)', 2 * (a + b), 'units'], ['Area', 'a × b', a * b, 'square units']];
    if (shape === 'triangle') { const h = Math.hypot(a, b); return [['Longest side', '√(a² + b²)', h, 'units'], ['Perimeter', 'a + b + longest side', a + b + h, 'units'], ['Area', '½ × a × b', a * b / 2, 'square units']]; }
    if (shape === 'circle') return [['Diameter', '2 × a', 2 * a, 'units'], ['Circumference', '2 × π × a', 2 * Math.PI * a, 'units'], ['Area', 'π × a²', Math.PI * a * a, 'square units']];
    return [['Volume', 'a × b × c', a * b * c, 'cubic units'], ['Surface area', '2 × (ab + bc + ac)', 2 * (a * b + b * c + a * c), 'square units'], ['Total edge length', '4 × (a + b + c)', 4 * (a + b + c), 'units']];
  },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-4, 20.8], y: [-1.8, 15.8], grid: false}), blue = '#215783', rows = Model.measure(v.shape, v.a, v.b, v.c);
  if (v.shape === 'rectangle') { p.line(0, 0, v.a, 0, blue, 3); p.line(v.a, 0, v.a, v.b, blue, 3); p.line(v.a, v.b, 0, v.b, blue, 3); p.line(0, v.b, 0, 0, blue, 3); p.text('a = ' + v.a, v.a / 2, 0, '#172533', -16, 20); p.text('b = ' + v.b, v.a, v.b / 2); }
  if (v.shape === 'triangle') { p.line(0, 0, v.a, 0, blue, 3); p.line(0, 0, 0, v.b, blue, 3); p.line(v.a, 0, 0, v.b, '#963d18', 3); p.text('a = ' + v.a, v.a / 2, 0, '#172533', -16, 20); p.text('b = ' + v.b, 0, v.b / 2, '#172533', -52, 0); }
  if (v.shape === 'circle') { const k = 0.55, cx = 8, cy = 6.5; for (let i = 0; i < 120; i++) p.line(cx + k * v.a * Math.cos(i * Math.PI / 60), cy + k * v.a * Math.sin(i * Math.PI / 60), cx + k * v.a * Math.cos((i + 1) * Math.PI / 60), cy + k * v.a * Math.sin((i + 1) * Math.PI / 60), blue, 3); p.line(cx, cy, cx + k * v.a, cy, '#963d18', 3); p.text('radius a = ' + v.a, cx, cy, '#172533', 4, -8); }
  if (v.shape === 'cuboid') { const dx = v.b * 0.45, dy = v.b * 0.3, box = [[0, 0], [v.a, 0], [v.a, v.c], [0, v.c]]; box.forEach(([x, y], i) => { const [nx, ny] = box[(i + 1) % 4]; p.line(x, y, nx, ny, blue, 3); p.line(x + dx, y + dy, nx + dx, ny + dy, blue, i < 1 || i > 2 ? 1 : 3, i < 1 || i > 2 ? [5, 5] : []); p.line(x, y, x + dx, y + dy, blue, i === 0 ? 1 : 3, i === 0 ? [5, 5] : []); }); p.text('a = ' + v.a, v.a / 2, 0, '#172533', -16, 20); p.text('c = ' + v.c, 0, v.c / 2, '#172533', -52, 0); p.text('b = ' + v.b, v.a + dx / 2, dy / 2, '#172533', 8, 6); }
  return {sum: rows.map(r => r[0] + ' ' + Kit.fmt(r[2])).join(' · '),
    rows: rows.map(r => [r[0], r[1], Kit.fmt(r[2]) + ' ' + r[3]]),
    result: v.shape === 'cuboid' ? 'Volume counts unit cubes: ' + v.a + ' × ' + v.b + ' in each layer, and ' + v.c + ' layers.' : 'Length is measured in units, area in square units. Doubling every length doubles the perimeter but makes the area four times as large.'};
}
function start() {
  const ids = ["shape", "a", "b", "c"];
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

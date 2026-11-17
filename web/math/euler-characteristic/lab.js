'use strict';
const Model = {
  SURFACES: {tetrahedron: [4, 6, 4], cube: [8, 12, 6], octahedron: [6, 12, 8], dodecahedron: [20, 30, 12], icosahedron: [12, 30, 20], prism: [6, 9, 5], torus: [9, 18, 9], doubletorus: [1, 4, 1]},
  NAMES: {tetrahedron: 'Tetrahedron', cube: 'Cube', octahedron: 'Octahedron', dodecahedron: 'Dodecahedron', icosahedron: 'Icosahedron', prism: 'Triangular prism', torus: 'Torus (3 × 3 grid)', doubletorus: 'Two-holed torus'},
  characteristic(name) { const [V, E, F] = Model.SURFACES[name]; return V - E + F; },
  // Number of holes of a closed orientable surface: χ = 2 − 2g.
  genus: name => (2 - Model.characteristic(name)) / 2,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const [V, E, F] = Model.SURFACES[v.solid], chi = Model.characteristic(v.solid), g = Model.genus(v.solid), p = Kit.plot(canvas, {x: [0, 4], y: [0, 34], grid: false});
  [['corners', V, '#215783'], ['edges', E, '#963d18'], ['faces', F, '#3c7a4b']].forEach(([name, count, colour], i) => { p.line(i + 1, 0, i + 1, count, colour, 60); p.text(name + ': ' + count, i + 1, count, '#172533', -34, -10); });
  p.line(0.3, 0, 3.7, 0, '#172533', 2);
  return {sum: 'V − E + F = ' + V + ' − ' + E + ' + ' + F + ' = ' + String(chi).replace('-', '−'),
    rows: Object.keys(Model.SURFACES).map(name => [Model.NAMES[name], ...Model.SURFACES[name].map(String), String(Model.characteristic(name)).replace('-', '−')]),
    result: g === 0 ? 'This surface can be inflated into a sphere, and every way of cutting a sphere into corners, edges and faces gives 2.' : 'This surface has ' + g + (g === 1 ? ' hole' : ' holes') + '. For a closed surface with g holes the count is always 2 − 2g, here ' + String(chi).replace('-', '−') + ', so it cannot be deformed into a sphere.'};
}
function start() {
  const ids = ["solid"];
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

'use strict';
const Model = {
  // Field direction of a small bar magnet at the origin with its north pole toward +x (a dipole). Returns a unit vector, or null at the centre.
  field(x, y) { const r2 = x * x + y * y; if (!r2) return null; const bx = (3 * x * x - r2), by = 3 * x * y, size = Math.hypot(bx, by); return [bx / size + 0, by / size + 0]; },
  angle(x, y) { const f = Model.field(x, y); return f ? Math.atan2(f[1], f[0]) * 180 / Math.PI : null; },
  // Like poles repel, unlike poles attract.
  force: (pole, other) => pole === other ? 'repel' : 'attract',
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5], grid: false}), f = Model.field(v.x, v.y), near = v.x >= 0 ? 'N' : 'S';
  for (let x = -4.5; x <= 4.5; x += 1) for (let y = -4.5; y <= 4.5; y += 1) { const g = Model.field(x, y); if (g && Math.hypot(x, y) > 1.2) p.arrow(x - g[0] * 0.3, y - g[1] * 0.3, x + g[0] * 0.3, y + g[1] * 0.3, '#b9c3ca', 1.5); }
  p.line(-0.9, 0, 0, 0, '#215783', 26); p.line(0, 0, 0.9, 0, '#b3261e', 26); p.text('S', -0.6, 0, '#fff', -4, 6); p.text('N', 0.5, 0, '#fff', -4, 6);
  if (f) { p.arrow(v.x - f[0] * 0.6, v.y - f[1] * 0.6, v.x + f[0] * 0.6, v.y + f[1] * 0.6, '#b3261e', 4); p.point(v.x, v.y, '#172533', 4); }
  return {sum: f ? 'Needle points ' + Kit.fmt(Model.angle(v.x, v.y), 3).replace('-', '−') + '° from the magnet’s axis' : 'Move the compass off the magnet',
    rows: [['Needle direction', f ? Kit.fmt(Model.angle(v.x, v.y), 3).replace('-', '−') + '°' : '—'], ['Nearer pole of the magnet', near === 'N' ? 'north' : 'south'], ['Second magnet, ' + (v.facing === 'N' ? 'north' : 'south') + ' pole first, at that end', 'they ' + Model.force(v.facing, near)]],
    result: 'Field lines leave the north pole and curve round to the south pole; the needle lines up along them. Like poles repel and unlike poles attract. Earth acts as a magnet too, which is why a compass finds north.'};
}
function start() {
  const ids = ["x", "y", "facing"];
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

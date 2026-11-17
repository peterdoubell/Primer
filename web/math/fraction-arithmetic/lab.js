'use strict';
const Model = {
  SIGNS: {add: '+', subtract: '−', multiply: '×', divide: '÷'},
  gcd: (a, b) => b ? Model.gcd(b, a % b) : Math.abs(a),
  lcm: (a, b) => a / Model.gcd(a, b) * b,
  // [numerator, denominator] in lowest terms with a positive denominator.
  simplify(n, d) { const g = Model.gcd(n, d) || 1, s = d < 0 ? -1 : 1; return [s * n / g, s * d / g]; },
  calc(n1, d1, n2, d2, op) {
    if (op === 'add') return Model.simplify(n1 * d2 + n2 * d1, d1 * d2);
    if (op === 'subtract') return Model.simplify(n1 * d2 - n2 * d1, d1 * d2);
    if (op === 'multiply') return Model.simplify(n1 * n2, d1 * d2);
    return n2 === 0 ? null : Model.simplify(n1 * d2, d1 * n2);
  },
  compare: (n1, d1, n2, d2) => Math.sign(n1 * d2 - n2 * d1),
  text: ([n, d]) => (d === 1 ? String(n) : n + '/' + d).replace('-', '−'),
  mixed([n, d]) { if (d === 1 || Math.abs(n) < d) return Model.text([n, d]); const whole = Math.trunc(n / d); return (whole + ' and ' + Math.abs(n % d) + '/' + d).replace('-', '−'); },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.calc(v.n1, v.d1, v.n2, v.d2, v.op), common = Model.lcm(v.d1, v.d2), p = Kit.plot(canvas, {x: [-0.1, 4.1], y: [0, 3.2], grid: false});
  const bar = (n, d, y, colour) => { const top = Math.min(n / d, 4); for (let k = 0; k <= 16; k++) p.line(0, y + k / 40, top, y + k / 40, colour, 3); for (let i = 0; i <= 4 * d; i++) p.line(i / d, y, i / d, y + 0.4, '#172533', i % d ? 0.6 : 2); p.line(0, y, 4, y); p.line(0, y + 0.4, 4, y + 0.4); };
  bar(v.n1, v.d1, 2.4, '#8fb6d6'); bar(v.n2, v.d2, 1.4, '#e3b89c'); if (r && r[0] >= 0) bar(r[0], r[1], 0.4, '#a9cdb1');
  p.text(v.n1 + '/' + v.d1, 0, 2.8, '#172533', 0, -10); p.text(v.n2 + '/' + v.d2, 0, 1.8, '#172533', 0, -10); if (r && r[0] >= 0) p.text('answer', 0, 0.8, '#172533', 0, -10);
  const order = Model.compare(v.n1, v.d1, v.n2, v.d2), same = v.op === 'add' || v.op === 'subtract';
  return {sum: v.n1 + '/' + v.d1 + ' ' + Model.SIGNS[v.op] + ' ' + v.n2 + '/' + v.d2 + ' = ' + (r ? Model.text(r) : 'not defined'),
    rows: [['Common bottom number', same ? String(common) : 'not needed'], ['Rewritten', same ? (v.n1 * common / v.d1) + '/' + common + ' and ' + (v.n2 * common / v.d2) + '/' + common : v.op === 'divide' ? 'multiply by ' + v.d2 + '/' + v.n2 : 'tops together, bottoms together'],
      ['Answer in lowest terms', r ? Model.text(r) : 'cannot divide by zero'], ['As a mixed number', r ? Model.mixed(r) : '—'], ['As a decimal', r ? Kit.fmt(r[0] / r[1]) : '—'],
      ['Which is bigger?', order ? (order > 0 ? v.n1 + '/' + v.d1 : v.n2 + '/' + v.d2) : 'they are equal']],
    result: same ? 'You can only add or subtract parts of the same size, so both fractions are rewritten over ' + common + '.' : v.op === 'multiply' ? 'Multiply the tops and multiply the bottoms, then simplify.' : 'Dividing by a fraction is the same as multiplying by it turned upside down.'};
}
function start() {
  const ids = ["n1", "d1", "op", "n2", "d2"];
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

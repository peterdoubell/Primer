'use strict';
const Model = {
  // Each step writes a = q × b + r; the last non-zero remainder is the gcd.
  euclid(a, b) { const steps = []; while (b) { const q = Math.floor(a / b), r = a % b; steps.push({a, b, q, r}); a = b; b = r; } return {steps, gcd: a}; },
  gcd: (a, b) => Model.euclid(a, b).gcd,
  // The x with a × x ≡ 1 (mod n), or null when a and n share a factor.
  inverse(a, n) { for (let x = 1; x < n; x++) if (a * x % n === 1) return x; return null; },
  power(a, k, n) { let result = 1 % n, base = a % n; while (k > 0) { if (k % 2) result = result * base % n; base = base * base % n; k = Math.floor(k / 2); } return result; },
  // The residues reached by 0, a, 2a, … modulo n.
  multiples(a, n) { const seen = []; let x = 0; do { seen.push(x); x = (x + a) % n; } while (x !== 0); return seen; },
  isPrime(n) { if (n < 2) return false; for (let d = 2; d * d <= n; d++) if (n % d === 0) return false; return true; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const e = Model.euclid(v.a, v.n), reach = Model.multiples(v.a, v.n), inv = Model.inverse(v.a, v.n), p = Kit.plot(canvas, {x: [-1.25, 1.25], y: [-1.25, 1.25], grid: false});
  const at = k => [Math.sin(2 * Math.PI * k / v.n), Math.cos(2 * Math.PI * k / v.n)];
  reach.forEach((k, i) => { const [x, y] = at(k), [nx, ny] = at(reach[(i + 1) % reach.length]); p.line(x, y, nx, ny, '#8fb6d6', 1.5); });
  for (let k = 0; k < v.n; k++) { const [x, y] = at(k); p.point(x, y, reach.includes(k) ? '#215783' : '#c3ccd2', v.n > 30 ? 4 : 6, !reach.includes(k)); }
  p.text('0', 0, 1, '#172533', -4, -12);
  const rows = e.steps.map((s, i) => ['Step ' + (i + 1), s.a + ' = ' + s.q + ' × ' + s.b + ' + ' + s.r]);
  rows.push(['Greatest common divisor', String(e.gcd)], ['Hours reached by multiples of ' + v.a, reach.length + ' of ' + v.n], ['Inverse of ' + v.a + ' modulo ' + v.n, inv === null ? 'none' : String(inv)]);
  if (Model.isPrime(v.n) && v.a % v.n) rows.push([v.a + ' to the power ' + (v.n - 1) + ', modulo ' + v.n, String(Model.power(v.a, v.n - 1, v.n))]);
  return {sum: 'gcd(' + v.a + ', ' + v.n + ') = ' + e.gcd, rows,
    result: e.gcd === 1 ? 'The gcd is 1, so stepping by ' + v.a + ' visits every hour and ' + v.a + ' has an inverse: ' + v.a + ' × ' + inv + ' leaves remainder 1.' + (Model.isPrime(v.n) ? ' Because ' + v.n + ' is prime, Fermat’s little theorem gives remainder 1 for the power shown.' : '') : 'The gcd is ' + e.gcd + ', so stepping by ' + v.a + ' only visits ' + reach.length + ' hours (' + v.n + ' ÷ ' + e.gcd + ') and ' + v.a + ' has no inverse modulo ' + v.n + '.'};
}
function start() {
  const ids = ["a", "n"];
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

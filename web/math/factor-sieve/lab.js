'use strict';
const Model = {
  sieve(limit) {
    const prime = Array(limit + 1).fill(true); prime[0] = prime[1] = false;
    for (let i = 2; i * i <= limit; i++) if (prime[i]) for (let j = i * i; j <= limit; j += i) prime[j] = false;
    return prime;
  },
  factorise(n) {
    const out = [];
    for (let p = 2; p * p <= n; p++) while (n % p === 0) { out.push(p); n /= p; }
    if (n > 1) out.push(n);
    return out;
  },
  divisors(n) { const out = []; for (let d = 1; d <= n; d++) if (n % d === 0) out.push(d); return out; },
  gcd(a, b) { while (b) [a, b] = [b, a % b]; return a; },
  lcm: (a, b) => a / Model.gcd(a, b) * b,
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d'), LIMIT = 200, primes = Model.sieve(LIMIT);
  const power = list => Object.entries(list.reduce((m, p) => (m[p] = (m[p] || 0) + 1, m), {})).map(([p, e]) => e > 1 ? p + '^' + e : p).join(' × ');
  function draw() {
    const n = Kit.num('n'), m = Kit.num('m'), factors = Model.factorise(n), first = factors[0];
    Kit.say('n', n, 'n = ' + n); Kit.say('m', m, 'm = ' + m);
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '14px system-ui, sans-serif';
    for (let v = 1; v <= LIMIT; v++) {
      const col = (v - 1) % 20, row = Math.floor((v - 1) / 20), x = 4 + col * 35.6, y = 4 + row * 35;
      ctx.fillStyle = v === n ? '#172533' : primes[v] ? '#f2c48d' : v > 1 && v % first === 0 ? '#bcd6ea' : '#f1f2f0';
      ctx.fillRect(x, y, 33, 32);
      ctx.fillStyle = v === n ? '#fff' : '#172533'; const s = String(v); ctx.fillText(s, x + 16.5 - ctx.measureText(s).width / 2, y + 21);
    }
    const g = Model.gcd(n, m);
    Kit.rows(Kit.get('rows'), [['Prime factorisation of ' + n, primes[n] ? n + ' is prime' : power(factors)],
      ['Divisors of ' + n, Model.divisors(n).join(', ')], ['Prime factorisation of ' + m, primes[m] ? m + ' is prime' : power(Model.factorise(m))],
      ['Greatest common divisor', String(g)], ['Least common multiple', String(Model.lcm(n, m))]]);
    Kit.get('result').textContent = 'Orange squares are primes. Blue squares are the multiples of ' + first + ', the smallest prime factor of ' + n + '. gcd × lcm = ' + g * Model.lcm(n, m) + ' = ' + n + ' × ' + m + '.';
    canvas.setAttribute('aria-label', 'Grid of the numbers 1 to 200 with primes highlighted and ' + n + ' selected. ' + Kit.get('result').textContent);
  }
  Kit.bind(['n', 'm'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

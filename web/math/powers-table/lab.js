'use strict';
const Model = {
  power: (a, n) => a ** n,
  expand(a, n) {
    if (n === 0) return '1 (any non-zero number to the power 0)';
    const product = Array(Math.abs(n)).fill(a < 0 ? '(' + a + ')' : a).join(' × ');
    return n > 0 ? product : '1 ÷ (' + product + ')';
  },
  // a^m × a^n = a^(m+n); a^m ÷ a^n = a^(m−n); (a^m)^n = a^(mn).
  laws: (a, m, n) => ({product: [a ** m * a ** n, a ** (m + n)], quotient: [a ** m / a ** n, a ** (m - n)], power: [(a ** m) ** n, a ** (m * n)]}),
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const a = Kit.num('base'), n = Kit.num('exponent'), m = Kit.num('second'), value = Model.power(a, n), laws = Model.laws(a, n, m);
    Kit.say('base', a, 'a = ' + a); Kit.say('exponent', n, 'n = ' + n); Kit.say('second', m, 'm = ' + m);
    const xs = [-3, -2, -1, 0, 1, 2, 3, 4, 5, 6], top = Math.max(...xs.map(x => Math.abs(Model.power(a, x))));
    const p = Kit.plot(canvas, {x: [-3.5, 6.5], y: [a < 0 ? -top * 1.1 : 0, top * 1.1], xlabel: 'exponent n', ylabel: 'aⁿ'});
    xs.forEach(x => { p.line(x, 0, x, Model.power(a, x), x === n ? '#963d18' : '#215783', 10); });
    Kit.rows(Kit.get('rows'), [[a + ' to the power ' + n, Model.expand(a, n), Kit.fmt(value, 8)],
      ['Multiply: a' + '^' + n + ' × a^' + m, 'add the exponents: a^' + (n + m), Kit.fmt(laws.product[1], 8)],
      ['Divide: a^' + n + ' ÷ a^' + m, 'subtract the exponents: a^' + (n - m), Kit.fmt(laws.quotient[1], 8)],
      ['Power of a power: (a^' + n + ')^' + m, 'multiply the exponents: a^' + (n * m), Kit.fmt(laws.power[1], 8)]]);
    Kit.get('result').textContent = (n > 0 ? 'A positive exponent counts how many times ' + a + ' is multiplied by itself.' : n === 0 ? 'A zero exponent gives 1.' : 'A negative exponent means divide: ' + a + '^' + n + ' = 1/' + a + '^' + (-n) + '.')
      + ' Each step to the right multiplies by ' + a + '; each step to the left divides by ' + a + '.';
    canvas.setAttribute('aria-label', 'Bar chart of powers of ' + a + ' for exponents −3 to 6. ' + Kit.get('result').textContent);
  }
  Kit.bind(['base', 'exponent', 'second'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

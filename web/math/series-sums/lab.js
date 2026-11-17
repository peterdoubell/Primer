'use strict';
const Model = {
  term: (kind, a, d, n) => kind === 'arithmetic' ? a + (n - 1) * d : a * d ** (n - 1),
  partial(kind, a, d, n) { let total = 0; for (let k = 1; k <= n; k++) total += Model.term(kind, a, d, k); return total; },
  closed: (kind, a, d, n) => kind === 'arithmetic' ? n * (2 * a + (n - 1) * d) / 2 : d === 1 ? a * n : a * (1 - d ** n) / (1 - d),
  // Sum to infinity of a geometric series; null when it does not converge.
  limit: (kind, a, d) => kind === 'geometric' && Math.abs(d) < 1 ? a / (1 - d) : null,
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const kind = Kit.get('kind').value, a = Kit.num('first'), d = Kit.num('step'), n = Kit.num('count');
    Kit.get('step-label').textContent = kind === 'arithmetic' ? 'Common difference d' : 'Common ratio r';
    Kit.say('first', a, 'a = ' + a); Kit.say('step', d, (kind === 'arithmetic' ? 'd = ' : 'r = ') + d); Kit.say('count', n, 'n = ' + n);
    const terms = Array.from({length: n}, (_, i) => Model.term(kind, a, d, i + 1));
    const sums = terms.map((_, i) => Model.partial(kind, a, d, i + 1));
    const all = [...terms, ...sums, 0], lo = Math.min(...all), hi = Math.max(...all), pad = (hi - lo || 1) * 0.08;
    const p = Kit.plot(canvas, {x: [0, n + 1], y: [lo - pad, hi + pad], xlabel: 'term number', ylabel: 'value'});
    terms.forEach((value, i) => p.line(i + 1 - 0.18, 0, i + 1 - 0.18, value, '#215783', 9));
    sums.forEach((value, i) => { p.point(i + 1 + 0.18, value, '#963d18', 4); if (i) p.line(i + 0.18, sums[i - 1], i + 1 + 0.18, value, '#963d18', 1.5); });
    const limit = Model.limit(kind, a, d);
    if (limit !== null) p.line(0, limit, n + 1, limit, '#172533', 1.5, [6, 4]);
    Kit.rows(Kit.get('rows'), [
      ['Term ' + n, terms[n - 1], kind === 'arithmetic' ? 'a + (n − 1)d' : 'a·rⁿ⁻¹'],
      ['Sum of ' + n + ' terms, added one by one', sums[n - 1], 'direct addition'],
      ['Sum of ' + n + ' terms, formula', Model.closed(kind, a, d, n), kind === 'arithmetic' ? 'n(2a + (n − 1)d)/2' : 'a(1 − rⁿ)/(1 − r)'],
    ]);
    Kit.get('result').textContent = 'Blue bars are the terms; orange points are the running sums. ' + (kind === 'arithmetic'
      ? 'An arithmetic series adds the same amount each time, so its sums follow a parabola.'
      : limit !== null ? 'Because |r| < 1 the sums approach a/(1 − r) = ' + Kit.fmt(limit) + ' (dashed line).' : 'Because |r| ≥ 1 the sums do not settle on a limit.');
    canvas.setAttribute('aria-label', 'Bar chart of the first ' + n + ' terms with running sums. ' + Kit.get('result').textContent);
  }
  Kit.bind(['kind', 'first', 'step', 'count'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

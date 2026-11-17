'use strict';
const Model = {
  FORMULAS: {imp: (p, q) => !p || q, and: (p, q) => p && q, or: (p, q) => p || q, iff: (p, q) => p === q, nand: (p, q) => !(p && q), nor: (p, q) => !(p || q), taut: p => p || !p,
    ornot: (p, q) => !p || q, contra: (p, q) => !(!q) || !p, conv: (p, q) => !q || p, demorgan: (p, q) => !p || !q, demorgan2: (p, q) => !p && !q, both: (p, q) => (!p || q) && (!q || p), absurd: p => p && !p},
  CASES: [[true, true], [true, false], [false, true], [false, false]],
  table: name => Model.CASES.map(([p, q]) => Boolean(Model.FORMULAS[name](p, q))),
  equivalent: (f, g) => Model.table(f).every((value, i) => value === Model.table(g)[i]),
  tautology: name => Model.table(name).every(Boolean),
  contradiction: name => Model.table(name).every(value => !value),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const F = Model.table(v.f), G = Model.table(v.g), same = Model.equivalent(v.f, v.g), ctx = canvas.getContext('2d'), t = b => b ? 'T' : 'F', label = id => Kit.get(id).selectedOptions[0].textContent;
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '18px system-ui, sans-serif';
  [['P', 60], ['Q', 150], [label('f'), 260], [label('g'), 480]].forEach(([text, x]) => { ctx.fillStyle = '#172533'; ctx.fillText(text, x, 34); });
  Model.CASES.forEach(([P, Q], i) => [[P, 60, 60], [Q, 150, 60], [F[i], 260, 190], [G[i], 480, 190]].forEach(([value, x, w]) => { ctx.fillStyle = value ? '#a9cdb1' : '#e9b3a8'; ctx.fillRect(x - 12, 50 + i * 44, w, 36); ctx.fillStyle = '#172533'; ctx.fillText(t(value), x, 75 + i * 44); }));
  ctx.strokeStyle = same ? '#3c7a4b' : '#b3261e'; ctx.lineWidth = 3; ctx.strokeRect(244, 46, 412, 4 * 44);
  const kind = name => Model.tautology(name) ? 'a tautology (always true)' : Model.contradiction(name) ? 'a contradiction (never true)' : 'sometimes true, sometimes false';
  return {sum: label('f') + (same ? '  ≡  ' : '  ≢  ') + label('g'),
    rows: Model.CASES.map(([P, Q], i) => [t(P), t(Q), t(F[i]), t(G[i])]),
    result: (same ? 'The two columns agree in all four cases, so the formulas are logically equivalent.' : 'The columns differ in at least one case, so the formulas are not equivalent.') + ' The first is ' + kind(v.f) + '; the second is ' + kind(v.g) + '.'};
}
function start() {
  const ids = ["f", "g"];
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

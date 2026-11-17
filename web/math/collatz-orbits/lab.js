'use strict';
const Model = {
  next: n => n % 2 ? 3 * n + 1 : n / 2,
  orbit(n) { const out = [n]; while (n !== 1) { n = Model.next(n); out.push(n); } return out; },
  steps: n => Model.orbit(n).length - 1,
  peak: n => Math.max(...Model.orbit(n)),
  // The start up to a limit that takes the most steps.
  longest(limit) { let best = 1; for (let n = 2; n <= limit; n++) if (Model.steps(n) > Model.steps(best)) best = n; return best; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const orbit = Model.orbit(v.n), peak = Model.peak(v.n), p = Kit.plot(canvas, {x: [0, Math.max(orbit.length - 1, 1)], y: [0, peak * 1.1], xlabel: 'step', ylabel: 'value'});
  orbit.forEach((value, i) => { if (i) p.line(i - 1, orbit[i - 1], i, value, '#215783', 2); }); orbit.forEach((value, i) => p.point(i, value, value === peak ? '#963d18' : '#215783', value === peak ? 6 : 3));
  const longest = Model.longest(200);
  return {sum: v.n + ' reaches 1 in ' + (orbit.length - 1) + ' steps',
    rows: [['Steps to reach 1', String(orbit.length - 1)], ['Highest value reached', String(peak)], ['First terms', orbit.slice(0, 12).join(', ') + (orbit.length > 12 ? ', …' : '')], ['Odd steps (× 3 + 1)', String(orbit.filter(x => x % 2 && x !== 1).length)], ['Longest run for a start up to 200', longest + ' takes ' + Model.steps(longest) + ' steps']],
    result: 'Every starting number ever tried reaches 1, and computers have checked far beyond anything shown here. But checking is not proof: whether all whole numbers reach 1 is the Collatz conjecture, and it is still open.'};
}
function start() {
  const ids = ["n"];
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

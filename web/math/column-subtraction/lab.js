'use strict';
const Model = {
  subtract(a, b) {
    const exchange = a % 10 < b % 10, ones = a % 10 + (exchange ? 10 : 0) - b % 10, tens = Math.floor(a / 10) - (exchange ? 1 : 0) - Math.floor(b / 10);
    return {difference: a - b, exchange, ones, tens, possible: a >= b};
  },
  check: (a, b) => (a - b) + b === a,
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.subtract(v.a, v.b), p = Kit.plot(canvas, {x: [-4, 104], y: [-1.2, 1.6], grid: false});
  axis(p, 0, 100, 10); p.arrow(0, 0.5, v.a, 0.5, '#215783');
  if (r.possible) { p.arrow(v.a, 1, r.difference, 1, '#963d18'); p.point(r.difference, 0, '#172533', 6); p.text('− ' + v.b, (v.a + r.difference) / 2, 1, '#963d18', -12, -8); }
  p.text(String(v.a), v.a / 2, 0.5, '#215783', -8, -8);
  if (!r.possible) return {sum: v.a + ' − ' + v.b, rows: [['Can you take ' + v.b + ' from ' + v.a + '?', 'not without going below zero'], ['How far apart are they?', String(v.b - v.a)]],
    result: 'There are only ' + v.a + ' to start with, so you cannot take away ' + v.b + '. The two numbers are ' + (v.b - v.a) + ' apart.'};
  return {sum: v.a + ' − ' + v.b + ' = ' + r.difference,
    rows: [['Exchange', r.exchange ? 'yes: swap 1 ten for 10 ones' : 'not needed'], ['Subtract the ones', (v.a % 10 + (r.exchange ? 10 : 0)) + ' − ' + (v.b % 10) + ' = ' + r.ones],
      ['Subtract the tens', (Math.floor(v.a / 10) - (r.exchange ? 1 : 0)) + ' − ' + Math.floor(v.b / 10) + ' = ' + r.tens], ['Check by adding', r.difference + ' + ' + v.b + ' = ' + v.a]],
    result: 'Addition undoes subtraction, so you can always check: ' + r.difference + ' + ' + v.b + ' = ' + v.a + '.'};
}
function start() {
  const ids = ["a", "b"];
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

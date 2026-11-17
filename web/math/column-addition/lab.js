'use strict';
const Model = {
  add(a, b) {
    const ones = a % 10 + b % 10, carry = ones >= 10 ? 1 : 0, tens = Math.floor(a / 10) + Math.floor(b / 10) + carry;
    return {sum: a + b, ones, carry, onesDigit: ones % 10, tens};
  },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.add(v.a, v.b), p = Kit.plot(canvas, {x: [-8, 208], y: [-1.2, 1.6], grid: false});
  axis(p, 0, 200, 20); p.arrow(0, 0.5, v.a, 0.5, '#215783'); p.arrow(v.a, 1, r.sum, 1, '#963d18'); p.point(r.sum, 0, '#172533', 6);
  p.text(String(v.a), v.a / 2, 0.5, '#215783', -8, -8); p.text('+ ' + v.b, v.a + v.b / 2, 1, '#963d18', -12, -8);
  return {sum: v.a + ' + ' + v.b + ' = ' + r.sum,
    rows: [['Add the ones', (v.a % 10) + ' + ' + (v.b % 10) + ' = ' + r.ones], ['Carry', r.carry ? 'write ' + r.onesDigit + ', carry 1 ten' : 'nothing to carry'],
      ['Add the tens', Math.floor(v.a / 10) + ' + ' + Math.floor(v.b / 10) + (r.carry ? ' + 1' : '') + ' = ' + r.tens], ['Answer', r.tens + ' tens and ' + r.onesDigit + ' ones = ' + r.sum]],
    result: 'Adding in either order gives the same answer: ' + v.b + ' + ' + v.a + ' is also ' + r.sum + '.'};
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

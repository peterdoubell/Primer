'use strict';
const Model = {
  SIGNS: {add: '+', subtract: '−', multiply: '×'},
  // Work in whole hundredths so the answers are exact.
  calc(a, b, op) { const A = Math.round(a * 100), B = Math.round(b * 100); return op === 'add' ? (A + B) / 100 : op === 'subtract' ? (A - B) / 100 : Math.round(A * B) / 10000; },
  round: (value, places) => Math.round(value * 10 ** places + (value < 0 ? -1e-9 : 1e-9)) / 10 ** places,
  places(value) { const text = String(Math.round(Math.abs(value) * 10000) / 10000); return text.includes('.') ? text.split('.')[1].length : 0; },
  show: value => String(Math.round(value * 10000) / 10000).replace('-', '−'),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.calc(v.a, v.b, v.op), max = v.op === 'multiply' ? 100 : 20, min = v.op === 'subtract' ? -10 : 0, p = Kit.plot(canvas, {x: [min - max * 0.03, max * 1.03], y: [-1.2, 1.6], grid: false});
  axis(p, min, max, (max - min) / 10); p.point(v.a, 0, '#215783', 6); p.point(v.b, 0, '#3c7a4b', 6); p.point(r, 0, '#963d18', 8); p.text(Model.show(r), r, 0, '#963d18', -10, -14);
  return {sum: Model.show(v.a) + ' ' + Model.SIGNS[v.op] + ' ' + Model.show(v.b) + ' = ' + Model.show(r),
    rows: [['Answer', Model.show(r)], ['Decimal places in the answer', String(Model.places(r))], ['Rounded to one decimal place', Model.show(Model.round(r, 1))], ['Rounded to the nearest whole number', Model.show(Model.round(r, 0))]],
    result: v.op === 'multiply' ? 'Multiply as whole numbers, then place the point: the answer has as many decimal places as the two numbers together (before any end zeros are dropped).' : 'Line up the decimal points so tenths sit under tenths and hundredths under hundredths, then ' + v.op + ' as usual.'};
}
function start() {
  const ids = ["a", "op", "b"];
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

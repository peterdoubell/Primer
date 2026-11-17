'use strict';
const Model = {
  apply: (a, op, b) => op === 'add' ? a + b : op === 'subtract' ? a - b : a * b,
  // Subtracting b is the same move as adding its opposite.
  move: (op, b) => op === 'add' ? b : -b,
  sign: n => n > 0 ? 'positive' : n < 0 ? 'negative' : 'zero',
};
function start() {
  const canvas = Kit.get('graph'), show = n => n < 0 ? '(−' + Math.abs(n) + ')' : String(n);
  function draw() {
    const a = Kit.num('a'), b = Kit.num('b'), op = Kit.get('op').value, result = Model.apply(a, op, b);
    Kit.say('a', a, 'a = ' + a); Kit.say('b', b, 'b = ' + b);
    const span = Math.max(12, Math.abs(result) + 2, Math.abs(a) + 2);
    const p = Kit.plot(canvas, {x: [-span, span], y: [-1, 3], grid: false});
    p.line(-span, 0, span, 0, '#172533', 2);
    for (const v of Kit.ticks(-span, span, 12)) { p.line(v, -0.08, v, 0.08, '#172533', 1.5); p.text(String(v), v, 0, '#172533', -6, 24); }
    const symbol = {add: '+', subtract: '−', multiply: '×'}[op];
    let note;
    if (op === 'multiply') {
      const step = a, count = Math.abs(b);
      for (let i = 0; i < count; i++) p.arrow((b < 0 ? -1 : 1) * step * i, 1 + (i % 2) * 0.5, (b < 0 ? -1 : 1) * step * (i + 1), 1 + (i % 2) * 0.5, '#215783');
      note = count + ' jumps of ' + show(a) + (b < 0 ? ', taken in the opposite direction because b is negative' : '') + '. A negative times a negative is positive; one negative factor gives a negative product.';
    } else {
      p.arrow(0, 1, a, 1, '#215783'); p.arrow(a, 1.7, a + Model.move(op, b), 1.7, '#963d18');
      note = 'Start at ' + show(a) + ' (blue), then move ' + Math.abs(b) + ' to the ' + (Model.move(op, b) >= 0 ? 'right' : 'left') + ' (orange).' + (op === 'subtract' ? ' Subtracting ' + show(b) + ' is the same as adding ' + show(-b) + '.' : '');
    }
    p.point(result, 0, '#172533', 7);
    Kit.get('sum').textContent = show(a) + ' ' + symbol + ' ' + show(b) + ' = ' + result;
    Kit.rows(Kit.get('rows'), op === 'multiply'
      ? [['Sizes multiplied', Math.abs(a) + ' × ' + Math.abs(b) + ' = ' + Math.abs(result)], ['Negative factors', String((a < 0) + (b < 0))], ['Sign of the product', Model.sign(result)]]
      : [['Start', show(a)], ['Move', (Model.move(op, b) >= 0 ? '+' : '−') + Math.abs(b)], ['Written as an addition', show(a) + ' + ' + show(Model.move(op, b)) + ' = ' + result]]);
    Kit.get('result').textContent = note + ' The answer, ' + result + ', is ' + Model.sign(result) + '.';
    canvas.setAttribute('aria-label', 'Number line showing ' + Kit.get('sum').textContent + '. ' + note);
  }
  Kit.bind(['a', 'b', 'op'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

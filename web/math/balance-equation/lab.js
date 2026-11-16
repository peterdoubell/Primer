'use strict';
const Model = {
  // a·x + b = c. Undo the addition first, then the multiplication.
  solve(a, b, c) {
    const term = b < 0 ? 'Add ' + (-b) + ' to both sides' : b > 0 ? 'Subtract ' + b + ' from both sides' : 'Nothing to undo';
    return {x: (c - b) / a, steps: [
      {left: a + 'x ' + (b < 0 ? '− ' + (-b) : '+ ' + b), right: String(c), rule: 'Equation'},
      {left: a + 'x', right: String(c - b), rule: term},
      {left: 'x', right: String((c - b) / a), rule: 'Divide both sides by ' + a}]};
  },
  check: (a, b, x) => a * x + b,
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d');
  function draw() {
    const a = Kit.num('a'), b = Kit.num('b'), x = Kit.num('x'), c = Model.check(a, b, x), s = Model.solve(a, b, c);
    Kit.say('a', a, 'a = ' + a); Kit.say('b', b, 'b = ' + b); Kit.say('x', x, 'hidden x = ' + x);
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '16px system-ui, sans-serif';
    ctx.strokeStyle = '#172533'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(90, 200); ctx.lineTo(630, 200); ctx.stroke();
    ctx.fillStyle = '#6b7780'; ctx.beginPath(); ctx.moveTo(360, 200); ctx.lineTo(335, 250); ctx.lineTo(385, 250); ctx.fill();
    for (let i = 0; i < a; i++) { ctx.fillStyle = '#215783'; ctx.fillRect(100 + i * 27, 160, 24, 36); ctx.fillStyle = '#fff'; ctx.fillText('x', 107 + i * 27, 184); }
    ctx.fillStyle = '#172533'; ctx.fillText(b === 0 ? '' : (b > 0 ? '+ ' : '− ') + Math.abs(b), 110 + a * 27, 184);
    ctx.fillStyle = '#c9a26b'; ctx.fillRect(470, 150, 110, 46); ctx.fillStyle = '#172533'; ctx.fillText(String(c), 515, 180);
    ctx.fillText('left side: ' + s.steps[0].left, 100, 130); ctx.fillText('right side: ' + c, 470, 130);
    Kit.rows(Kit.get('rows'), s.steps.map(step => [step.rule, step.left + ' = ' + step.right]));
    Kit.get('result').textContent = 'x = ' + Kit.fmt(s.x) + '. Check: ' + a + ' × ' + Kit.fmt(s.x) + (b < 0 ? ' − ' + (-b) : ' + ' + b) + ' = ' + Model.check(a, b, s.x) + '. Whatever is done to one side must be done to the other, so the scale stays level.';
    canvas.setAttribute('aria-label', 'Balance with ' + s.steps[0].left + ' on the left and ' + c + ' on the right.');
  }
  Kit.bind(['a', 'b', 'x'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

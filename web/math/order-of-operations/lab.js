'use strict';
const Model = {
  tokens: text => text.match(/\d+(?:\.\d+)?|[-+×÷^()]/g).map(t => /\d/.test(t) ? Number(t) : t),
  apply: (a, op, b) => ({'+': a + b, '-': a - b, '×': a * b, '÷': a / b, '^': a ** b})[op],
  show: list => list.join(' ').replace(/\( /g, '(').replace(/ \)/g, ')'),
  // One reduction at a time: brackets first, then powers, then × and ÷ left to right, then + and −.
  steps(text) {
    let list = Model.tokens(text); const out = [{text: Model.show(list), rule: 'Start'}];
    for (let guard = 0; guard < 60 && list.length > 1; guard++) {
      let lo = 0, hi = list.length, inside = false;
      const close = list.indexOf(')');
      if (close >= 0) { hi = close; lo = list.lastIndexOf('(', close) + 1; inside = true; }
      if (inside && hi - lo === 1) { list.splice(lo - 1, 3, list[lo]); out.push({text: Model.show(list), rule: 'Remove the brackets'}); continue; }
      const part = list.slice(lo, hi);
      let at = part.lastIndexOf('^'), rule = 'Power';
      if (at < 0) { at = part.findIndex(t => t === '×' || t === '÷'); rule = 'Multiply or divide, left to right'; }
      if (at < 0) { at = part.findIndex(t => t === '+' || t === '-'); rule = 'Add or subtract, left to right'; }
      list.splice(lo + at - 1, 3, Model.apply(part[at - 1], part[at], part[at + 1]));
      out.push({text: Model.show(list), rule: (inside ? 'Inside the brackets: ' : '') + rule});
    }
    return out;
  },
  value: text => Model.steps(text).pop().text === undefined ? NaN : Number(Model.steps(text).pop().text),
  // The common mistake: working strictly left to right, ignoring precedence and brackets.
  leftToRight(text) { const list = Model.tokens(text).filter(t => t !== '(' && t !== ')'); let total = list[0]; for (let i = 1; i < list.length; i += 2) total = Model.apply(total, list[i], list[i + 1]); return total; },
};
function start() {
  function draw() {
    const text = Kit.get('expression').value, steps = Model.steps(text), answer = Number(steps[steps.length - 1].text), naive = Model.leftToRight(text);
    Kit.rows(Kit.get('rows'), steps.map((s, i) => [i ? 'Step ' + i : 'Expression', s.text, s.rule]));
    Kit.get('result').textContent = 'The value is ' + Kit.fmt(answer, 8) + '. ' + (naive === answer
      ? 'Here working left to right happens to give the same answer.'
      : 'Working strictly left to right would give ' + Kit.fmt(naive, 8) + ', which is wrong: brackets, then powers, then multiplication and division, then addition and subtraction.');
  }
  Kit.bind(['expression'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

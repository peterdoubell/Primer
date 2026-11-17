'use strict';
const Model = {
  ITEMS: [{"name": "b", "cat": "Tall", "cols": ["Tall", "reaches up to the top line"]}, {"name": "d", "cat": "Tall", "cols": ["Tall", "reaches up to the top line"]}, {"name": "f", "cat": "Tall", "cols": ["Tall", "reaches up to the top line"]}, {"name": "h", "cat": "Tall", "cols": ["Tall", "reaches up to the top line"]}, {"name": "k", "cat": "Tall", "cols": ["Tall", "reaches up to the top line"]}, {"name": "l", "cat": "Tall", "cols": ["Tall", "reaches up to the top line"]}, {"name": "t", "cat": "Tall", "cols": ["Tall", "reaches up to the top line"]}, {"name": "a", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "c", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "e", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "i", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "m", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "n", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "o", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "r", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "s", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "u", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "v", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "w", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "x", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "z", "cat": "Small", "cols": ["Small", "fits between the base line and the middle line"]}, {"name": "g", "cat": "Tail", "cols": ["Tail", "hangs below the base line"]}, {"name": "j", "cat": "Tail", "cols": ["Tail", "hangs below the base line"]}, {"name": "p", "cat": "Tail", "cols": ["Tail", "hangs below the base line"]}, {"name": "q", "cat": "Tail", "cols": ["Tail", "hangs below the base line"]}, {"name": "y", "cat": "Tail", "cols": ["Tail", "hangs below the base line"]}],
  CATEGORIES: ["Tall", "Small", "Tail"],
  QUIZ: [["b", "Tall"], ["d", "Tall"], ["f", "Tall"], ["h", "Tall"], ["k", "Tall"], ["l", "Tall"], ["t", "Tall"], ["a", "Small"], ["c", "Small"], ["e", "Small"], ["i", "Small"], ["m", "Small"], ["n", "Small"], ["o", "Small"], ["r", "Small"], ["s", "Small"], ["u", "Small"], ["v", "Small"], ["w", "Small"], ["x", "Small"], ["z", "Small"], ["g", "Tail"], ["j", "Tail"], ["p", "Tail"], ["q", "Tail"], ["y", "Tail"]],
  PROMPT: "Which family does the letter “{name}” belong to?",
  category: name => (Model.ITEMS.find(item => item.name === name) || {}).cat,
  inCategory: cat => Model.ITEMS.filter(item => item.cat === cat).map(item => item.name),
  // Round n asks about one quiz entry and offers up to four categories, the right one among them.
  round(n) {
    const quiz = Model.QUIZ, cats = Model.CATEGORIES, entry = quiz[(n * 7) % quiz.length];
    const size = Math.min(4, cats.length), at = cats.indexOf(entry[1]), first = (at - (n * 7 + (n >> 1)) % size + cats.length) % cats.length;
    // An entry may carry its own options, for questions whose choices come from the sentence itself.
    const options = entry[2] || Array.from({length: size}, (_, i) => cats[(first + i) % cats.length]);
    return {text: entry[0], prompt: Model.PROMPT.replace('{name}', entry[0]), options, answer: entry[1]};
  },
  check: (n, choice) => Model.round(n).answer === choice,
};
function start() {
  const show = Kit.get('show'); let n = 0, score = 0;
  show.add(new Option('Everything', ''));
  if (true) Model.CATEGORIES.forEach(cat => show.add(new Option(cat, cat)));
  function ask() {
    const round = Model.round(n);
    Kit.get('prompt').textContent = round.prompt;
    Kit.get('choices').replaceChildren(...round.options.map(option => {
      const button = document.createElement('button'); button.textContent = option;
      button.addEventListener('click', () => {
        const right = option === round.answer; if (right) score++;
        Kit.get('feedback').textContent = (right ? 'Yes. ' : 'Not quite. ') + 'The answer is ' + round.answer + '. Score ' + score + ' of ' + (n + 1) + '.';
        n++; ask();
      });
      return button;
    }));
  }
  function draw() {
    const shown = Model.ITEMS.filter(item => !show.value || item.cat === show.value);
    Kit.rows(Kit.get('rows'), shown.map(item => [item.name, ...item.cols]));
    const p = Kit.plot(Kit.get('graph'), {x: [0, 10], y: [-1.6, 2.6], grid: false});
    p.line(0, 2, 10, 2, '#9aa6ae', 1.5, [6, 6]); p.line(0, 1, 10, 1, '#9aa6ae', 1.5, [6, 6]); p.line(0, 0, 10, 0, '#172533', 2.5); p.line(0, -1, 10, -1, '#9aa6ae', 1.5, [6, 6]);
    p.text('top line', 8.2, 2, '#4a5560', 0, -6); p.text('middle line', 8.2, 1, '#4a5560', 0, -6); p.text('base line', 8.2, 0, '#172533', 0, -6); p.text('tail line', 8.2, -1, '#4a5560', 0, -6);
    const boxes = {Tall: [0, 2], Small: [0, 1], Tail: [-1, 1]}, sample = {Tall: 'h', Small: 'a', Tail: 'g'};
    Object.keys(boxes).forEach((family, i) => { const [from, to] = boxes[family], x = 1 + i * 2.4, on = !show.value || show.value === family, colour = on ? '#215783' : '#c3ccd2';
      p.line(x, from, x, to, colour, 14); p.text(family + ' (' + sample[family] + ')', x, 2, on ? '#172533' : '#7a8790', -22, -22); });
    Kit.get('result').textContent = "Keep small letters the same height, make tall letters clearly taller, and let tails drop below the line.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

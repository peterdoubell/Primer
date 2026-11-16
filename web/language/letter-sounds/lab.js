'use strict';
const Model = {
  ITEMS: [{"name": "s", "cat": "s", "cols": ["sss, like a snake", "sun"]}, {"name": "m", "cat": "m", "cols": ["mmm", "moon"]}, {"name": "t", "cat": "t", "cols": ["t, a quick tap", "top"]}, {"name": "p", "cat": "p", "cols": ["p, a puff of air", "pig"]}, {"name": "b", "cat": "b", "cols": ["b", "bat"]}, {"name": "f", "cat": "f", "cols": ["fff", "fish"]}, {"name": "d", "cat": "d", "cols": ["d", "dog"]}, {"name": "n", "cat": "n", "cols": ["nnn", "net"]}, {"name": "h", "cat": "h", "cols": ["h, a breath", "hat"]}, {"name": "l", "cat": "l", "cols": ["lll", "leg"]}, {"name": "r", "cat": "r", "cols": ["rrr", "red"]}, {"name": "c", "cat": "c", "cols": ["k, as in cat", "cup"]}],
  CATEGORIES: ["s", "m", "t", "p", "b", "f", "d", "n", "h", "l", "r", "c"],
  QUIZ: [["sock", "s"], ["map", "m"], ["ten", "t"], ["pan", "p"], ["bed", "b"], ["fan", "f"], ["dig", "d"], ["nut", "n"], ["hen", "h"], ["log", "l"], ["rug", "r"], ["cat", "c"], ["sit", "s"], ["mud", "m"], ["tap", "t"], ["pot", "p"]],
  PROMPT: "Which letter starts the word “{name}”?",
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
  if (false) Model.CATEGORIES.forEach(cat => show.add(new Option(cat, cat)));
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

    Kit.get('result').textContent = "Say the word slowly and listen to the first sound. Then find the letter that makes that sound.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

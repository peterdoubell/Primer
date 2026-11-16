'use strict';
const Model = {
  ITEMS: [{"name": "enormous", "cat": "tiny", "cols": ["very big", "huge", "tiny"]}, {"name": "ancient", "cat": "modern", "cols": ["very old", "old", "modern"]}, {"name": "brave", "cat": "fearful", "cols": ["ready to face danger", "bold", "fearful"]}, {"name": "swift", "cat": "slow", "cols": ["moving fast", "quick", "slow"]}, {"name": "gloomy", "cat": "cheerful", "cols": ["dark or sad", "dismal", "cheerful"]}, {"name": "fragile", "cat": "sturdy", "cols": ["easily broken", "delicate", "sturdy"]}, {"name": "generous", "cat": "selfish", "cols": ["glad to give", "giving", "selfish"]}, {"name": "silent", "cat": "noisy", "cols": ["making no sound", "quiet", "noisy"]}, {"name": "expand", "cat": "shrink", "cols": ["to grow larger", "grow", "shrink"]}, {"name": "scarce", "cat": "plentiful", "cols": ["hard to find", "rare", "plentiful"]}],
  CATEGORIES: ["tiny", "modern", "fearful", "slow", "cheerful", "sturdy", "selfish", "noisy", "shrink", "plentiful"],
  QUIZ: [["enormous", "tiny"], ["ancient", "modern"], ["brave", "fearful"], ["swift", "slow"], ["gloomy", "cheerful"], ["fragile", "sturdy"], ["generous", "selfish"], ["silent", "noisy"], ["expand", "shrink"], ["scarce", "plentiful"]],
  PROMPT: "Which word is the opposite of “{name}”?",
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

    Kit.get('result').textContent = "A new word sticks when you use it. Say it in a sentence of your own today.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

'use strict';
const Model = {
  ITEMS: [{"name": "a diary", "cat": "Primary", "cols": ["Primary", "written by someone who was there"]}, {"name": "a letter", "cat": "Primary", "cols": ["Primary", "written at the time by a person involved"]}, {"name": "a photograph", "cat": "Primary", "cols": ["Primary", "made at the event itself"]}, {"name": "an interview with a witness", "cat": "Primary", "cols": ["Primary", "first-hand account"]}, {"name": "a biography", "cat": "Secondary", "cols": ["Secondary", "written later, using primary sources"]}, {"name": "a history book", "cat": "Secondary", "cols": ["Secondary", "explains and interprets the evidence"]}, {"name": "a documentary film", "cat": "Secondary", "cols": ["Secondary", "tells the story from gathered evidence"]}, {"name": "an encyclopedia", "cat": "Tertiary", "cols": ["Tertiary", "sums up what secondary sources say"]}, {"name": "a dictionary", "cat": "Tertiary", "cols": ["Tertiary", "a reference list drawn from other works"]}, {"name": "an almanac", "cat": "Tertiary", "cols": ["Tertiary", "collected facts and figures"]}],
  CATEGORIES: ["Primary", "Secondary", "Tertiary"],
  QUIZ: [["a diary", "Primary"], ["a letter", "Primary"], ["a photograph", "Primary"], ["an interview with a witness", "Primary"], ["a biography", "Secondary"], ["a history book", "Secondary"], ["a documentary film", "Secondary"], ["an encyclopedia", "Tertiary"], ["a dictionary", "Tertiary"], ["an almanac", "Tertiary"]],
  PROMPT: "What kind of source is {name}?",
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

    Kit.get('result').textContent = "Checking a source, in order: 1. Who made it? 2. When? 3. What evidence does it give? 4. Does a second, independent source agree?";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

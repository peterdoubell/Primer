'use strict';
const Model = {
  ITEMS: [{"name": "Who", "cat": "Who", "cols": ["a person", "Who is at the door?"]}, {"name": "What", "cat": "What", "cols": ["a thing or an action", "What are you making?"]}, {"name": "Where", "cat": "Where", "cols": ["a place", "Where is my hat?"]}, {"name": "When", "cat": "When", "cols": ["a time", "When is lunch?"]}, {"name": "Why", "cat": "Why", "cols": ["a reason", "Why is the sky dark?"]}, {"name": "How", "cat": "How", "cols": ["the way something is done", "How do you tie a bow?"]}],
  CATEGORIES: ["Who", "What", "Where", "When", "Why", "How"],
  QUIZ: [["My grandma", "Who"], ["At the park", "Where"], ["After dinner", "When"], ["Because it is raining", "Why"], ["A red kite", "What"], ["By mixing blue and yellow", "How"], ["The bus driver", "Who"], ["Under the bed", "Where"], ["On Saturday", "When"], ["Because I was tired", "Why"], ["A sandwich", "What"], ["By pedalling fast", "How"]],
  PROMPT: "The answer is “{name}”. Which question word was asked?",
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

    Kit.get('result').textContent = "Listen to the answer. A person answers Who, a place answers Where, a time answers When, and a reason answers Why.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

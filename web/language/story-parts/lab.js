'use strict';
const Model = {
  ITEMS: [{"name": "Beginning", "cat": "Beginning", "cols": ["who the story is about and where they are", "Once upon a time; One morning"]}, {"name": "Middle", "cat": "Middle", "cols": ["what happens, and the problem", "But then; Suddenly"]}, {"name": "End", "cat": "End", "cols": ["how the problem is solved", "At last; In the end"]}],
  CATEGORIES: ["Beginning", "Middle", "End"],
  QUIZ: [["Once upon a time a little fox lived by a river.", "Beginning"], ["But then the river began to rise.", "Middle"], ["At last the fox was safe and warm at home.", "End"], ["One morning Mina found a tiny door in the garden wall.", "Beginning"], ["Suddenly the door creaked open and a mouse ran out.", "Middle"], ["In the end Mina and the mouse were friends.", "End"], ["There was once a baker who loved to sing.", "Beginning"], ["Then one day all the bread went missing.", "Middle"], ["So the baker sang, and everyone shared the bread happily ever after.", "End"]],
  PROMPT: "Which part of the story is this? “{name}”",
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

    Kit.get('result').textContent = "Ask three questions after any story: who was it about, where were they, and what happened?";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

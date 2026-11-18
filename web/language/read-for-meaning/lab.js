'use strict';
const Model = {
  ITEMS: [{"name": "The cat sat on the mat.", "cat": "Who", "cols": ["the cat", "sat", "on the mat"]}, {"name": "Ben ran to the shop.", "cat": "Who", "cols": ["Ben", "ran", "to the shop"]}, {"name": "A frog hid under a leaf.", "cat": "Who", "cols": ["a frog", "hid", "under a leaf"]}, {"name": "Mum reads in the garden.", "cat": "Who", "cols": ["Mum", "reads", "in the garden"]}, {"name": "The dog swam in the pond.", "cat": "Who", "cols": ["the dog", "swam", "in the pond"]}],
  CATEGORIES: ["Who", "the cat", "Ben", "a frog", "Mum", "the dog", "on the mat", "to the shop", "under a leaf", "in the garden", "in the pond", "sat", "ran", "hid", "reads", "swam"],
  QUIZ: [["“The cat sat on the mat.” Who sat?", "the cat", ["the cat", "sat", "on the mat"]], ["“Ben ran to the shop.” Who ran?", "Ben", ["Ben", "ran", "to the shop"]], ["“A frog hid under a leaf.” Who hid?", "a frog", ["a frog", "hid", "under a leaf"]], ["“Mum reads in the garden.” Who reads?", "Mum", ["Mum", "reads", "in the garden"]], ["“The dog swam in the pond.” Who swam?", "the dog", ["the dog", "swam", "in the pond"]], ["“The cat sat on the mat.” Where did the cat sit?", "on the mat", ["the cat", "sat", "on the mat"]], ["“Ben ran to the shop.” Where did Ben run?", "to the shop", ["Ben", "ran", "to the shop"]], ["“A frog hid under a leaf.” Where did the frog hide?", "under a leaf", ["a frog", "hid", "under a leaf"]], ["“Mum reads in the garden.” Where does Mum read?", "in the garden", ["Mum", "reads", "in the garden"]], ["“The dog swam in the pond.” Where did the dog swim?", "in the pond", ["the dog", "swam", "in the pond"]], ["“The cat sat on the mat.” What did the cat do?", "sat", ["the cat", "sat", "on the mat"]], ["“Ben ran to the shop.” What did Ben do?", "ran", ["Ben", "ran", "to the shop"]], ["“A frog hid under a leaf.” What did the frog do?", "hid", ["a frog", "hid", "under a leaf"]], ["“Mum reads in the garden.” What does Mum do?", "reads", ["Mum", "reads", "in the garden"]], ["“The dog swam in the pond.” What did the dog do?", "swam", ["the dog", "swam", "in the pond"]]],
  PROMPT: "{name}",
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

    Kit.get('result').textContent = "Read the sentence, then answer from the sentence itself. If you are not sure, read it again.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

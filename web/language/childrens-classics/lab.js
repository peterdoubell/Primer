'use strict';
const Model = {
  ITEMS: [{"name": "Alice's Adventures in Wonderland", "cat": "Lewis Carroll", "cols": ["Lewis Carroll", "1865", "A girl follows a rabbit into a world of nonsense."], "year": 1865}, {"name": "The Tale of Peter Rabbit", "cat": "Beatrix Potter", "cols": ["Beatrix Potter", "1902", "A rabbit sneaks into Mr McGregor's garden."], "year": 1902}, {"name": "The Wind in the Willows", "cat": "Kenneth Grahame", "cols": ["Kenneth Grahame", "1908", "Mole, Rat, Badger and the reckless Mr Toad."], "year": 1908}, {"name": "Winnie-the-Pooh", "cat": "A. A. Milne", "cols": ["A. A. Milne", "1926", "A bear and his friends in the Hundred Acre Wood."], "year": 1926}, {"name": "Charlotte's Web", "cat": "E. B. White", "cols": ["E. B. White", "1952", "A spider saves a pig by writing in her web."], "year": 1952}, {"name": "The Cat in the Hat", "cat": "Dr. Seuss", "cols": ["Dr. Seuss", "1957", "A cat in a striped hat turns a rainy day upside down."], "year": 1957}, {"name": "Where the Wild Things Are", "cat": "Maurice Sendak", "cols": ["Maurice Sendak", "1963", "Max sails to an island of wild things."], "year": 1963}, {"name": "The Very Hungry Caterpillar", "cat": "Eric Carle", "cols": ["Eric Carle", "1969", "A caterpillar eats through the week and becomes a butterfly."], "year": 1969}],
  CATEGORIES: ["Lewis Carroll", "Beatrix Potter", "Kenneth Grahame", "A. A. Milne", "E. B. White", "Dr. Seuss", "Maurice Sendak", "Eric Carle"],
  QUIZ: [["Alice's Adventures in Wonderland", "Lewis Carroll"], ["The Tale of Peter Rabbit", "Beatrix Potter"], ["The Wind in the Willows", "Kenneth Grahame"], ["Winnie-the-Pooh", "A. A. Milne"], ["Charlotte's Web", "E. B. White"], ["The Cat in the Hat", "Dr. Seuss"], ["Where the Wild Things Are", "Maurice Sendak"], ["The Very Hungry Caterpillar", "Eric Carle"]],
  PROMPT: "Who wrote “{name}”?",
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
    const years = Model.ITEMS.map(item => item.year), lo = Math.min(...years), hi = Math.max(...years), pad = Math.max(2, (hi - lo) * 0.08), count = Model.ITEMS.length;
    const p = Kit.plot(Kit.get('graph'), {x: [lo - pad, hi + pad], y: [-0.6, count + 1], grid: false});
    p.line(lo - pad, 0, hi + pad, 0, '#172533', 1.5);
    for (const year of Kit.ticks(lo - pad, hi + pad)) { p.line(year, 0, year, count + 0.6, '#d8dfe4', 1); p.text(String(year), year, 0, '#172533', -14, 20); }
    p.text('Year', hi + pad, 0, '#172533', -34, 40);
    Model.ITEMS.forEach((item, i) => {
      const on = shown.includes(item), y = count - i, left = item.year > (lo + hi) / 2;
      p.point(item.year, y, on ? '#963d18' : '#9aa6ae', 6, !on);
      p.text(item.name, item.year, y, on ? '#172533' : '#7a8790', left ? -10 - p.ctx.measureText(item.name).width : 10, 5);
    });
    Kit.get('result').textContent = "When you finish a book, tell someone who it was about, what happened, and which part you liked best.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

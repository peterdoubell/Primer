'use strict';
const Model = {
  ITEMS: [{"name": "Iliad", "cat": "Homer", "cols": ["Homer", "Greek", "about 8th century BCE"], "year": -750}, {"name": "Odyssey", "cat": "Homer", "cols": ["Homer", "Greek", "about 8th century BCE"], "year": -725}, {"name": "Theogony", "cat": "Hesiod", "cols": ["Hesiod", "Greek", "about 700 BCE"], "year": -700}, {"name": "Oresteia", "cat": "Aeschylus", "cols": ["Aeschylus", "Greek", "458 BCE"], "year": -458}, {"name": "Medea", "cat": "Euripides", "cols": ["Euripides", "Greek", "431 BCE"], "year": -431}, {"name": "Oedipus the King", "cat": "Sophocles", "cols": ["Sophocles", "Greek", "about 429 BCE"], "year": -429}, {"name": "Aeneid", "cat": "Virgil", "cols": ["Virgil", "Latin", "29–19 BCE"], "year": -19}, {"name": "Metamorphoses", "cat": "Ovid", "cols": ["Ovid", "Latin", "about 8 CE"], "year": 8}],
  CATEGORIES: ["Homer", "Hesiod", "Aeschylus", "Euripides", "Sophocles", "Virgil", "Ovid"],
  QUIZ: [["Iliad", "Homer"], ["Odyssey", "Homer"], ["Theogony", "Hesiod"], ["Oresteia", "Aeschylus"], ["Medea", "Euripides"], ["Oedipus the King", "Sophocles"], ["Aeneid", "Virgil"], ["Metamorphoses", "Ovid"]],
  PROMPT: "Who composed the “{name}”?",
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
    Kit.get('result').textContent = "Virgil wrote the Aeneid in answer to Homer: its first half echoes the Odyssey and its second half the Iliad.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

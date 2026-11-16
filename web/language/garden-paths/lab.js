'use strict';
const Model = {
  ITEMS: [{"name": "The old man the boats.", "cat": "man", "cols": ["“old man” read as adjective and noun", "“the old” is the subject; “man” is the verb"]}, {"name": "The horse raced past the barn fell.", "cat": "fell", "cols": ["“raced” read as the main verb", "“raced past the barn” is a reduced relative clause; “fell” is the main verb"]}, {"name": "The complex houses married and single soldiers.", "cat": "houses", "cols": ["“complex houses” read as adjective and noun", "“the complex” is the subject; “houses” is the verb"]}, {"name": "Fat people eat accumulates.", "cat": "accumulates", "cols": ["“fat people” read as adjective and noun", "“fat (that) people eat” is the subject; “accumulates” is the verb"]}, {"name": "The cotton clothing is made of grows in Mississippi.", "cat": "grows", "cols": ["“cotton clothing” read as one noun phrase", "“the cotton (that) clothing is made of” is the subject"]}, {"name": "While the man hunted the deer ran into the woods.", "cat": "ran", "cols": ["“the deer” read as the object of “hunted”", "“the deer” is the subject of “ran”"]}],
  CATEGORIES: ["man", "fell", "houses", "accumulates", "grows", "ran"],
  QUIZ: [["The old man the boats.", "man", ["old", "man", "the", "boats"]], ["The horse raced past the barn fell.", "fell", ["horse", "raced", "barn", "fell"]], ["The complex houses married and single soldiers.", "houses", ["complex", "houses", "married", "soldiers"]], ["Fat people eat accumulates.", "accumulates", ["Fat", "people", "eat", "accumulates"]], ["The cotton clothing is made of grows in Mississippi.", "grows", ["cotton", "clothing", "made", "grows"]], ["While the man hunted the deer ran into the woods.", "ran", ["hunted", "deer", "ran", "woods"]]],
  PROMPT: "At which word must the reader rethink “{name}”?",
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

    Kit.get('result').textContent = "The parser commits early instead of waiting. Minimal attachment and late closure are two proposed principles for which analysis it tries first.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

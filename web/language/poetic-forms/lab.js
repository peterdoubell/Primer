'use strict';
const Model = {
  ITEMS: [{"name": "Sonnet", "cat": "Italian", "cols": ["Italian", "14 lines; a turn of thought part-way through"]}, {"name": "Haiku", "cat": "Japanese", "cols": ["Japanese", "17 sound units in a 5–7–5 pattern; a seasonal word"]}, {"name": "Tanka", "cat": "Japanese", "cols": ["Japanese", "31 sound units in a 5–7–5–7–7 pattern"]}, {"name": "Ghazal", "cat": "Arabic and Persian", "cols": ["Arabic and Persian", "self-contained couplets sharing a rhyme and refrain"]}, {"name": "Villanelle", "cat": "French", "cols": ["French", "19 lines; two refrains that return in turn"]}, {"name": "Terza rima", "cat": "Italian", "cols": ["Italian", "three-line stanzas chained by rhyme: aba bcb cdc"]}, {"name": "Alliterative verse", "cat": "Old English and Germanic", "cols": ["Old English and Germanic", "two half-lines bound by repeated starting sounds"]}, {"name": "Rubai", "cat": "Arabic and Persian", "cols": ["Arabic and Persian", "a four-line stanza, usually rhymed aaba"]}],
  CATEGORIES: ["Italian", "Japanese", "Arabic and Persian", "French", "Old English and Germanic"],
  QUIZ: [["Sonnet", "Italian"], ["Haiku", "Japanese"], ["Tanka", "Japanese"], ["Ghazal", "Arabic and Persian"], ["Villanelle", "French"], ["Terza rima", "Italian"], ["Alliterative verse", "Old English and Germanic"], ["Rubai", "Arabic and Persian"]],
  PROMPT: "In which tradition did the {name} arise?",
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

    Kit.get('result').textContent = "When a form crosses languages it changes. The English sonnet rhymes differently from the Italian, and English haiku count syllables where Japanese counts shorter sound units.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

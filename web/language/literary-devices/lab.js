'use strict';
const Model = {
  ITEMS: [{"name": "Simile", "cat": "Simile", "cols": ["compares using “like” or “as”", "“O my Luve is like a red, red rose” — Robert Burns"]}, {"name": "Metaphor", "cat": "Metaphor", "cols": ["says one thing is another", "“All the world’s a stage” — William Shakespeare"]}, {"name": "Personification", "cat": "Personification", "cols": ["gives human action to something not human", "“Because I could not stop for Death – He kindly stopped for me” — Emily Dickinson"]}, {"name": "Alliteration", "cat": "Alliteration", "cols": ["repeats a starting sound", "“The fair breeze blew, the white foam flew” — Samuel Taylor Coleridge"]}, {"name": "Hyperbole", "cat": "Hyperbole", "cols": ["exaggerates for effect", "“I’ve told you a million times.”"]}, {"name": "Irony", "cat": "Irony", "cols": ["says the opposite of what is meant, or shows the opposite of what is expected", "A fire station burns down."]}],
  CATEGORIES: ["Simile", "Metaphor", "Personification", "Alliteration", "Hyperbole", "Irony"],
  QUIZ: [["Her smile was as bright as the morning.", "Simile"], ["Time is a thief.", "Metaphor"], ["The wind whispered through the pines.", "Personification"], ["Peter Piper picked a peck of pickled peppers.", "Alliteration"], ["This bag weighs a ton.", "Hyperbole"], ["“What lovely weather,” she said, as the hail broke the window.", "Irony"], ["He ran like the wind.", "Simile"], ["The classroom was a zoo.", "Metaphor"], ["The old house groaned and sighed.", "Personification"], ["Silver ships sailed slowly south.", "Alliteration"], ["I am so hungry I could eat a horse.", "Hyperbole"], ["The lifeguard had to be rescued from the paddling pool.", "Irony"]],
  PROMPT: "Which device is at work? “{name}”",
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

    Kit.get('result').textContent = "Naming the device is the start. Then ask what it makes you see or feel that plain words would not.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

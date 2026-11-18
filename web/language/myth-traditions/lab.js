'use strict';
const Model = {
  ITEMS: [{"name": "Zeus", "cat": "Greek", "cols": ["Greek", "king of the gods; sky and thunder"], "lon": 22, "lat": 39}, {"name": "Athena", "cat": "Greek", "cols": ["Greek", "wisdom and craft"]}, {"name": "Poseidon", "cat": "Greek", "cols": ["Greek", "the sea and earthquakes"]}, {"name": "Odin", "cat": "Norse", "cols": ["Norse", "chief of the gods; wisdom and poetry"], "lon": 15, "lat": 62}, {"name": "Thor", "cat": "Norse", "cols": ["Norse", "thunder; wields the hammer Mjölnir"]}, {"name": "Loki", "cat": "Norse", "cols": ["Norse", "trickery and shape-changing"]}, {"name": "Ra", "cat": "Egyptian", "cols": ["Egyptian", "the sun"], "lon": 31, "lat": 27}, {"name": "Isis", "cat": "Egyptian", "cols": ["Egyptian", "magic and protection"]}, {"name": "Anubis", "cat": "Egyptian", "cols": ["Egyptian", "embalming and the dead"]}, {"name": "Anansi", "cat": "Akan (West African)", "cols": ["Akan (West African)", "the spider trickster who owns all stories"], "lon": -1, "lat": 8}, {"name": "Quetzalcoatl", "cat": "Aztec", "cols": ["Aztec", "the feathered serpent; wind and learning"], "lon": -99, "lat": 19}, {"name": "Amaterasu", "cat": "Japanese", "cols": ["Japanese", "the sun goddess"], "lon": 138, "lat": 36}],
  CATEGORIES: ["Greek", "Norse", "Egyptian", "Akan (West African)", "Aztec", "Japanese"],
  QUIZ: [["Zeus", "Greek"], ["Athena", "Greek"], ["Poseidon", "Greek"], ["Odin", "Norse"], ["Thor", "Norse"], ["Loki", "Norse"], ["Ra", "Egyptian"], ["Isis", "Egyptian"], ["Anubis", "Egyptian"], ["Anansi", "Akan (West African)"], ["Quetzalcoatl", "Aztec"], ["Amaterasu", "Japanese"]],
  PROMPT: "Which tradition tells of {name}?",
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
    const p = Kit.plot(Kit.get('graph'), {x: [-130, 170], y: [-20, 75], xlabel: 'Longitude (°E)', ylabel: 'Latitude (°N)', grid: true});
    Model.ITEMS.filter(item => item.lon !== undefined).forEach(item => {
      const on = shown.includes(item), below = item.below === true;
      p.point(item.lon, item.lat, on ? '#963d18' : '#9aa6ae', 7, !on);
      p.text(item.cat, item.lon, item.lat, on ? '#172533' : '#7a8790', below ? -12 : 10, below ? 22 : -8);
    });
    Kit.get('result').textContent = "Myths from far-apart places often share shapes: a sun deity, a thunder god, a trickster. Compare two and note what differs.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

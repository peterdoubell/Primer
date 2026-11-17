'use strict';
const Model = {
  ITEMS: [{"name": "Epic of Gilgamesh", "cat": "Mesopotamia", "cols": ["Mesopotamia", "about 2100–1200 BCE", "Sumerian and Akkadian tablets"], "lon": 44, "lat": 33}, {"name": "Mahabharata", "cat": "India", "cols": ["India", "about 400 BCE–400 CE", "attributed to Vyasa"], "lon": 78, "lat": 24}, {"name": "Shahnameh", "cat": "Persia", "cols": ["Persia", "about 1010", "Ferdowsi"], "lon": 53, "lat": 32, "below": true}, {"name": "The Tale of Genji", "cat": "Japan", "cols": ["Japan", "about 1010", "Murasaki Shikibu"], "lon": 136, "lat": 35}, {"name": "Journey to the West", "cat": "China", "cols": ["China", "16th century", "attributed to Wu Cheng’en"], "lon": 110, "lat": 34, "below": true}, {"name": "Popol Vuh", "cat": "Maya (Guatemala)", "cols": ["Maya (Guatemala)", "written down in the 16th century", "K’iche’ Maya tradition"], "lon": -91, "lat": 15}, {"name": "Don Quixote", "cat": "Spain", "cols": ["Spain", "1605 and 1615", "Miguel de Cervantes"], "lon": -4, "lat": 40}, {"name": "Things Fall Apart", "cat": "Nigeria", "cols": ["Nigeria", "1958", "Chinua Achebe"], "lon": 8, "lat": 8}, {"name": "One Hundred Years of Solitude", "cat": "Colombia", "cols": ["Colombia", "1967", "Gabriel García Márquez"], "lon": -74, "lat": 5}],
  CATEGORIES: ["Mesopotamia", "India", "Persia", "Japan", "China", "Maya (Guatemala)", "Spain", "Nigeria", "Colombia"],
  QUIZ: [["Epic of Gilgamesh", "Mesopotamia"], ["Mahabharata", "India"], ["Shahnameh", "Persia"], ["The Tale of Genji", "Japan"], ["Journey to the West", "China"], ["Popol Vuh", "Maya (Guatemala)"], ["Don Quixote", "Spain"], ["Things Fall Apart", "Nigeria"], ["One Hundred Years of Solitude", "Colombia"]],
  PROMPT: "Where does “{name}” come from?",
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
    const p = Kit.plot(Kit.get('graph'), {x: [-130, 170], y: [-20, 75], xlabel: 'Longitude (°E)', ylabel: 'Latitude (°N)', grid: true});
    Model.ITEMS.filter(item => item.lon !== undefined).forEach(item => {
      const on = shown.includes(item), below = item.below === true;
      p.point(item.lon, item.lat, on ? '#963d18' : '#9aa6ae', 7, !on);
      p.text(item.cat, item.lon, item.lat, on ? '#172533' : '#7a8790', below ? -12 : 10, below ? 22 : -8);
    });
    Kit.get('result').textContent = "Read one work from a tradition that is new to you, and note one thing it assumes that your own tradition does not.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

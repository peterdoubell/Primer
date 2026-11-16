'use strict';
const Model = {
  ITEMS: [{"name": "Richard III", "cat": "History", "cols": ["History", "1592", "A ruthless duke schemes his way to the crown."], "year": 1592}, {"name": "Romeo and Juliet", "cat": "Tragedy", "cols": ["Tragedy", "1595", "Two young lovers from feuding families."], "year": 1595}, {"name": "A Midsummer Night's Dream", "cat": "Comedy", "cols": ["Comedy", "1595", "Lovers and fairies in a wood near Athens."], "year": 1595}, {"name": "Much Ado About Nothing", "cat": "Comedy", "cols": ["Comedy", "1598", "Beatrice and Benedick are tricked into love."], "year": 1598}, {"name": "Henry V", "cat": "History", "cols": ["History", "1599", "A young king leads his army at Agincourt."], "year": 1599}, {"name": "Julius Caesar", "cat": "Tragedy", "cols": ["Tragedy", "1599", "Brutus joins the plot against Caesar."], "year": 1599}, {"name": "Hamlet", "cat": "Tragedy", "cols": ["Tragedy", "1600", "A prince is told to avenge his father."], "year": 1600}, {"name": "Twelfth Night", "cat": "Comedy", "cols": ["Comedy", "1601", "Shipwrecked Viola disguises herself as a man."], "year": 1601}, {"name": "Othello", "cat": "Tragedy", "cols": ["Tragedy", "1604", "Iago poisons a general’s trust in his wife."], "year": 1604}, {"name": "King Lear", "cat": "Tragedy", "cols": ["Tragedy", "1605", "An old king divides his kingdom."], "year": 1605}, {"name": "Macbeth", "cat": "Tragedy", "cols": ["Tragedy", "1606", "A prophecy drives a Scottish lord to murder."], "year": 1606}],
  CATEGORIES: ["History", "Tragedy", "Comedy"],
  QUIZ: [["Richard III", "History"], ["Romeo and Juliet", "Tragedy"], ["A Midsummer Night's Dream", "Comedy"], ["Much Ado About Nothing", "Comedy"], ["Henry V", "History"], ["Julius Caesar", "Tragedy"], ["Hamlet", "Tragedy"], ["Twelfth Night", "Comedy"], ["Othello", "Tragedy"], ["King Lear", "Tragedy"], ["Macbeth", "Tragedy"]],
  PROMPT: "Which kind of play is “{name}”?",
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
    Kit.get('result').textContent = "A comedy ends in marriage or reunion, a tragedy in the death of its hero, and a history follows an English king.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

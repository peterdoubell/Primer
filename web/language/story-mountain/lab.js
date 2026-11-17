'use strict';
const Model = {
  ITEMS: [{"name": "Opening", "cat": "Opening", "cols": ["who and where", "Tia lived beside a lighthouse."], "stage": 0}, {"name": "Build-up", "cat": "Build-up", "cols": ["something starts to happen", "One night the lamp flickered."], "stage": 1}, {"name": "Problem", "cat": "Problem", "cols": ["the biggest trouble", "The lamp went out as a ship drew near."], "stage": 2}, {"name": "Resolution", "cat": "Resolution", "cols": ["how the trouble is solved", "Tia waved a lantern from the rocks."], "stage": 3}, {"name": "Ending", "cat": "Ending", "cols": ["how things are afterwards", "The sailors named the lantern Tia’s Star."], "stage": 4}],
  CATEGORIES: ["Opening", "Build-up", "Problem", "Resolution", "Ending"],
  QUIZ: [["Sam and his dog Pip lived on a windy hill.", "Opening"], ["One day Pip began to dig by the old oak.", "Build-up"], ["The hole fell in and Pip was stuck.", "Problem"], ["Sam lowered a rope and pulled Pip out.", "Resolution"], ["After that, Pip only dug in the sandpit.", "Ending"], ["Long ago a girl called Noor kept bees.", "Opening"], ["That spring the bees grew restless.", "Build-up"], ["A storm knocked over every hive.", "Problem"], ["Noor built the hives again, stronger than before.", "Resolution"], ["The honey that year was the sweetest of all.", "Ending"]],
  PROMPT: "Which step of the story is this? “{name}”",
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
    const heights = [1, 2.2, 4, 2.2, 1];
    const p = Kit.plot(Kit.get('graph'), {x: [-0.6, 4.9], y: [0, 5], grid: false});
    for (let i = 0; i < 4; i++) p.line(i, heights[i], i + 1, heights[i + 1], '#215783', 3);
    Model.ITEMS.forEach(item => { const on = shown.includes(item); p.point(item.stage, heights[item.stage], on ? '#963d18' : '#9aa6ae', 7, !on); p.text((item.stage + 1) + '. ' + item.name, item.stage, heights[item.stage], '#172533', -30, -14); });
    Kit.get('result').textContent = "Plan the five steps in a few words each before you write. The problem is the top of the mountain.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

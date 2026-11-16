'use strict';
const Model = {
  ITEMS: [{"name": "Character", "cat": "Character", "cols": ["Who is the story about?", "what people want, say and do"], "stage": 0}, {"name": "Setting", "cat": "Setting", "cols": ["Where and when does it happen?", "place, time, weather, mood"], "stage": 1}, {"name": "Plot", "cat": "Plot", "cols": ["What happens, and why?", "events linked by cause and effect"], "stage": 2}, {"name": "Theme", "cat": "Theme", "cols": ["What is the story really about?", "an idea that keeps returning"], "stage": 3}, {"name": "Point of view", "cat": "Point of view", "cols": ["Who is telling the story?", "“I” or “she”; what the teller can know"], "stage": 4}],
  CATEGORIES: ["Character", "Setting", "Plot", "Theme", "Point of view"],
  QUIZ: [["The story takes place on a frozen island in winter.", "Setting"], ["Mara is stubborn but kind, and she hates being told what to do.", "Character"], ["Because the bridge collapses, the twins must cross the marsh.", "Plot"], ["Again and again the book returns to the cost of telling the truth.", "Theme"], ["The narrator says “I” and never knows what the others are thinking.", "Point of view"], ["Most of the chapters happen in one crowded kitchen in 1920.", "Setting"], ["The old sailor wants, above all, to see his daughter again.", "Character"], ["The theft in chapter two leads to the chase in chapter three.", "Plot"], ["Friendship across differences is the idea under every chapter.", "Theme"], ["The teller can see into every character’s mind.", "Point of view"]],
  PROMPT: "Which element does this note describe? “{name}”",
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
    const stages = ['Opening', 'Rising action', 'Climax', 'Falling action', 'Resolution'], heights = [1, 2.4, 4, 2.4, 1.3];
    const p = Kit.plot(Kit.get('graph'), {x: [-0.6, 4.9], y: [0, 5], grid: false});
    for (let i = 0; i < 4; i++) p.line(i, heights[i], i + 1, heights[i + 1], '#215783', 3);
    stages.forEach((stage, i) => { p.point(i, heights[i], '#963d18', 6); p.text(stage, i, heights[i], '#172533', -34, -14); });
    Kit.get('result').textContent = "While you read a long story, keep a short note for each element. Update it every few chapters.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

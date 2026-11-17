'use strict';
const Model = {
  ITEMS: [{"name": "Claim", "cat": "Claim", "cols": ["states what you want the reader to accept", "should; is; must"]}, {"name": "Evidence", "cat": "Evidence", "cols": ["gives facts, examples or quotations", "for example; a study found"]}, {"name": "Reasoning", "cat": "Reasoning", "cols": ["explains why the evidence supports the claim", "this shows; because; therefore"]}, {"name": "Counterargument", "cat": "Counterargument", "cols": ["states the strongest objection fairly", "some argue; it may be objected"]}, {"name": "Rebuttal", "cat": "Rebuttal", "cols": ["answers the objection", "however; yet; even so"]}],
  CATEGORIES: ["Claim", "Evidence", "Reasoning", "Counterargument", "Rebuttal"],
  QUIZ: [["Schools should start later in the morning.", "Claim"], ["In one district, attendance rose after the start time moved to nine.", "Evidence"], ["This shows that a later start removes a barrier to coming to school.", "Reasoning"], ["Some argue that a later start only moves bedtimes later.", "Counterargument"], ["However, students in the district slept longer, not later.", "Rebuttal"], ["Cities must plant more street trees.", "Claim"], ["For example, shaded streets were several degrees cooler in the survey.", "Evidence"], ["Because cooler streets need less air conditioning, trees save energy.", "Reasoning"], ["It may be objected that trees are costly to maintain.", "Counterargument"], ["Yet the saving in energy outweighs the cost of care.", "Rebuttal"]],
  PROMPT: "Which part of an argument is this? “{name}”",
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

    Kit.get('result').textContent = "A fair essay states the best objection to itself and answers it. That is what makes an argument honest.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

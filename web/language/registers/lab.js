'use strict';
const Model = {
  ITEMS: [{"name": "Frozen", "cat": "Frozen", "cols": ["ritual, law, oaths", "fixed wording that does not change"]}, {"name": "Formal", "cat": "Formal", "cols": ["lectures, official letters", "full sentences; no interruption; careful word choice"]}, {"name": "Consultative", "cat": "Consultative", "cols": ["doctor and patient; teacher and student", "two-way, polite, background information supplied"]}, {"name": "Casual", "cat": "Casual", "cols": ["friends", "slang, contractions, shared background assumed"]}, {"name": "Intimate", "cat": "Intimate", "cols": ["family and partners", "private words, few words, tone carries the meaning"]}],
  CATEGORIES: ["Frozen", "Formal", "Consultative", "Casual", "Intimate"],
  QUIZ: [["I do solemnly swear to tell the truth, the whole truth, and nothing but the truth.", "Frozen"], ["The committee regrets to inform you that your application was unsuccessful.", "Formal"], ["How long have you had the cough? Does it get worse at night?", "Consultative"], ["You coming tonight or what?", "Casual"], ["Usual, love?", "Intimate"], ["We the people, in order to form a more perfect union …", "Frozen"], ["This paper examines three causes of the decline.", "Formal"], ["Could you show me which step you found difficult?", "Consultative"], ["Nah, that film was rubbish.", "Casual"], ["Mm. You too.", "Intimate"]],
  PROMPT: "Which register is this? “{name}”",
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

    Kit.get('result').textContent = "No register is better than another. Skill lies in choosing the one the situation calls for, and noticing who is expected to shift.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

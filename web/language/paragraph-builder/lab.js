'use strict';
const Model = {
  ROLES: ['topic sentence', 'supporting point', 'evidence or example', 'concluding sentence'],
  JOB: {'topic sentence': 'says what the paragraph is about', 'supporting point': 'gives a reason for the main idea', 'evidence or example': 'backs the reason with a fact or example', 'concluding sentence': 'ties the paragraph back to the main idea'},
  PARAGRAPHS: [
    {title: 'Bees', sentences: [['Bees are essential to the food we eat.', 0], ['They carry pollen between flowers, which lets plants make fruit and seeds.', 1], ['Apples, almonds and blueberries all depend on this pollination.', 2], ['Protecting bees therefore protects our own food supply.', 3]]},
    {title: 'Reading aloud', sentences: [['Reading aloud helps young children learn language.', 0], ['It lets them hear words they would not meet in everyday talk.', 1], ['A picture book may use words such as “enormous” or “gloomy” that rarely come up at breakfast.', 2], ['For that reason, a daily story is one of the simplest ways to build vocabulary.', 3]]},
  ],
  // The same sentences in a fixed scrambled order.
  shuffled: paragraph => [2, 0, 3, 1].map(i => paragraph.sentences[i]),
  score: (paragraph, answers) => Model.shuffled(paragraph).filter(([, role], i) => answers[i] === role).length,
  ordered: paragraph => paragraph.sentences.map(s => s[0]).join(' '),
};
function start() {
  const pick = Kit.get('paragraph'), list = Kit.get('sentences');
  Model.PARAGRAPHS.forEach((p, i) => pick.add(new Option(p.title, i)));
  function grade() {
    const paragraph = Model.PARAGRAPHS[pick.value], answers = [...list.querySelectorAll('select')].map(s => Number(s.value)), n = Model.score(paragraph, answers);
    Kit.get('built').textContent = n === 4 ? Model.ordered(paragraph) : '';
    Kit.get('result').textContent = n === 4 ? 'All four are right. In order they read as one clear paragraph, shown above.' : n + ' of 4 are right. The topic sentence states the main idea; the others explain it, prove it and wrap it up.';
  }
  function draw() {
    list.replaceChildren(...Model.shuffled(Model.PARAGRAPHS[pick.value]).map(([text], i) => {
      const item = document.createElement('li'), label = document.createElement('label'), select = document.createElement('select');
      select.id = 'role-' + i; label.htmlFor = select.id; label.textContent = text; select.add(new Option('Choose its job', -1)); Model.ROLES.forEach((r, k) => select.add(new Option(r, k)));
      select.addEventListener('change', grade); item.append(label, select); return item;
    }));
    Kit.rows(Kit.get('rows'), Model.ROLES.map((r, i) => [String(i + 1), r, Model.JOB[r]])); grade();
  }
  Kit.bind(['paragraph'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

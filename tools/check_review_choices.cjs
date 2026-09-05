// Exercise the actual review-choice function, including its worst-case shuffle.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('web/app.js', 'utf8');
const code = source.slice(source.indexOf('  function backAnswer(back)'), source.indexOf('  function answerRecall('));
const context = {
  data: {cards: []},
  Math: Object.assign(Object.create(Math), {random: () => 0.5}),
  sameText: (a, b) => String(a).trim().toLowerCase() === String(b).trim().toLowerCase(),
};
vm.createContext(context);
vm.runInContext(code, context);
for (const prompt of ['Put these ages in order', 'Compare sizes', 'Fixed torch: order the positions']) {
  const parts = ['a small child', 'a grown adult', 'an old person'];
  const card = {id: 1, node_id: 'test', front: prompt + ': ' + parts.join(', '), back: parts.join(' ')};
  context.data.cards = [card];
  context.card = card;
  const other = vm.runInContext('distractorFor(card)', context);
  assert.notEqual(other, card.back);
  assert(parts.every(part => other.includes(part)), other);
  assert.equal(other.length, card.back.length);
}
console.log('Review choices: a single card, multiword members, internal colon and stalled shuffle all retain a different complete ordering.');

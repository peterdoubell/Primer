'use strict';
const Model = {
  JOBS: {noun: 'names a person, place, thing or idea', pronoun: 'stands in for a noun', verb: 'tells what happens or what is', adjective: 'describes a noun', adverb: 'describes a verb, adjective or another adverb',
    preposition: 'shows how a noun relates to the rest', conjunction: 'joins words or clauses', determiner: 'points to which noun is meant'},
  SENTENCES: [
    [['The', 'determiner'], ['small', 'adjective'], ['dog', 'noun'], ['barked', 'verb'], ['loudly', 'adverb'], ['at', 'preposition'], ['the', 'determiner'], ['postman', 'noun']],
    [['She', 'pronoun'], ['quickly', 'adverb'], ['read', 'verb'], ['an', 'determiner'], ['old', 'adjective'], ['book', 'noun'], ['and', 'conjunction'], ['smiled', 'verb']],
    [['Three', 'determiner'], ['tired', 'adjective'], ['children', 'noun'], ['slept', 'verb'], ['under', 'preposition'], ['a', 'determiner'], ['tree', 'noun']],
    [['We', 'pronoun'], ['often', 'adverb'], ['walk', 'verb'], ['to', 'preposition'], ['school', 'noun'], ['but', 'conjunction'], ['they', 'pronoun'], ['cycle', 'verb']],
    [['My', 'determiner'], ['clever', 'adjective'], ['sister', 'noun'], ['solved', 'verb'], ['the', 'determiner'], ['puzzle', 'noun'], ['very', 'adverb'], ['easily', 'adverb']],
  ],
  text: sentence => sentence.map(w => w[0]).join(' ') + '.',
  count(sentence) { const out = {}; for (const [, kind] of sentence) out[kind] = (out[kind] || 0) + 1; return out; },
};
function start() {
  const select = Kit.get('sentence'); let target = 0, score = 0, tries = 0;
  Model.SENTENCES.forEach((s, i) => select.add(new Option(Model.text(s), i)));
  const answers = Kit.get('answers');
  for (const kind of Object.keys(Model.JOBS)) { const b = document.createElement('button'); b.textContent = kind; b.addEventListener('click', () => answer(kind)); answers.append(b); }
  function ask() { const s = Model.SENTENCES[select.value]; target = (target + 3) % s.length; Kit.get('prompt').textContent = 'What kind of word is “' + s[target][0] + '” in this sentence?'; }
  function answer(kind) {
    const [word, right] = Model.SENTENCES[select.value][target]; tries++; if (kind === right) score++;
    Kit.get('result').textContent = (kind === right ? 'Yes. ' : 'Not quite. ') + '“' + word + '” is a ' + right + ': it ' + Model.JOBS[right] + '. Score ' + score + ' of ' + tries + '.'; ask();
  }
  function draw() {
    const s = Model.SENTENCES[select.value];
    Kit.rows(Kit.get('rows'), s.map(([word, kind]) => [word, kind, Model.JOBS[kind]]));
    Kit.get('summary').textContent = Object.entries(Model.count(s)).map(([kind, n]) => n + ' ' + kind + (n > 1 ? 's' : '')).join(', ') + '.';
    target = -3; ask();
  }
  Kit.bind(['sentence'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

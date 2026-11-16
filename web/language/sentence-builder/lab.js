'use strict';
const Model = {
  SUBJECTS: ['the cat', 'my friend', 'a tall giraffe', 'our teacher', 'the rain'],
  VERBS: ['sleeps', 'sings', 'eats', 'reads', 'falls'],
  ENDINGS: ['on the mat', 'in the garden', 'every morning', 'very quietly', ''],
  build(subject, verb, ending, kind) {
    if (kind === 'question') { const words = ['does', subject, verb.replace(/s$/, ''), ending].filter(Boolean).join(' '); return words[0].toUpperCase() + words.slice(1) + '?'; }
    const words = [subject, verb, ending].filter(Boolean).join(' ');
    return words[0].toUpperCase() + words.slice(1) + (kind === 'exclamation' ? '!' : '.');
  },
  // The three checks a complete sentence must pass.
  check(text) { return {capital: /^[A-Z]/.test(text), end: /[.?!]$/.test(text), verb: Model.VERBS.some(v => text.toLowerCase().includes(v.replace(/s$/, '')))}; },
  kind: text => text.endsWith('?') ? 'question' : text.endsWith('!') ? 'exclamation' : text.endsWith('.') ? 'statement' : 'not finished',
};
function start() {
  const fill = (id, list) => list.forEach(v => Kit.get(id).add(new Option(v || '(nothing)', v)));
  fill('subject', Model.SUBJECTS); fill('verb', Model.VERBS); fill('ending', Model.ENDINGS);
  function draw() {
    const sentence = Model.build(Kit.get('subject').value, Kit.get('verb').value, Kit.get('ending').value, Kit.get('kind').value), c = Model.check(sentence);
    Kit.get('sentence').textContent = sentence;
    Kit.rows(Kit.get('rows'), [['Who or what? (subject)', Kit.get('subject').value], ['What happens? (verb)', Kit.get('verb').value], ['More detail', Kit.get('ending').value || '—'],
      ['Starts with a capital letter', c.capital ? 'yes' : 'no'], ['Ends with . ? or !', c.end ? 'yes' : 'no'], ['Kind of sentence', Model.kind(sentence)]]);
    Kit.get('result').textContent = 'A complete sentence needs someone or something (the subject) and what they do (the verb). It starts with a capital letter and ends with a full stop, a question mark or an exclamation mark.';
  }
  Kit.bind(['subject', 'verb', 'ending', 'kind'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

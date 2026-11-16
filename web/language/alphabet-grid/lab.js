'use strict';
const Model = {
  WORDS: ['apple', 'ball', 'cat', 'dog', 'egg', 'fish', 'goat', 'hat', 'insect', 'jam', 'kite', 'lion', 'moon', 'nest', 'orange', 'pig', 'queen', 'rain', 'sun', 'tree', 'umbrella', 'van', 'web', 'box', 'yo-yo', 'zebra'],
  letters: () => [...'abcdefghijklmnopqrstuvwxyz'],
  info(letter) {
    const index = letter.toLowerCase().charCodeAt(0) - 97, word = Model.WORDS[index];
    return {index: index + 1, upper: letter.toUpperCase(), lower: letter.toLowerCase(), vowel: 'aeiou'.includes(letter.toLowerCase()), word,
      before: index ? String.fromCharCode(96 + index) : null, after: index < 25 ? String.fromCharCode(98 + index) : null, position: word.indexOf(letter.toLowerCase()) === 0 ? 'starts' : 'ends'};
  },
};
function start() {
  const grid = Kit.get('grid');
  function show(letter) {
    const i = Model.info(letter);
    for (const b of grid.children) b.setAttribute('aria-pressed', String(b.dataset.letter === letter));
    Kit.get('big').textContent = i.upper + ' ' + i.lower;
    Kit.rows(Kit.get('rows'), [['Place in the alphabet', i.index + ' of 26'], ['Kind of letter', i.vowel ? 'vowel' : 'consonant'], ['Letter before', i.before ? i.before.toUpperCase() : 'none: A is first'],
      ['Letter after', i.after ? i.after.toUpperCase() : 'none: Z is last'], ['A word to listen for', i.word + (i.position === 'ends' ? ' (ends with ' + i.lower + ')' : '')]]);
    Kit.get('result').textContent = i.upper + ' is letter ' + i.index + '. ' + (i.vowel ? 'It is one of the five vowels: A, E, I, O, U.' : 'It is a consonant.') + ' Capital ' + i.upper + ' and small ' + i.lower + ' are the same letter. Say “' + i.word + '” and listen for it.';
  }
  for (const letter of Model.letters()) { const b = document.createElement('button'); b.textContent = letter.toUpperCase() + letter; b.dataset.letter = letter; if ('aeiou'.includes(letter)) b.className = 'vowel'; b.addEventListener('click', () => show(letter)); grid.append(b); }
  show('a');
}
if (typeof module === 'object') module.exports = Model; else start();

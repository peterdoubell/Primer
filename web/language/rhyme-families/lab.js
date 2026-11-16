'use strict';
const Model = {
  FAMILIES: {at: ['cat', 'hat', 'mat', 'bat', 'rat'], og: ['dog', 'log', 'frog', 'fog', 'jog'], ee: ['tree', 'bee', 'sea', 'key', 'three'], ight: ['night', 'light', 'kite', 'white', 'bright'],
    ake: ['cake', 'lake', 'snake', 'steak', 'rake'], un: ['sun', 'run', 'bun', 'one', 'fun']},
  family: word => Object.keys(Model.FAMILIES).find(f => Model.FAMILIES[f].includes(word)),
  rhymes: (a, b) => a !== b && Model.family(a) === Model.family(b),
  // Words that rhyme without sharing the same spelling of the ending.
  surprising: word => { const f = Model.family(word); return Model.FAMILIES[f].filter(w => w !== word && !w.endsWith(f)); },
  // Three words from one family and one from the next.
  round(n) { const keys = Object.keys(Model.FAMILIES), f = keys[n % keys.length], other = keys[(n + 1) % keys.length]; const words = Model.FAMILIES[f].slice(0, 3); words.splice(n % 4, 0, Model.FAMILIES[other][n % 5]); return {words, odd: Model.FAMILIES[other][n % 5]}; },
};
function start() {
  const pick = Kit.get('word'); let n = 0, score = 0;
  Object.values(Model.FAMILIES).flat().forEach(w => pick.add(new Option(w, w)));
  function ask() {
    const round = Model.round(n), box = Kit.get('choices');
    box.replaceChildren(...round.words.map(w => { const b = document.createElement('button'); b.textContent = w; b.addEventListener('click', () => {
      if (w === round.odd) score++; Kit.get('feedback').textContent = (w === round.odd ? 'Yes! ' : 'Listen again. ') + '“' + round.odd + '” does not rhyme with the others. Score ' + score + ' of ' + (n + 1) + '.'; n++; ask(); }); return b; }));
  }
  function draw() {
    const word = pick.value, f = Model.family(word), odd = Model.surprising(word);
    Kit.rows(Kit.get('rows'), Model.FAMILIES[f].filter(w => w !== word).map(w => [w, w.endsWith(f) ? 'same letters at the end' : 'same sound, different spelling']));
    Kit.get('result').textContent = 'Words rhyme when they end with the same sound. “' + word + '” rhymes with ' + Model.FAMILIES[f].filter(w => w !== word).join(', ') + '.' + (odd.length ? ' Rhyme is about sound, not spelling: ' + odd.join(' and ') + ' rhyme too.' : '');
  }
  Kit.bind(['word'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();

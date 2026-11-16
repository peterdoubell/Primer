'use strict';
const Model = {
  ROOTS: {tele: ['Greek', 'far'], graph: ['Greek', 'write'], phon: ['Greek', 'sound'], photo: ['Greek', 'light'], bio: ['Greek', 'life'], geo: ['Greek', 'earth'], logy: ['Greek', 'study of'],
    micro: ['Greek', 'small'], scope: ['Greek', 'look at'], therm: ['Greek', 'heat'], meter: ['Greek', 'measure'], chron: ['Greek', 'time'], auto: ['Greek', 'self'],
    aqua: ['Latin', 'water'], port: ['Latin', 'carry'], script: ['Latin', 'written'], spect: ['Latin', 'look'], dict: ['Latin', 'say'], trans: ['Latin', 'across'], in: ['Latin', 'into, on']},
  WORDS: {telephone: ['tele', 'phon'], telegraph: ['tele', 'graph'], telescope: ['tele', 'scope'], photograph: ['photo', 'graph'], biography: ['bio', 'graph'], autobiography: ['auto', 'bio', 'graph'],
    biology: ['bio', 'logy'], geology: ['geo', 'logy'], geography: ['geo', 'graph'], microscope: ['micro', 'scope'], microphone: ['micro', 'phon'], thermometer: ['therm', 'meter'],
    chronology: ['chron', 'logy'], chronometer: ['chron', 'meter'], autograph: ['auto', 'graph'], transport: ['trans', 'port'], transcript: ['trans', 'script'], inscription: ['in', 'script'],
    inspect: ['in', 'spect'], aquarium: ['aqua'], dictate: ['dict'], import: ['in', 'port']},
  literal: word => Model.WORDS[word].map(r => Model.ROOTS[r][1]).join(' + '),
  family: root => Object.keys(Model.WORDS).filter(w => Model.WORDS[w].includes(root)),
};
function start() {
  const word = Kit.get('word'), root = Kit.get('root');
  Object.keys(Model.WORDS).forEach(w => word.add(new Option(w, w))); Object.keys(Model.ROOTS).forEach(r => root.add(new Option(r + ' (' + Model.ROOTS[r][1] + ')', r)));
  function draw() {
    const parts = Model.WORDS[word.value];
    Kit.rows(Kit.get('rows'), parts.map(r => [r, Model.ROOTS[r][0], Model.ROOTS[r][1], Model.family(r).join(', ')]));
    Kit.get('family').textContent = Model.family(root.value).join(', ') || 'no words in this list';
    Kit.get('result').textContent = '“' + word.value + '” is built from ' + parts.length + (parts.length > 1 ? ' roots' : ' root') + ': ' + Model.literal(word.value) + '. Roots are spelled a little differently inside some words (im- for in-, -phone for phon), and meanings drift over time, so a root is a clue to a word, not its full definition.';
  }
  Kit.bind(['word', 'root'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

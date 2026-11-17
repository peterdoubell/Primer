'use strict';
const Model = {
  FEET: {iamb: 'da-DUM', trochee: 'DUM-da', anapest: 'da-da-DUM', dactyl: 'DUM-da-da', spondee: 'DUM-DUM'},
  PATTERN: {iamb: 'xS', trochee: 'Sx', anapest: 'xxS', dactyl: 'Sxx', spondee: 'SS'},
  COUNT: {1: 'monometer', 2: 'dimeter', 3: 'trimeter', 4: 'tetrameter', 5: 'pentameter', 6: 'hexameter'},
  // Syllables with the usual stress pattern: S stressed, x unstressed.
  LINES: [
    {poet: 'William Shakespeare, Sonnet 18', foot: 'iamb', feet: 5, syllables: ['Shall', 'I', 'com', 'pare', 'thee', 'to', 'a', 'sum', "mer's", 'day?'], stress: 'xSxSxSxSxS'},
    {poet: 'William Blake, “The Tyger”', foot: 'trochee', feet: 4, syllables: ['Ty', 'ger', 'Ty', 'ger,', 'burn', 'ing', 'bright'], stress: 'SxSxSxS', note: 'The last foot is cut short by one syllable.'},
    {poet: 'Clement Clarke Moore, “A Visit from St. Nicholas”', foot: 'anapest', feet: 4, syllables: ["'Twas", 'the', 'night', 'be', 'fore', 'Christ', 'mas,', 'when', 'all', 'through', 'the', 'house'], stress: 'xxSxxSxxSxxS'},
    {poet: 'Emily Dickinson, “Because I could not stop for Death”', foot: 'iamb', feet: 4, syllables: ['Be', 'cause', 'I', 'could', 'not', 'stop', 'for', 'Death'], stress: 'xSxSxSxS'},
    {poet: 'Henry Wadsworth Longfellow, “Evangeline”', foot: 'dactyl', feet: 6, syllables: ['This', 'is', 'the', 'for', 'est', 'pri', 'me', 'val.', 'The', 'mur', 'mur', 'ing', 'pines', 'and', 'the', 'hem', 'locks'], stress: 'SxxSxxSxxSxxSxxSx', note: 'The final foot has two syllables, as is usual in this metre.'},
  ],
  name: line => line.foot.replace('iamb', 'iambic').replace('trochee', 'trochaic').replace('anapest', 'anapestic').replace('dactyl', 'dactylic') + ' ' + Model.COUNT[line.feet],
  // How many complete feet of the named kind the stress pattern contains, reading from the start.
  matches(line) { const unit = Model.PATTERN[line.foot]; let n = 0; for (let i = 0; i + unit.length <= line.stress.length; i += unit.length) if (line.stress.slice(i, i + unit.length) === unit) n++; return n; },
};
function start() {
  const select = Kit.get('line');
  Model.LINES.forEach((l, i) => select.add(new Option(l.poet, i)));
  function draw() {
    const line = Model.LINES[select.value], verse = Kit.get('verse');
    verse.replaceChildren(...line.syllables.map((s, i) => { const span = document.createElement(line.stress[i] === 'S' ? 'strong' : 'span'); span.textContent = s; span.className = 'syllable'; return span; }));
    Kit.get('beats').textContent = [...line.stress].map(c => c === 'S' ? 'DUM' : 'da').join(' ');
    Kit.rows(Kit.get('rows'), Object.entries(Model.FEET).map(([foot, sound]) => [foot + (foot === line.foot ? ' ← this line' : ''), sound, foot === line.foot ? String(line.feet) + ' in the line' : '']));
    Kit.get('result').textContent = 'This line is ' + Model.name(line) + ': ' + line.feet + ' feet, each ' + (/^[aeiou]/.test(line.foot) ? 'an ' : 'a ') + line.foot + ' (' + Model.FEET[line.foot] + '). Stressed syllables are in bold. ' + (line.note || '') + ' Read it aloud and tap the strong beats.';
  }
  Kit.bind(['line'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

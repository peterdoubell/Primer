'use strict';
const Model = {
  PERIODS: [
    {name: 'Old English', from: 450, to: 1150, sample: 'Fæder ure þu þe eart on heofonum', source: 'West Saxon Gospels, about 990', note: 'A Germanic language with case endings; most of it is unreadable today without study.'},
    {name: 'Middle English', from: 1150, to: 1500, sample: 'Oure fadir that art in heuenes', source: 'Wycliffite Bible, 1380s', note: 'After the Norman Conquest thousands of French words arrive and most case endings are lost.'},
    {name: 'Early Modern English', from: 1500, to: 1700, sample: 'Our father which art in heauen', source: 'King James Bible, 1611', note: 'Printing fixes spellings while the Great Vowel Shift changes how long vowels are said.'},
    {name: 'Modern English', from: 1700, to: 2025, sample: 'Our Father in heaven', source: 'a present-day translation', note: 'Dictionaries standardise spelling and the language spreads worldwide.'},
  ],
  EVENTS: [[597, 'Augustine’s mission brings Latin words through the Church'], [793, 'Viking raids begin; Old Norse gives they, sky, egg'], [1066, 'Norman Conquest: French becomes the language of court and law'],
    [1400, 'Death of Chaucer, author of The Canterbury Tales'], [1476, 'Caxton sets up the first printing press in England'], [1611, 'King James Bible published'], [1623, 'Shakespeare’s First Folio printed'],
    [1755, 'Samuel Johnson’s Dictionary'], [1828, 'Noah Webster’s American Dictionary'], [1928, 'First edition of the Oxford English Dictionary completed']],
  period: year => Model.PERIODS.find(p => year >= p.from && year < p.to) || Model.PERIODS[Model.PERIODS.length - 1],
  eventsBy: year => Model.EVENTS.filter(e => e[0] <= year),
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d'), colours = ['#8fb3cc', '#c9a26b', '#a9c79a', '#d9a5a0'];
  function draw() {
    const year = Kit.num('year'), period = Model.period(year), X = y => 30 + (y - 450) * 660 / 1575;
    Kit.say('year', year, 'year ' + year);
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '14px system-ui, sans-serif';
    Model.PERIODS.forEach((p, i) => { ctx.fillStyle = colours[i]; ctx.fillRect(X(p.from), 50, X(p.to) - X(p.from), 46); ctx.fillStyle = '#172533'; ctx.fillText(p.name, X(p.from) + 6, 78); ctx.fillText(String(p.from), X(p.from), 116); });
    Model.EVENTS.forEach(([y]) => { ctx.fillStyle = y <= year ? '#172533' : '#b5bcc1'; ctx.beginPath(); ctx.arc(X(y), 34, 5, 0, 2 * Math.PI); ctx.fill(); });
    ctx.strokeStyle = '#963d18'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(X(year), 18); ctx.lineTo(X(year), 124); ctx.stroke();
    Kit.get('sample').textContent = period.sample; Kit.get('source').textContent = period.source;
    Kit.rows(Kit.get('rows'), Model.eventsBy(year).slice(-5).reverse().map(([y, what]) => [String(y), what]));
    Kit.get('result').textContent = 'In ' + year + ' the language is ' + period.name + ' (' + period.from + '–' + (period.to === 2025 ? 'today' : period.to) + '). ' + period.note + ' The period boundaries are conventions; the language changed gradually.';
    canvas.setAttribute('aria-label', 'Timeline of English from 450 to the present with the year ' + year + ' marked in the ' + period.name + ' period.');
  }
  Kit.bind(['year'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

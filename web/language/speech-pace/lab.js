'use strict';
const Model = {
  // Shares of the whole talk. They are a common rule of thumb, not a law.
  PARTS: [{name: 'Opening', share: 0.15, job: 'win attention and say what the talk is about'},
    {name: 'Body', share: 0.7, job: 'two or three points, each with an example'},
    {name: 'Close', share: 0.15, job: 'sum up and end on one clear sentence'}],
  PACES: [{label: 'slow and clear', below: 120}, {label: 'comfortable', below: 160}, {label: 'fast', below: Infinity}],
  words: (minutes, pace) => Math.round(minutes * pace),
  seconds: (words, pace) => Math.round(words / pace * 60),
  count: text => (text.trim().match(/\S+/g) || []).length,
  describe: pace => Model.PACES.find(row => pace < row.below).label,
  clock(seconds) { const m = Math.floor(seconds / 60), s = seconds % 60; return m + ':' + String(s).padStart(2, '0'); },
  plan(minutes, pace) {
    const total = Model.words(minutes, pace);
    return Model.PARTS.map(part => ({name: part.name, job: part.job, seconds: Math.round(minutes * 60 * part.share), words: Math.round(total * part.share)}));
  },
  // Positive when the draft runs over the time allowed.
  overrun: (text, minutes, pace) => Model.seconds(Model.count(text), pace) - Math.round(minutes * 60),
};
function start() {
  function draw() {
    const minutes = Kit.num('minutes'), pace = Kit.num('pace'), text = Kit.get('draft').value, plan = Model.plan(minutes, pace);
    Kit.say('minutes', minutes, minutes + ' minutes'); Kit.say('pace', pace, pace + ' words a minute (' + Model.describe(pace) + ')');
    Kit.rows(Kit.get('rows'), plan.map(part => [part.name, part.job, Model.clock(part.seconds), String(part.words)]));
    const canvas = Kit.get('graph'), ctx = canvas.getContext('2d'), colours = ['#215783', '#963d18', '#3c7a4b'];
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '16px system-ui, sans-serif';
    let x = 30; const width = canvas.width - 60;
    Model.PARTS.forEach((part, i) => {
      const w = width * part.share; ctx.fillStyle = colours[i]; ctx.fillRect(x, 60, w - 3, 70);
      ctx.fillStyle = '#172533'; ctx.fillText(part.name, x, 48); ctx.fillText(Model.clock(plan[i].seconds), x, 154); x += w;
    });
    let message = 'In ' + minutes + ' minutes at ' + pace + ' words a minute you can say about ' + Model.words(minutes, pace) + ' words. Leave room for pauses: a pause lets a point land.';
    const words = Model.count(text);
    if (words) {
      const over = Model.overrun(text, minutes, pace);
      message += ' Your draft has ' + words + ' words and would take about ' + Model.clock(Model.seconds(words, pace)) + '. '
        + (over > 0 ? 'That is ' + Model.clock(over) + ' too long: cut about ' + Math.round(over / 60 * pace) + ' words.' : 'It fits the time allowed.');
    }
    Kit.get('result').textContent = message;
  }
  Kit.bind(['minutes', 'pace', 'draft'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

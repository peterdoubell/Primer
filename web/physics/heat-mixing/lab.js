'use strict';
const Model = {
  C_WATER: 4186,                                   // J per kg per °C
  final: (m1, t1, m2, t2) => (m1 * t1 + m2 * t2) / (m1 + m2),
  // Energy leaving the warmer water (J); the cooler water gains the same amount.
  transferred(m1, t1, m2, t2) { const f = Model.final(m1, t1, m2, t2); return Math.abs(m1 * Model.C_WATER * (t1 - f)); },
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d');
  const colour = t => 'rgb(' + Math.round(40 + 2.1 * t) + ',' + Math.round(110 - 0.3 * t) + ',' + Math.round(230 - 1.9 * t) + ')';
  function draw() {
    const m1 = Kit.num('m1'), t1 = Kit.num('t1'), m2 = Kit.num('m2'), t2 = Kit.num('t2'), f = Model.final(m1, t1, m2, t2), q = Model.transferred(m1, t1, m2, t2);
    Kit.say('m1', m1, m1 + ' kg'); Kit.say('t1', t1, t1 + ' °C'); Kit.say('m2', m2, m2 + ' kg'); Kit.say('t2', t2, t2 + ' °C');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '16px system-ui, sans-serif'; ctx.strokeStyle = '#172533'; ctx.lineWidth = 3;
    const beaker = (x, mass, temp, label) => { const h = 34 * mass; ctx.fillStyle = colour(temp); ctx.fillRect(x, 300 - h, 130, h); ctx.strokeRect(x, 60, 130, 240); ctx.fillStyle = '#172533'; ctx.fillText(label, x, 325); ctx.fillText(Kit.fmt(temp, 3) + ' °C, ' + Kit.fmt(mass) + ' kg', x, 345); };
    beaker(70, m1, t1, 'First'); beaker(250, m2, t2, 'Second'); ctx.fillStyle = '#172533'; ctx.fillText('→ mix →', 400, 190);
    const h = 17 * (m1 + m2); ctx.fillStyle = colour(f); ctx.fillRect(490, 300 - h, 180, h); ctx.strokeRect(490, 60, 180, 240); ctx.fillStyle = '#172533'; ctx.fillText('Mixture', 490, 325); ctx.fillText(Kit.fmt(f, 3) + ' °C, ' + Kit.fmt(m1 + m2) + ' kg', 490, 345);
    Kit.rows(Kit.get('rows'), [['Final temperature', Kit.fmt(f) + ' °C'], ['Energy moved from warm to cool', Kit.fmt(q / 1000) + ' kJ'], ['First water changes by', Kit.fmt(f - t1) + ' °C'], ['Second water changes by', Kit.fmt(f - t2) + ' °C']]);
    Kit.get('result').textContent = t1 === t2 ? 'Both are at the same temperature, so no energy moves.' : 'Energy flows from the warmer water to the cooler until both reach ' + Kit.fmt(f, 3) + ' °C. The final temperature lies closer to that of the larger mass, because more water needs more energy to change by each degree.';
    canvas.setAttribute('aria-label', 'Two beakers of water mixed. The mixture is at ' + Kit.fmt(f, 3) + ' degrees Celsius.');
  }
  Kit.bind(['m1', 't1', 'm2', 't2'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

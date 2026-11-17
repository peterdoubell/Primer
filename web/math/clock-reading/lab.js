'use strict';
const Model = {
  angles: (h, m) => ({minute: m * 6, hour: (h % 12) * 30 + m * 0.5}),
  digital: (h, m) => h + ':' + String(m).padStart(2, '0'),
  words(h, m) {
    const N = ['twelve', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'], next = N[h % 12 + 1];
    if (m === 0) return N[h] + " o'clock";
    if (m === 15) return 'quarter past ' + N[h];
    if (m === 30) return 'half past ' + N[h];
    if (m === 45) return 'quarter to ' + next;
    return m < 30 ? m + (m === 1 ? ' minute past ' : ' minutes past ') + N[h] : (60 - m) + (m === 59 ? ' minute to ' : ' minutes to ') + next;
  },
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d');
  function draw() {
    const h = Kit.num('hour'), m = Kit.num('minute'), a = Model.angles(h, m), cx = 360, cy = 210, R = 180;
    Kit.say('hour', h, h + ''); Kit.say('minute', m, m + ' min');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#172533'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 2 * Math.PI); ctx.stroke();
    ctx.font = '24px system-ui, sans-serif'; ctx.fillStyle = '#172533';
    for (let i = 1; i <= 60; i++) {
      const t = i * Math.PI / 30, big = i % 5 === 0, r0 = R - (big ? 16 : 8);
      ctx.lineWidth = big ? 3 : 1; ctx.beginPath(); ctx.moveTo(cx + r0 * Math.sin(t), cy - r0 * Math.cos(t)); ctx.lineTo(cx + R * Math.sin(t), cy - R * Math.cos(t)); ctx.stroke();
      if (big) { const s = String(i / 5); ctx.fillText(s, cx + (R - 38) * Math.sin(t) - ctx.measureText(s).width / 2, cy - (R - 38) * Math.cos(t) + 8); }
    }
    const hand = (deg, len, colour, width) => { const t = deg * Math.PI / 180; ctx.strokeStyle = colour; ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + len * Math.sin(t), cy - len * Math.cos(t)); ctx.stroke(); };
    hand(a.hour, 100, '#963d18', 9); hand(a.minute, 150, '#215783', 5);
    Kit.rows(Kit.get('rows'), [['Digital', Model.digital(h, m)], ['In words', Model.words(h, m)], ['Minutes until the next hour', String((60 - m) % 60)],
      ['Short (hour) hand has turned', Kit.fmt(a.hour) + '° from 12'], ['Long (minute) hand has turned', a.minute + '° from 12']]);
    Kit.get('result').textContent = 'It is ' + Model.words(h, m) + '. The long blue hand points to the minutes. The short orange hand shows the hour and creeps towards the next number as the minutes pass.';
    canvas.setAttribute('aria-label', 'Clock face showing ' + Model.digital(h, m) + '.');
  }
  Kit.bind(['hour', 'minute'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

'use strict';
const Model = {
  hex: (r, g, b) => '#' + [r, g, b].map(v => Math.round(v * 255 / 100).toString(16).padStart(2, '0')).join(''),
  // Name the light made by red, green and blue beams (each 0–100%).
  name(r, g, b) {
    const on = [r, g, b].map(v => v >= 50);
    return ({'000': 'black (no light)', '100': 'red', '010': 'green', '001': 'blue', '110': 'yellow', '011': 'cyan', '101': 'magenta', '111': 'white'})[on.map(Number).join('')];
  },
  complement: (r, g, b) => [100 - r, 100 - g, 100 - b],
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d');
  function draw() {
    const r = Kit.num('red'), g = Kit.num('green'), b = Kit.num('blue');
    Kit.say('red', r, r + '%'); Kit.say('green', g, g + '%'); Kit.say('blue', b, b + '%');
    ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.globalCompositeOperation = 'lighter';
    for (const [x, y, colour] of [[300, 150, Model.hex(r, 0, 0)], [420, 150, Model.hex(0, g, 0)], [360, 250, Model.hex(0, 0, b)]]) { ctx.fillStyle = colour; ctx.beginPath(); ctx.arc(x, y, 120, 0, 2 * Math.PI); ctx.fill(); }
    ctx.globalCompositeOperation = 'source-over';
    const c = Model.complement(r, g, b);
    Kit.rows(Kit.get('rows'), [['All three beams together', Model.name(r, g, b), Model.hex(r, g, b)], ['Red + green', Model.name(r, g, 0), Model.hex(r, g, 0)], ['Green + blue', Model.name(0, g, b), Model.hex(0, g, b)],
      ['Red + blue', Model.name(r, 0, b), Model.hex(r, 0, b)], ['Light that would complete it to white', Model.name(...c), Model.hex(...c)]]);
    Kit.get('result').textContent = 'Coloured lights add. Where all three beams overlap the mixture looks ' + Model.name(r, g, b) + '. Red and green light together look yellow; all three at full strength look white. Paints behave differently because they remove light instead of adding it.';
    canvas.setAttribute('aria-label', 'Three overlapping beams of red, green and blue light. The centre looks ' + Model.name(r, g, b) + '.');
  }
  Kit.bind(['red', 'green', 'blue'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

'use strict';
const Model = {
  gamma: beta => 1 / Math.sqrt(1 - beta * beta),
  dilated: (properTime, beta) => properTime * Model.gamma(beta),
  contracted: (properLength, beta) => properLength / Model.gamma(beta),
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const beta = Kit.num('speed'), g = Model.gamma(beta);
    Kit.say('speed', beta, 'v = ' + beta + ' c');
    const p = Kit.plot(canvas, {x: [0, 1], y: [0, 8], xlabel: 'speed v / c', ylabel: 'γ'});
    p.curve(v => v < 0.9995 ? Model.gamma(v) : NaN, '#215783', 0, 0.9995);
    p.line(0, 1, 1, 1, '#6b7780', 1.5, [6, 4]);
    p.line(beta, 0, beta, Math.min(g, 8), '#963d18', 2, [5, 4]); p.point(beta, Math.min(g, 8)); p.text('γ = ' + Kit.fmt(g), beta, Math.min(g, 7.4), '#172533', beta > 0.7 ? -110 : 8);
    Kit.rows(Kit.get('rows'), [['Lorentz factor γ = 1/√(1 − v²/c²)', Kit.fmt(g)],
      ['1 s on the moving clock, measured from the ground', Kit.fmt(Model.dilated(1, beta)) + ' s'],
      ['A 10 m ship, measured from the ground', Kit.fmt(Model.contracted(10, beta)) + ' m'],
      ['Speed', Kit.fmt(beta * 299792.458, 6) + ' km/s']]);
    Kit.get('result').textContent = (g < 1.01 ? 'At this speed the effect is below 1%: everyday speeds are far too slow to notice.' : 'The moving clock runs slow by a factor of ' + Kit.fmt(g) + ' and the ship is shortened along its direction of travel by the same factor.')
      + ' The curve stays near 1 until about half the speed of light, then rises without limit as v approaches c.';
    canvas.setAttribute('aria-label', 'Graph of the Lorentz factor against speed, marked at ' + beta + ' c. ' + Kit.get('result').textContent);
  }
  Kit.bind(['speed'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

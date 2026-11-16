'use strict';
const Model = {
  // Launch at speed v (m/s), angle (degrees) from height h (m); no air resistance.
  flight(v, angle, h = 0, g = 9.81) {
    const t = angle * Math.PI / 180, vx = v * Math.cos(t), vy = v * Math.sin(t), time = (vy + Math.sqrt(vy * vy + 2 * g * h)) / g;
    return {vx, vy, time, range: vx * time, peak: h + vy * vy / (2 * g), peakTime: vy / g, impactSpeed: Math.hypot(vx, vy - g * time)};
  },
  position: (v, angle, h, t, g = 9.81) => { const a = angle * Math.PI / 180; return [v * Math.cos(a) * t, h + v * Math.sin(a) * t - g * t * t / 2]; },
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const v = Kit.num('speed'), angle = Kit.num('angle'), h = Kit.num('height'), f = Model.flight(v, angle, h);
    Kit.say('speed', v, v + ' m/s'); Kit.say('angle', angle, angle + '°'); Kit.say('height', h, h + ' m');
    const p = Kit.plot(canvas, {x: [0, Math.max(10, f.range * 1.1)], y: [0, Math.max(5, f.peak * 1.2)], xlabel: 'distance (m)', ylabel: 'height (m)'});
    p.curve(x => { const t = x / f.vx; return t <= f.time ? Model.position(v, angle, h, t)[1] : NaN; }, '#215783', 0, f.range);
    for (let t = 0; t <= f.time; t += f.time / 8) { const [x, y] = Model.position(v, angle, h, t); p.point(x, y, '#963d18', 4); }
    p.point(f.vx * f.peakTime, f.peak, '#172533', 6, true);
    const mirror = Model.flight(v, 90 - angle, 0);
    Kit.rows(Kit.get('rows'), [['Horizontal speed (constant)', Kit.fmt(f.vx) + ' m/s'], ['Initial vertical speed', Kit.fmt(f.vy) + ' m/s'], ['Time in the air', Kit.fmt(f.time) + ' s'],
      ['Greatest height', Kit.fmt(f.peak) + ' m'], ['Range', Kit.fmt(f.range) + ' m'], ['Speed on landing', Kit.fmt(f.impactSpeed) + ' m/s']]);
    Kit.get('result').textContent = 'Orange dots are equal time steps: evenly spaced across, because nothing pushes sideways, but bunched near the top, where the vertical speed passes through zero.'
      + (h === 0 ? ' From ground level, ' + angle + '° and ' + (90 - angle) + '° give the same range (' + Kit.fmt(mirror.range, 3) + ' m); 45° gives the longest.' : '');
    canvas.setAttribute('aria-label', 'Trajectory of a projectile launched at ' + v + ' metres per second and ' + angle + ' degrees. Range ' + Kit.fmt(f.range, 3) + ' metres.');
  }
  Kit.bind(['speed', 'angle', 'height'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

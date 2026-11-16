'use strict';
const Model = {
  // Block of mass m (kg) at rest on a slope of angle theta (degrees).
  incline({m, theta, mus, muk, g = 9.81}) {
    const t = theta * Math.PI / 180, weight = m * g, normal = weight * Math.cos(t), parallel = weight * Math.sin(t);
    const maxStatic = mus * normal, slides = parallel > maxStatic + 1e-12;
    const friction = slides ? muk * normal : parallel;
    return {weight, normal, parallel, maxStatic, slides, friction, acceleration: slides ? (parallel - friction) / m : 0,
      criticalAngle: Math.atan(mus) * 180 / Math.PI};
  },
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d');
  function arrow(x0, y0, dx, dy, colour, label) {
    const x1 = x0 + dx, y1 = y0 + dy, a = Math.atan2(dy, dx);
    ctx.strokeStyle = ctx.fillStyle = colour; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 - 11 * Math.cos(a - 0.4), y1 - 11 * Math.sin(a - 0.4)); ctx.lineTo(x1 - 11 * Math.cos(a + 0.4), y1 - 11 * Math.sin(a + 0.4)); ctx.fill();
    ctx.fillText(label, x1 + 8, y1 + 4);
  }
  function draw() {
    const m = Kit.num('mass'), theta = Kit.num('angle'), mus = Kit.num('mus'), muk = Math.min(Kit.num('muk'), mus);
    Kit.say('mass', m, m + ' kg'); Kit.say('angle', theta, theta + '°'); Kit.say('mus', mus, 'μs = ' + mus); Kit.say('muk', muk, 'μk = ' + muk);
    const r = Model.incline({m, theta, mus, muk}), t = theta * Math.PI / 180;
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '15px system-ui, sans-serif';
    const ox = 90, oy = 330, L = 520, tx = ox + L * Math.cos(t), ty = oy - L * Math.sin(t);
    ctx.fillStyle = '#e4e7e2'; ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(tx, oy); ctx.lineTo(tx, ty); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#172533'; ctx.lineWidth = 2; ctx.stroke();
    const cx = ox + 0.55 * L * Math.cos(t), cy = oy - 0.55 * L * Math.sin(t);
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-t); ctx.fillStyle = '#c9a26b'; ctx.fillRect(-34, -46, 68, 46); ctx.strokeRect(-34, -46, 68, 46); ctx.restore();
    const bx = cx - 23 * Math.sin(t), by = cy - 23 * Math.cos(t), scale = 150 / r.weight;
    arrow(bx, by, 0, r.weight * scale, '#172533', 'weight');
    arrow(bx, by, -r.normal * scale * Math.sin(t), -r.normal * scale * Math.cos(t), '#215783', 'normal');
    arrow(bx, by, r.friction * scale * Math.cos(t), -r.friction * scale * Math.sin(t), '#963d18', 'friction');
    Kit.rows(Kit.get('rows'), [['Weight mg', Kit.fmt(r.weight) + ' N'], ['Normal force mg cos θ', Kit.fmt(r.normal) + ' N'],
      ['Pull down the slope mg sin θ', Kit.fmt(r.parallel) + ' N'], ['Largest static friction μs N', Kit.fmt(r.maxStatic) + ' N'],
      ['Friction acting', Kit.fmt(r.friction) + ' N (' + (r.slides ? 'kinetic' : 'static') + ')'], ['Acceleration', Kit.fmt(r.acceleration) + ' m/s²']]);
    Kit.get('result').textContent = r.slides
      ? 'The block slides. The pull down the slope exceeds the largest static friction, so kinetic friction acts and the block accelerates at ' + Kit.fmt(r.acceleration) + ' m/s².'
      : 'The block stays at rest. Static friction matches the pull down the slope exactly. It would start to slide above ' + Kit.fmt(r.criticalAngle, 3) + '°, where tan θ = μs. Mass does not change that angle.';
    canvas.setAttribute('aria-label', 'Block on a ' + theta + ' degree slope with weight, normal and friction arrows. ' + Kit.get('result').textContent);
  }
  Kit.bind(['mass', 'angle', 'mus', 'muk'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

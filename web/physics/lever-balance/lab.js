'use strict';
const Model = {
  // Class 1 lever: load (N) at dLoad from the pivot, effort applied at dEffort on the other side.
  lever(load, dLoad, dEffort) {
    const effort = load * dLoad / dEffort;
    return {effort, advantage: load / effort, torque: load * dLoad};
  },
  // Lifting the load by rise makes the effort end move further, in proportion to the arms.
  travel: (rise, dLoad, dEffort) => rise * dEffort / dLoad,
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d');
  function draw() {
    const load = Kit.num('load'), dLoad = Kit.num('dload'), dEffort = Kit.num('deffort'), r = Model.lever(load, dLoad, dEffort);
    Kit.say('load', load, load + ' N'); Kit.say('dload', dLoad, dLoad + ' m'); Kit.say('deffort', dEffort, dEffort + ' m');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '15px system-ui, sans-serif';
    const px = 300, py = 230, s = 62;
    ctx.fillStyle = '#6b7780'; ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px - 26, py + 60); ctx.lineTo(px + 26, py + 60); ctx.fill();
    ctx.strokeStyle = '#172533'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(px - dLoad * s, py - 4); ctx.lineTo(px + dEffort * s, py - 4); ctx.stroke();
    const size = 24 + Math.sqrt(load) * 3;
    ctx.fillStyle = '#c9a26b'; ctx.fillRect(px - dLoad * s - size / 2, py - 8 - size, size, size);
    ctx.fillStyle = '#172533'; ctx.fillText('load ' + load + ' N', px - dLoad * s - 36, py - size - 16);
    ctx.strokeStyle = ctx.fillStyle = '#963d18'; ctx.lineWidth = 3; const ex = px + dEffort * s, len = Math.min(150, 20 + r.effort * 0.45);
    ctx.beginPath(); ctx.moveTo(ex, py - 12 - len); ctx.lineTo(ex, py - 12); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ex, py - 10); ctx.lineTo(ex - 8, py - 24); ctx.lineTo(ex + 8, py - 24); ctx.fill();
    ctx.fillText('effort ' + Kit.fmt(r.effort, 3) + ' N', ex - 40, py - 20 - len);
    ctx.fillStyle = '#172533'; ctx.fillText(dLoad + ' m', px - dLoad * s / 2 - 12, py + 24); ctx.fillText(dEffort + ' m', px + dEffort * s / 2 - 12, py + 24); ctx.fillText('pivot', px - 18, py + 80);
    const rise = 0.1, travel = Model.travel(rise, dLoad, dEffort);
    Kit.rows(Kit.get('rows'), [['Turning effect of the load', Kit.fmt(r.torque) + ' N·m'], ['Effort needed to balance', Kit.fmt(r.effort) + ' N'],
      ['Mechanical advantage', Kit.fmt(r.advantage)], ['To lift the load 0.1 m the effort end moves', Kit.fmt(travel) + ' m'],
      ['Work on the load / work by the effort', Kit.fmt(load * rise) + ' J / ' + Kit.fmt(r.effort * travel) + ' J']]);
    Kit.get('result').textContent = (r.advantage > 1 ? 'The effort is smaller than the load, but it must move further.' : r.advantage < 1 ? 'The effort is larger than the load, but it moves a shorter distance.' : 'Equal arms: the effort equals the load.')
      + ' A lever trades force for distance; the work done is the same on both sides.';
    canvas.setAttribute('aria-label', 'Lever with a ' + load + ' newton load ' + dLoad + ' metres from the pivot and the effort ' + dEffort + ' metres on the other side. ' + Kit.get('result').textContent);
  }
  Kit.bind(['load', 'dload', 'deffort'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

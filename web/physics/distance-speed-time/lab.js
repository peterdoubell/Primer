'use strict';
const Model = {
  distance: (speed, time) => speed * time,
  // With a steady slowing, the thing stops after speed ÷ slowing seconds.
  stopTime: (speed, slowing) => slowing ? speed / slowing : Infinity,
  travelled(speed, time, slowing) { const t = Math.min(time, Model.stopTime(speed, slowing)); return speed * t - slowing * t * t / 2; },
  speedAt: (speed, time, slowing) => Math.max(0, speed - slowing * time),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const d = Model.travelled(v.speed, v.time, v.friction), stop = Model.stopTime(v.speed, v.friction), p = Kit.plot(canvas, {x: [0, 20], y: [0, 310], xlabel: 'time (s)', ylabel: 'distance (m)'});
  p.curve(t => Model.travelled(v.speed, t, v.friction), '#215783'); p.point(v.time, d, '#963d18', 6); if (v.friction) p.curve(t => Model.distance(v.speed, t), '#9aa6ae', 0, 20, 1.5);
  return {sum: Kit.fmt(d) + ' m in ' + v.time + ' s',
    rows: [['Distance travelled', Kit.fmt(d) + ' m'], ['Speed now', Kit.fmt(Model.speedAt(v.speed, v.time, v.friction)) + ' m/s'], ['Distance with no slowing', Kit.fmt(Model.distance(v.speed, v.time)) + ' m'], ['Time until it stops', Number.isFinite(stop) ? Kit.fmt(stop) + ' s' : 'it never stops']],
    result: v.friction ? 'Friction is a force against the motion. It slows the thing by ' + v.friction + ' m/s every second, so the graph bends over and goes flat when it stops.' : 'With nothing slowing it, the thing keeps the same speed and the graph is a straight line: distance = speed × time. Things stop because forces such as friction act on them.'};
}
function start() {
  const ids = ["speed", "time", "friction"];
  function draw() {
    const v = {};
    for (const id of ids) {
      const node = Kit.get(id); v[id] = node.type === 'range' ? node.valueAsNumber : node.value;
      if (node.type === 'range') Kit.say(id, v[id], String(v[id]));
    }
    const out = render(v);
    Kit.get('sum').textContent = out.sum || '';
    Kit.rows(Kit.get('rows'), out.rows); Kit.get('result').textContent = out.result;
  }
  Kit.bind(ids, draw);
}
if (typeof module === 'object') module.exports = Model; else start();

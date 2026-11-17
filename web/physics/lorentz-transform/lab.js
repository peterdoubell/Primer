'use strict';
const Model = {
  gamma: v => 1 / Math.sqrt(1 - v * v),
  // Units with c = 1: x in light-seconds, t in seconds.
  transform(v, x, t) { const g = Model.gamma(v); return [g * (x - v * t), g * (t - v * x)]; },
  // Invariant interval squared; positive is time-like, negative space-like.
  interval: (x, t) => t * t - x * x,
  kind(x, t) { const s = Model.interval(x, t); return Math.abs(s) < 1e-12 ? 'light-like' : s > 0 ? 'time-like' : 'space-like'; },
  // Velocity of an object moving at w in a frame that itself moves at v.
  addVelocities: (v, w) => (v + w) / (1 + v * w),
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const [x2, t2] = Model.transform(v.v, v.x, v.t), p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5], xlabel: 'x', ylabel: 't'}), m = n => Kit.fmt(n, 4).replace('-', '−'), kind = Model.kind(v.x, v.t);
  p.line(-5, -5, 5, 5, '#d99a00', 1.5, [6, 5]); p.line(-5, 5, 5, -5, '#d99a00', 1.5, [6, 5]);
  p.line(-5 * v.v, -5, 5 * v.v, 5, '#3c7a4b', 2); p.line(-5, -5 * v.v, 5, 5 * v.v, '#3c7a4b', 2); p.text('t′ axis', 4 * v.v, 4, '#3c7a4b'); p.text('x′ axis', 4, 4 * v.v, '#3c7a4b');
  p.point(v.x, v.t, '#963d18', 7); p.text('event', v.x, v.t);
  return {sum: 'Moving frame: x′ = ' + m(x2) + ', t′ = ' + m(t2),
    rows: [['Position (light-seconds)', m(v.x), m(x2)], ['Time (seconds)', m(v.t), m(t2)], ['Interval t² − x²', m(Model.interval(v.x, v.t)), m(Model.interval(x2, t2))], ['Lorentz factor γ', '1', m(Model.gamma(v.v))], ['Object moving at ' + m(v.w) + ' c in the moving frame', m(Model.addVelocities(v.v, v.w)) + ' c', m(v.w) + ' c']],
    result: 'The two observers disagree about where and when, but not about the interval, which is ' + kind + '. ' + (kind === 'space-like' ? 'For a space-like interval even the order in time of this event and the origin can differ between observers.' : kind === 'time-like' ? 'For a time-like interval every observer agrees which came first.' : 'A light ray connects the event to the origin for every observer.') + ' Speeds do not simply add: the combined speed never reaches c. The yellow lines are light rays.'};
}
function start() {
  const ids = ["v", "x", "t", "w"];
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

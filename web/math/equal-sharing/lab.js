'use strict';
const Model = {
  divide: (total, groups) => ({each: Math.floor(total / groups), left: total % groups, exact: total % groups === 0}),
  check: (total, groups) => { const r = Model.divide(total, groups); return groups * r.each + r.left === total; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const r = Model.divide(v.total, v.groups), rows = Math.max(Math.ceil(r.each / 5), Math.ceil(r.left / 5), 1), p = Kit.plot(canvas, {x: [0.3, v.groups + 2], y: [-0.2, rows + 1], grid: false});
  const pile = (x, count, colour) => { for (let k = 0; k < count; k++) p.point(x + (k % 5 - 2) * 0.15, rows + 0.4 - Math.floor(k / 5), colour, Math.min(9, 60 / (v.groups + 2))); };
  for (let g = 1; g <= v.groups; g++) { pile(g, r.each, '#215783'); p.text('group ' + g, g, 0, '#172533', -24, 14); }
  if (r.left) { pile(v.groups + 1.2, r.left, '#963d18'); p.text('left over', v.groups + 1.2, 0, '#963d18', -28, 14); }
  return {sum: v.total + ' ÷ ' + v.groups + ' = ' + r.each + (r.left ? ' remainder ' + r.left : ''),
    rows: [['In each group', String(r.each)], ['Left over', String(r.left)], ['Check', v.groups + ' × ' + r.each + (r.left ? ' + ' + r.left : '') + ' = ' + v.total], ['Times-table fact', r.exact ? v.groups + ' × ' + r.each + ' = ' + v.total : 'the nearest is ' + v.groups + ' × ' + r.each + ' = ' + v.groups * r.each]],
    result: r.exact ? v.total + ' shares equally into ' + v.groups + ' groups of ' + r.each + '. Division undoes multiplication.' : v.total + ' does not share equally into ' + v.groups + ' groups. Each gets ' + r.each + ' and ' + r.left + ' ' + (r.left === 1 ? 'is' : 'are') + ' left over.'};
}
function start() {
  const ids = ["total", "groups"];
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

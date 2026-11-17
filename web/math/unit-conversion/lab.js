'use strict';
const Model = {
  UNITS: {length: {small: 'centimetres', big: 'metres', s: 'cm', b: 'm', per: 100, tool: 'a ruler or tape measure'},
    mass: {small: 'grams', big: 'kilograms', s: 'g', b: 'kg', per: 1000, tool: 'scales'},
    capacity: {small: 'millilitres', big: 'litres', s: 'ml', b: 'l', per: 1000, tool: 'a measuring jug'}},
  toBig: (kind, value) => value / Model.UNITS[kind].per,
  toSmall: (kind, value) => value * Model.UNITS[kind].per,
  split(kind, value) { const per = Model.UNITS[kind].per; return {big: Math.floor(value / per), small: value % per}; },
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
  const u = Model.UNITS[v.kind], s = Model.split(v.kind, v.value), max = 5000 / u.per, p = Kit.plot(canvas, {x: [-max * 0.04, max * 1.04], y: [-1.2, 1.6], grid: false});
  axis(p, 0, max, max / 10); p.line(0, 0.6, Model.toBig(v.kind, v.value), 0.6, '#215783', 16); p.text(u.big, max, 0, '#172533', -50, 44);
  return {sum: v.value + ' ' + u.s + ' = ' + Kit.fmt(Model.toBig(v.kind, v.value), 6) + ' ' + u.b,
    rows: [['Small unit', u.small], ['Large unit', u.big], ['How many small units make one large', String(u.per)], ['As large and small together', s.big + ' ' + u.b + ' ' + s.small + ' ' + u.s], ['Measured with', u.tool]],
    result: 'There are ' + u.per + ' ' + u.small + ' in 1 ' + u.big.replace(/s$/, '') + '. To change ' + u.small + ' to ' + u.big + ', divide by ' + u.per + '.'};
}
function start() {
  const ids = ["kind", "value"];
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

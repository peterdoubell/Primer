"""Generate the early and middle mathematics activities that share one page shell.

Each activity has labelled controls, a drawing, a table of values and a plain result line.
The model of each is a small pure object, tested in tests/activity-models.test.cjs.

Run: python tools/build_math_number_activities.py. It rewrites web/math/<slug>/ and adds registry entries.
"""
import json
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / 'web'

HTML = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@TITLE@ · Primer</title>
<link rel="stylesheet" href="/app/activities/kit.css">
<script defer src="/app/activities/kit.js"></script>
<script defer src="lab.js"></script>
</head>
<body><main>
<a href="/app/#/node/@NODE@">Return to @BACK@</a>
<h1>@TITLE@</h1>
<p class="lede">@LEDE@</p>
<div class="controls">
@CONTROLS@
</div>
<p id="sum" class="big" style="font-weight:700"></p>
<figure>
<canvas id="graph" width="720" height="@HEIGHT@" role="img" aria-label="@ARIA@ The table below gives the same values."></canvas>
</figure>
<table><caption>@CAPTION@</caption><thead><tr>@HEADS@</tr></thead><tbody id="rows"></tbody></table>
<p id="result" role="status"></p>
</main></body></html>
'''

JS = '''\'use strict\';
const Model = {
@MODEL@
};
// A horizontal number line with ticks and labels at y = 0.
function axis(p, min, max, step) {
  p.line(min, 0, max, 0, '#172533', 2);
  for (let value = min; value <= max + 1e-9; value += step) { p.line(value, -0.12, value, 0.12, '#172533', 1.5); p.text(Kit.fmt(value), value, 0, '#172533', -8, 24); }
}
function render(v) {
  const canvas = Kit.get('graph');
@RENDER@
}
function start() {
  const ids = @IDS@;
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
'''


def slider(i, label, lo, hi, value, step=1):
    return '<div><label for="%s">%s</label><input type="range" id="%s" min="%s" max="%s" step="%s" value="%s"><output id="%s-out" for="%s"></output></div>' % (i, label, i, lo, hi, step, value, i, i)


def select(i, label, options):
    return '<div><label for="%s">%s</label><select id="%s">%s</select></div>' % (
        i, label, i, ''.join('<option value="%s">%s</option>' % pair for pair in options))


ACTS = []


def add(slug, node, back, title, lede, controls, heads, model, render, height=260, aria='', caption='Values'):
    ACTS.append(dict(slug=slug, node=node, back=back, title=title, lede=lede, controls=controls, heads=heads, model=model,
                     render=render, height=height, aria=aria or title + '.', caption=caption))


add('bigger-smaller', 'math.0.compare', 'Bigger and Smaller', 'Which is bigger?',
    'Choose two numbers. Line up the dots and see which row is longer.',
    [('a', slider('a', 'First number', 0, 20, 7)), ('b', slider('b', 'Second number', 0, 20, 4))], ['Question', 'Answer'],
    '''  sign: (a, b) => a > b ? '>' : a < b ? '<' : '=',
  words: (a, b) => a > b ? a + ' is bigger than ' + b : a < b ? a + ' is smaller than ' + b : a + ' is the same as ' + b,
  difference: (a, b) => Math.abs(a - b),''',
    '''  const p = Kit.plot(canvas, {x: [0, 21.5], y: [0.3, 2.7], grid: false});
  for (let i = 1; i <= v.a; i++) p.point(i, 2, '#215783', 9);
  for (let i = 1; i <= v.b; i++) p.point(i, 1, '#963d18', 9);
  p.text(String(v.a), Math.max(v.a, 0.2), 2, '#215783', 14, 6); p.text(String(v.b), Math.max(v.b, 0.2), 1, '#963d18', 14, 6);
  return {sum: v.a + ' ' + Model.sign(v.a, v.b) + ' ' + v.b,
    rows: [['Which is bigger?', v.a === v.b ? 'neither' : String(Math.max(v.a, v.b))], ['Which is smaller?', v.a === v.b ? 'neither' : String(Math.min(v.a, v.b))], ['How many more?', String(Model.difference(v.a, v.b))]],
    result: Model.words(v.a, v.b) + '. The open end of the sign always faces the bigger number.'};''', height=200,
    aria='Two rows of dots, one for each number.')

add('count-to-ten', 'math.0.counting', 'Counting', 'Count up and count back',
    'Slide to choose how many. Touch each dot once as you count.',
    [('n', slider('n', 'How many', 0, 10, 6))], ['Count', 'Numbers'],
    '''  forward: n => Array.from({length: n}, (_, i) => i + 1),
  back: n => Array.from({length: n}, (_, i) => n - i),
  WORDS: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'],''',
    '''  const p = Kit.plot(canvas, {x: [0, 11], y: [0, 2], grid: false});
  for (let i = 1; i <= 10; i++) { p.point(i, 1, i <= v.n ? '#215783' : '#c3ccd2', 14, i > v.n); if (i <= v.n) p.text(String(i), i, 1, '#172533', -5, 40); }
  return {sum: v.n + ' — ' + Model.WORDS[v.n],
    rows: [['Counting up', Model.forward(v.n).join(', ') || 'nothing to count'], ['Counting back', Model.back(v.n).join(', ') || 'nothing to count'], ['One more', v.n < 10 ? String(v.n + 1) : '11'], ['One fewer', v.n > 0 ? String(v.n - 1) : 'none left to take']],
    result: 'The last number you say tells you how many there are: ' + Model.WORDS[v.n] + '.'};''', height=180,
    aria='A row of ten dots with the counted ones filled in.')

add('numbers-to-twenty', 'math.0.numbers20', 'Numbers to Twenty', 'Tens and ones up to twenty',
    'Numbers after ten are one ten and some more. Fill the frames and read the number.',
    [('n', slider('n', 'Number', 1, 20, 13))], ['Question', 'Answer'],
    '''  WORDS: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty'],
  split: n => ({tens: Math.floor(n / 10), ones: n % 10}),
  before: n => n - 1, after: n => n + 1,''',
    '''  const p = Kit.plot(canvas, {x: [0, 12.5], y: [0, 3], grid: false});
  for (let i = 0; i < 20; i++) { const frame = Math.floor(i / 10), k = i % 10, x = 1 + (k % 5) + frame * 6, y = 2 - Math.floor(k / 5); p.point(x, y, i < v.n ? (frame ? '#963d18' : '#215783') : '#c3ccd2', 13, i >= v.n); }
  const s = Model.split(v.n);
  return {sum: v.n + ' — ' + Model.WORDS[v.n],
    rows: [['Tens', String(s.tens)], ['Ones', String(s.ones)], ['Number before', String(Model.before(v.n))], ['Number after', String(Model.after(v.n))]],
    result: v.n + ' is ' + s.tens + (s.tens === 1 ? ' ten' : ' tens') + ' and ' + s.ones + (s.ones === 1 ? ' one' : ' ones') + '. It comes after ' + Model.before(v.n) + ' and before ' + Model.after(v.n) + '.'};''', height=220,
    aria='Two frames of ten spaces, filled to show the number.')

add('what-comes-next', 'math.0.patterns', 'Patterns', 'What comes next?',
    'A pattern follows a rule. Find the rule and you can say what comes next.',
    [('kind', select('kind', 'Pattern', [('ab', 'red, blue, red, blue'), ('aab', 'red, red, blue'), ('abc', 'red, blue, green'), ('plus2', 'growing by 2'), ('plus3', 'growing by 3')])),
     ('n', slider('n', 'How many are shown', 3, 10, 6))], ['Position', 'Item'],
    '''  PATTERNS: {ab: {unit: ['red', 'blue']}, aab: {unit: ['red', 'red', 'blue']}, abc: {unit: ['red', 'blue', 'green']}, plus2: {first: 1, step: 2}, plus3: {first: 2, step: 3}},
  // Item at position i, counting from 1.
  term(kind, i) { const p = Model.PATTERNS[kind]; return p.unit ? p.unit[(i - 1) % p.unit.length] : p.first + (i - 1) * p.step; },
  sequence: (kind, n) => Array.from({length: n}, (_, i) => Model.term(kind, i + 1)),
  rule(kind) { const p = Model.PATTERNS[kind]; return p.unit ? 'Repeat ' + p.unit.join(', ') + ' again and again.' : 'Start at ' + p.first + ' and add ' + p.step + ' each time.'; },''',
    '''  const items = Model.sequence(v.kind, v.n), next = Model.term(v.kind, v.n + 1), colours = {red: '#b3261e', blue: '#215783', green: '#3c7a4b'}, growing = typeof next === 'number';
  const p = Kit.plot(canvas, {x: [0, 12], y: [0, growing ? 36 : 2], grid: false});
  [...items, next].forEach((item, i) => {
    const last = i === items.length;
    if (growing) { p.line(i + 1, 0, i + 1, item, last ? '#9aa6ae' : '#215783', 18); p.text(last ? '?' : String(item), i + 1, item, '#172533', -6, -8); }
    else { p.point(i + 1, 1, last ? '#ffffff' : colours[item], 15); if (last) p.text('?', i + 1, 1, '#172533', -5, 6); }
  });
  return {sum: items.join(', ') + ', …',
    rows: items.map((item, i) => [String(i + 1), String(item)]),
    result: 'Rule: ' + Model.rule(v.kind) + ' So the next one is ' + next + '.'};''', height=240,
    aria='The pattern drawn in order, with a question mark for the next item.', caption='The pattern so far')

add('shape-sides', 'math.0.shapes', 'Shapes All Around', 'Shapes and their sides',
    'Choose a shape. Count its straight sides and its corners.',
    [('shape', select('shape', 'Shape', [('circle', 'Circle'), ('triangle', 'Triangle'), ('square', 'Square'), ('rectangle', 'Rectangle'), ('pentagon', 'Pentagon'), ('hexagon', 'Hexagon')]))], ['Shape', 'Straight sides', 'Corners'],
    '''  SHAPES: {circle: 0, triangle: 3, square: 4, rectangle: 4, pentagon: 5, hexagon: 6},
  sides: shape => Model.SHAPES[shape],
  corners: shape => Model.SHAPES[shape],
  // Corner points of the drawing, in a box from -1 to 1.
  points(shape) {
    if (shape === 'circle') return [];
    if (shape === 'rectangle') return [[-1, -0.55], [1, -0.55], [1, 0.55], [-1, 0.55]];
    const n = Model.SHAPES[shape], turn = shape === 'square' ? Math.PI / 4 : -Math.PI / 2;
    return Array.from({length: n}, (_, i) => [Math.cos(turn + 2 * Math.PI * i / n), Math.sin(turn + 2 * Math.PI * i / n)]);
  },''',
    '''  const ctx = canvas.getContext('2d'), cx = canvas.width / 2, cy = canvas.height / 2, r = canvas.height * 0.38, points = Model.points(v.shape);
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.lineWidth = 5; ctx.strokeStyle = '#215783'; ctx.fillStyle = '#dbe8f2'; ctx.beginPath();
  if (!points.length) ctx.arc(cx, cy, r, 0, 2 * Math.PI); else points.forEach(([x, y], i) => i ? ctx.lineTo(cx + r * x, cy + r * y) : ctx.moveTo(cx + r * x, cy + r * y));
  ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#963d18'; for (const [x, y] of points) { ctx.beginPath(); ctx.arc(cx + r * x, cy + r * y, 8, 0, 2 * Math.PI); ctx.fill(); }
  const n = Model.sides(v.shape);
  return {sum: v.shape[0].toUpperCase() + v.shape.slice(1),
    rows: Object.keys(Model.SHAPES).map(shape => [shape, String(Model.sides(shape)), String(Model.corners(shape))]),
    result: n ? 'A ' + v.shape + ' has ' + n + ' straight sides and ' + n + ' corners. A shape with straight sides has as many corners as sides.' : 'A circle has no straight sides and no corners. It is one curved line.'};''', height=300,
    aria='The chosen shape with its corners marked.', caption='All six shapes')

add('column-addition', 'math.1.addition', 'Addition', 'Adding with tens and ones',
    'Add the ones first. If they make ten or more, carry one ten.',
    [('a', slider('a', 'First number', 0, 99, 47)), ('b', slider('b', 'Second number', 0, 99, 38))], ['Step', 'Working'],
    '''  add(a, b) {
    const ones = a % 10 + b % 10, carry = ones >= 10 ? 1 : 0, tens = Math.floor(a / 10) + Math.floor(b / 10) + carry;
    return {sum: a + b, ones, carry, onesDigit: ones % 10, tens};
  },''',
    '''  const r = Model.add(v.a, v.b), p = Kit.plot(canvas, {x: [-8, 208], y: [-1.2, 1.6], grid: false});
  axis(p, 0, 200, 20); p.arrow(0, 0.5, v.a, 0.5, '#215783'); p.arrow(v.a, 1, r.sum, 1, '#963d18'); p.point(r.sum, 0, '#172533', 6);
  p.text(String(v.a), v.a / 2, 0.5, '#215783', -8, -8); p.text('+ ' + v.b, v.a + v.b / 2, 1, '#963d18', -12, -8);
  return {sum: v.a + ' + ' + v.b + ' = ' + r.sum,
    rows: [['Add the ones', (v.a % 10) + ' + ' + (v.b % 10) + ' = ' + r.ones], ['Carry', r.carry ? 'write ' + r.onesDigit + ', carry 1 ten' : 'nothing to carry'],
      ['Add the tens', Math.floor(v.a / 10) + ' + ' + Math.floor(v.b / 10) + (r.carry ? ' + 1' : '') + ' = ' + r.tens], ['Answer', r.tens + ' tens and ' + r.onesDigit + ' ones = ' + r.sum]],
    result: 'Adding in either order gives the same answer: ' + v.b + ' + ' + v.a + ' is also ' + r.sum + '.'};''',
    aria='A number line with one jump for each number.', caption='Working')

add('column-subtraction', 'math.1.subtraction', 'Subtraction', 'Taking away and finding the difference',
    'Subtraction takes away, and it also measures how far apart two numbers are.',
    [('a', slider('a', 'Start with', 0, 99, 52)), ('b', slider('b', 'Take away', 0, 99, 27))], ['Step', 'Working'],
    '''  subtract(a, b) {
    const exchange = a % 10 < b % 10, ones = a % 10 + (exchange ? 10 : 0) - b % 10, tens = Math.floor(a / 10) - (exchange ? 1 : 0) - Math.floor(b / 10);
    return {difference: a - b, exchange, ones, tens, possible: a >= b};
  },
  check: (a, b) => (a - b) + b === a,''',
    '''  const r = Model.subtract(v.a, v.b), p = Kit.plot(canvas, {x: [-4, 104], y: [-1.2, 1.6], grid: false});
  axis(p, 0, 100, 10); p.arrow(0, 0.5, v.a, 0.5, '#215783');
  if (r.possible) { p.arrow(v.a, 1, r.difference, 1, '#963d18'); p.point(r.difference, 0, '#172533', 6); p.text('− ' + v.b, (v.a + r.difference) / 2, 1, '#963d18', -12, -8); }
  p.text(String(v.a), v.a / 2, 0.5, '#215783', -8, -8);
  if (!r.possible) return {sum: v.a + ' − ' + v.b, rows: [['Can you take ' + v.b + ' from ' + v.a + '?', 'not without going below zero'], ['How far apart are they?', String(v.b - v.a)]],
    result: 'There are only ' + v.a + ' to start with, so you cannot take away ' + v.b + '. The two numbers are ' + (v.b - v.a) + ' apart.'};
  return {sum: v.a + ' − ' + v.b + ' = ' + r.difference,
    rows: [['Exchange', r.exchange ? 'yes: swap 1 ten for 10 ones' : 'not needed'], ['Subtract the ones', (v.a % 10 + (r.exchange ? 10 : 0)) + ' − ' + (v.b % 10) + ' = ' + r.ones],
      ['Subtract the tens', (Math.floor(v.a / 10) - (r.exchange ? 1 : 0)) + ' − ' + Math.floor(v.b / 10) + ' = ' + r.tens], ['Check by adding', r.difference + ' + ' + v.b + ' = ' + v.a]],
    result: 'Addition undoes subtraction, so you can always check: ' + r.difference + ' + ' + v.b + ' = ' + v.a + '.'};''',
    aria='A number line with a jump forward and a jump back.', caption='Working')

add('times-table-array', 'math.1.multiplication', 'Multiplication', 'Rows and columns: the times tables',
    'Multiplying counts equal rows. Change the rows and columns and read the table.',
    [('a', slider('a', 'Rows', 1, 12, 4)), ('b', slider('b', 'In each row', 1, 12, 6))], ['Fact', 'Answer'],
    '''  product: (a, b) => a * b,
  table: a => Array.from({length: 12}, (_, i) => [a + ' × ' + (i + 1), a * (i + 1)]),
  // The product as repeated addition.
  repeated: (a, b) => Array(a).fill(b).join(' + '),''',
    '''  const p = Kit.plot(canvas, {x: [0, 13], y: [0, 13], grid: false});
  for (let row = 1; row <= v.a; row++) for (let col = 1; col <= v.b; col++) p.point(col, 13 - row, '#215783', 8);
  return {sum: v.a + ' × ' + v.b + ' = ' + Model.product(v.a, v.b),
    rows: Model.table(v.a).map(([fact, answer]) => [fact, String(answer)]),
    result: v.a + ' rows of ' + v.b + ' is ' + Model.repeated(v.a, v.b) + ' = ' + Model.product(v.a, v.b) + '. Turn the array on its side and it is ' + v.b + ' rows of ' + v.a + ': the same ' + Model.product(v.a, v.b) + '.'};''', height=420,
    aria='An array of dots in rows and columns.', caption='The times table for the number of rows')

add('equal-sharing', 'math.1.division', 'Division', 'Sharing into equal groups',
    'Share the counters out one at a time. Whatever cannot be shared equally is left over.',
    [('total', slider('total', 'Counters to share', 1, 60, 23)), ('groups', slider('groups', 'Groups', 1, 12, 4))], ['Question', 'Answer'],
    '''  divide: (total, groups) => ({each: Math.floor(total / groups), left: total % groups, exact: total % groups === 0}),
  check: (total, groups) => { const r = Model.divide(total, groups); return groups * r.each + r.left === total; },''',
    '''  const r = Model.divide(v.total, v.groups), rows = Math.max(Math.ceil(r.each / 5), Math.ceil(r.left / 5), 1), p = Kit.plot(canvas, {x: [0.3, v.groups + 2], y: [-0.2, rows + 1], grid: false});
  const pile = (x, count, colour) => { for (let k = 0; k < count; k++) p.point(x + (k % 5 - 2) * 0.15, rows + 0.4 - Math.floor(k / 5), colour, Math.min(9, 60 / (v.groups + 2))); };
  for (let g = 1; g <= v.groups; g++) { pile(g, r.each, '#215783'); p.text('group ' + g, g, 0, '#172533', -24, 14); }
  if (r.left) { pile(v.groups + 1.2, r.left, '#963d18'); p.text('left over', v.groups + 1.2, 0, '#963d18', -28, 14); }
  return {sum: v.total + ' ÷ ' + v.groups + ' = ' + r.each + (r.left ? ' remainder ' + r.left : ''),
    rows: [['In each group', String(r.each)], ['Left over', String(r.left)], ['Check', v.groups + ' × ' + r.each + (r.left ? ' + ' + r.left : '') + ' = ' + v.total], ['Times-table fact', r.exact ? v.groups + ' × ' + r.each + ' = ' + v.total : 'the nearest is ' + v.groups + ' × ' + r.each + ' = ' + v.groups * r.each]],
    result: r.exact ? v.total + ' shares equally into ' + v.groups + ' groups of ' + r.each + '. Division undoes multiplication.' : v.total + ' does not share equally into ' + v.groups + ' groups. Each gets ' + r.each + ' and ' + r.left + ' ' + (r.left === 1 ? 'is' : 'are') + ' left over.'};''', height=380,
    aria='Counters dealt into groups, with any left over shown apart.')

add('halves-and-quarters', 'math.1.fractions-intro', 'Halves and Quarters', 'Equal parts of a whole',
    'A fraction names equal parts. The bottom number says how many equal parts; the top says how many you have.',
    [('parts', select('parts', 'Equal parts', [('2', '2 (halves)'), ('4', '4 (quarters)'), ('3', '3 (thirds)'), ('8', '8 (eighths)')])), ('shaded', slider('shaded', 'Parts shaded', 0, 8, 1))], ['Question', 'Answer'],
    '''  NAMES: {2: ['half', 'halves'], 3: ['third', 'thirds'], 4: ['quarter', 'quarters'], 8: ['eighth', 'eighths']},
  COUNT: ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'],
  gcd: (a, b) => b ? Model.gcd(b, a % b) : a,
  // [numerator, denominator] in lowest terms.
  simplest(n, d) { const g = Model.gcd(n, d) || 1; return [n / g, d / g]; },
  name(n, d) { if (n === d) return 'one whole'; if (n === 0) return 'nothing'; return Model.COUNT[n] + ' ' + Model.NAMES[d][n === 1 ? 0 : 1]; },''',
    '''  const d = Number(v.parts), n = Math.min(v.shaded, d), p = Kit.plot(canvas, {x: [-0.2, 8.2], y: [0, 3], grid: false}), w = 8 / d, [sn, sd] = Model.simplest(n, d);
  for (let i = 0; i < d; i++) { if (i < n) for (let k = 0; k <= 30; k++) p.line(i * w + 0.03, 1 + k / 20, (i + 1) * w - 0.03, 1 + k / 20, '#8fb6d6', 6); p.line(i * w, 1, i * w, 2.5, '#172533', 2); }
  p.line(8, 1, 8, 2.5, '#172533', 2); p.line(0, 1, 8, 1, '#172533', 2); p.line(0, 2.5, 8, 2.5, '#172533', 2);
  return {sum: n + '/' + d + ' — ' + Model.name(n, d),
    rows: [['Equal parts in the whole', String(d)], ['Parts shaded', String(n)], ['Parts not shaded', String(d - n)], ['The same amount, written most simply', n === d ? '1' : n === 0 ? '0' : sn + '/' + sd]],
    result: n === d ? 'All ' + d + ' parts are shaded, so that is one whole.' : 'The parts must be equal. ' + (sd !== d && n ? n + '/' + d + ' is the same amount as ' + sn + '/' + sd + '.' : 'Here ' + n + ' of ' + d + ' equal parts are shaded.')};''', height=220,
    aria='A bar cut into equal parts with some shaded.')

add('unit-conversion', 'math.1.measurement', 'Measuring Things', 'Measuring with small and large units',
    'Choose what to measure. A big unit is made of many small ones.',
    [('kind', select('kind', 'Measure', [('length', 'Length'), ('mass', 'Mass'), ('capacity', 'Liquid capacity')])), ('value', slider('value', 'Amount in the small unit', 0, 5000, 1250, 50))], ['Question', 'Answer'],
    '''  UNITS: {length: {small: 'centimetres', big: 'metres', s: 'cm', b: 'm', per: 100, tool: 'a ruler or tape measure'},
    mass: {small: 'grams', big: 'kilograms', s: 'g', b: 'kg', per: 1000, tool: 'scales'},
    capacity: {small: 'millilitres', big: 'litres', s: 'ml', b: 'l', per: 1000, tool: 'a measuring jug'}},
  toBig: (kind, value) => value / Model.UNITS[kind].per,
  toSmall: (kind, value) => value * Model.UNITS[kind].per,
  split(kind, value) { const per = Model.UNITS[kind].per; return {big: Math.floor(value / per), small: value % per}; },''',
    '''  const u = Model.UNITS[v.kind], s = Model.split(v.kind, v.value), max = 5000 / u.per, p = Kit.plot(canvas, {x: [-max * 0.04, max * 1.04], y: [-1.2, 1.6], grid: false});
  axis(p, 0, max, max / 10); p.line(0, 0.6, Model.toBig(v.kind, v.value), 0.6, '#215783', 16); p.text(u.big, max, 0, '#172533', -50, 44);
  return {sum: v.value + ' ' + u.s + ' = ' + Kit.fmt(Model.toBig(v.kind, v.value), 6) + ' ' + u.b,
    rows: [['Small unit', u.small], ['Large unit', u.big], ['How many small units make one large', String(u.per)], ['As large and small together', s.big + ' ' + u.b + ' ' + s.small + ' ' + u.s], ['Measured with', u.tool]],
    result: 'There are ' + u.per + ' ' + u.small + ' in 1 ' + u.big.replace(/s$/, '') + '. To change ' + u.small + ' to ' + u.big + ', divide by ' + u.per + '.'};''',
    aria='A scale in the large unit with a bar showing the amount.')

add('place-value-digits', 'math.1.place-value', 'Place Value', 'What each digit is worth',
    'The place of a digit tells you its value. Move the slider and read each column.',
    [('n', slider('n', 'Number', 0, 9999, 3407))], ['Place', 'Digit', 'Value'],
    '''  PLACES: ['thousands', 'hundreds', 'tens', 'ones'],
  digits: n => Model.PLACES.map((place, i) => { const unit = 10 ** (3 - i), digit = Math.floor(n / unit) % 10; return {place, digit, value: digit * unit}; }),
  expanded(n) { const parts = Model.digits(n).filter(d => d.value).map(d => d.value); return parts.length ? parts.join(' + ') : '0'; },''',
    '''  const digits = Model.digits(v.n), p = Kit.plot(canvas, {x: [0, 5], y: [-1.5, 10], grid: false}), colours = ['#6b3fa0', '#963d18', '#3c7a4b', '#215783'];
  digits.forEach((d, i) => { for (let k = 0; k < d.digit; k++) p.point(i + 1, k + 1, colours[i], 8); p.text(d.place, i + 1, 0, '#172533', -30, 22); p.text(String(d.digit), i + 1, 0, colours[i], -5, 44); });
  p.line(0.4, 0.3, 4.6, 0.3, '#172533', 2);
  return {sum: String(v.n) + ' = ' + Model.expanded(v.n),
    rows: digits.map(d => [d.place, String(d.digit), String(d.value)]),
    result: 'Each place is worth ten times the place to its right. ' + (digits.some(d => d.digit === 0) && v.n > 9 ? 'A zero holds a place open so the other digits keep their value.' : 'Ten ones make one ten, ten tens make one hundred.')};''', height=320,
    aria='Four columns of counters, one for each place.', caption='Digits')

add('plot-a-point', 'math.2.coordinates', 'The Coordinate Plane', 'Plotting a point',
    'A point is named by two numbers: across first, then up. Move the point and read where it lies.',
    [('x', slider('x', 'x (across)', -6, 6, 3)), ('y', slider('y', 'y (up)', -6, 6, -2))], ['Question', 'Answer'],
    '''  quadrant(x, y) {
    if (!x && !y) return 'at the origin'; if (!y) return 'on the x-axis'; if (!x) return 'on the y-axis';
    return 'in the ' + (x > 0 ? (y > 0 ? 'first' : 'fourth') : (y > 0 ? 'second' : 'third')) + ' quadrant';
  },
  distance: (x, y) => Math.hypot(x, y),
  reflectX: (x, y) => [x, -y], reflectY: (x, y) => [-x, y],''',
    '''  const p = Kit.plot(canvas, {x: [-7, 7], y: [-7, 7], xlabel: 'x', ylabel: 'y'}), fx = Model.reflectX(v.x, v.y), fy = Model.reflectY(v.x, v.y);
  p.line(v.x, 0, v.x, v.y, '#963d18', 2, [6, 5]); p.line(0, v.y, v.x, v.y, '#963d18', 2, [6, 5]); p.line(0, 0, v.x, v.y, '#9aa6ae', 1.5);
  p.point(fx[0], fx[1], '#215783', 5, true); p.point(fy[0], fy[1], '#3c7a4b', 5, true); p.point(v.x, v.y, '#963d18', 7); p.text(('(' + v.x + ', ' + v.y + ')').replace(/-/g, '−'), v.x, v.y);
  return {sum: ('(' + v.x + ', ' + v.y + ')').replace(/-/g, '−'),
    rows: [['Where is it?', Model.quadrant(v.x, v.y)], ['Distance from the origin', Kit.fmt(Model.distance(v.x, v.y))], ['Mirror image in the x-axis', '(' + fx.join(', ') + ')'], ['Mirror image in the y-axis', '(' + fy.join(', ') + ')']],
    result: 'Go ' + Math.abs(v.x) + (v.x < 0 ? ' left' : ' right') + ', then ' + Math.abs(v.y) + (v.y < 0 ? ' down' : ' up') + '. The point is ' + Model.quadrant(v.x, v.y) + '.'};''', height=560,
    aria='A coordinate grid with the point and its two mirror images.')

add('decimal-arithmetic', 'math.2.decimals', 'Decimals', 'Calculating with decimals',
    'Decimals extend place value to tenths and hundredths. Line up the points to add; count the places to multiply.',
    [('a', slider('a', 'First number', 0, 10, 3.75, 0.05)), ('op', select('op', 'Operation', [('add', 'Add'), ('subtract', 'Subtract'), ('multiply', 'Multiply')])), ('b', slider('b', 'Second number', 0, 10, 1.4, 0.05))], ['Step', 'Value'],
    '''  SIGNS: {add: '+', subtract: '−', multiply: '×'},
  // Work in whole hundredths so the answers are exact.
  calc(a, b, op) { const A = Math.round(a * 100), B = Math.round(b * 100); return op === 'add' ? (A + B) / 100 : op === 'subtract' ? (A - B) / 100 : Math.round(A * B) / 10000; },
  round: (value, places) => Math.round(value * 10 ** places + (value < 0 ? -1e-9 : 1e-9)) / 10 ** places,
  places(value) { const text = String(Math.round(Math.abs(value) * 10000) / 10000); return text.includes('.') ? text.split('.')[1].length : 0; },
  show: value => String(Math.round(value * 10000) / 10000).replace('-', '−'),''',
    '''  const r = Model.calc(v.a, v.b, v.op), max = v.op === 'multiply' ? 100 : 20, min = v.op === 'subtract' ? -10 : 0, p = Kit.plot(canvas, {x: [min - max * 0.03, max * 1.03], y: [-1.2, 1.6], grid: false});
  axis(p, min, max, (max - min) / 10); p.point(v.a, 0, '#215783', 6); p.point(v.b, 0, '#3c7a4b', 6); p.point(r, 0, '#963d18', 8); p.text(Model.show(r), r, 0, '#963d18', -10, -14);
  return {sum: Model.show(v.a) + ' ' + Model.SIGNS[v.op] + ' ' + Model.show(v.b) + ' = ' + Model.show(r),
    rows: [['Answer', Model.show(r)], ['Decimal places in the answer', String(Model.places(r))], ['Rounded to one decimal place', Model.show(Model.round(r, 1))], ['Rounded to the nearest whole number', Model.show(Model.round(r, 0))]],
    result: v.op === 'multiply' ? 'Multiply as whole numbers, then place the point: the answer has as many decimal places as the two numbers together (before any end zeros are dropped).' : 'Line up the decimal points so tenths sit under tenths and hundredths under hundredths, then ' + v.op + ' as usual.'};''',
    aria='A number line marking the two numbers and the answer.')

add('fraction-arithmetic', 'math.2.fractions', 'Fractions', 'Adding, multiplying and comparing fractions',
    'Set two fractions and an operation. To add or subtract, first make the bottom numbers the same.',
    [('n1', slider('n1', 'First top number', 0, 12, 2)), ('d1', slider('d1', 'First bottom number', 1, 12, 3)), ('op', select('op', 'Operation', [('add', 'Add'), ('subtract', 'Subtract'), ('multiply', 'Multiply'), ('divide', 'Divide')])),
     ('n2', slider('n2', 'Second top number', 0, 12, 3)), ('d2', slider('d2', 'Second bottom number', 1, 12, 4))], ['Step', 'Value'],
    '''  SIGNS: {add: '+', subtract: '−', multiply: '×', divide: '÷'},
  gcd: (a, b) => b ? Model.gcd(b, a % b) : Math.abs(a),
  lcm: (a, b) => a / Model.gcd(a, b) * b,
  // [numerator, denominator] in lowest terms with a positive denominator.
  simplify(n, d) { const g = Model.gcd(n, d) || 1, s = d < 0 ? -1 : 1; return [s * n / g, s * d / g]; },
  calc(n1, d1, n2, d2, op) {
    if (op === 'add') return Model.simplify(n1 * d2 + n2 * d1, d1 * d2);
    if (op === 'subtract') return Model.simplify(n1 * d2 - n2 * d1, d1 * d2);
    if (op === 'multiply') return Model.simplify(n1 * n2, d1 * d2);
    return n2 === 0 ? null : Model.simplify(n1 * d2, d1 * n2);
  },
  compare: (n1, d1, n2, d2) => Math.sign(n1 * d2 - n2 * d1),
  text: ([n, d]) => (d === 1 ? String(n) : n + '/' + d).replace('-', '−'),
  mixed([n, d]) { if (d === 1 || Math.abs(n) < d) return Model.text([n, d]); const whole = Math.trunc(n / d); return (whole + ' and ' + Math.abs(n % d) + '/' + d).replace('-', '−'); },''',
    '''  const r = Model.calc(v.n1, v.d1, v.n2, v.d2, v.op), common = Model.lcm(v.d1, v.d2), p = Kit.plot(canvas, {x: [-0.1, 4.1], y: [0, 3.2], grid: false});
  const bar = (n, d, y, colour) => { const top = Math.min(n / d, 4); for (let k = 0; k <= 16; k++) p.line(0, y + k / 40, top, y + k / 40, colour, 3); for (let i = 0; i <= 4 * d; i++) p.line(i / d, y, i / d, y + 0.4, '#172533', i % d ? 0.6 : 2); p.line(0, y, 4, y); p.line(0, y + 0.4, 4, y + 0.4); };
  bar(v.n1, v.d1, 2.4, '#8fb6d6'); bar(v.n2, v.d2, 1.4, '#e3b89c'); if (r && r[0] >= 0) bar(r[0], r[1], 0.4, '#a9cdb1');
  p.text(v.n1 + '/' + v.d1, 0, 2.8, '#172533', 0, -10); p.text(v.n2 + '/' + v.d2, 0, 1.8, '#172533', 0, -10); if (r && r[0] >= 0) p.text('answer', 0, 0.8, '#172533', 0, -10);
  const order = Model.compare(v.n1, v.d1, v.n2, v.d2), same = v.op === 'add' || v.op === 'subtract';
  return {sum: v.n1 + '/' + v.d1 + ' ' + Model.SIGNS[v.op] + ' ' + v.n2 + '/' + v.d2 + ' = ' + (r ? Model.text(r) : 'not defined'),
    rows: [['Common bottom number', same ? String(common) : 'not needed'], ['Rewritten', same ? (v.n1 * common / v.d1) + '/' + common + ' and ' + (v.n2 * common / v.d2) + '/' + common : v.op === 'divide' ? 'multiply by ' + v.d2 + '/' + v.n2 : 'tops together, bottoms together'],
      ['Answer in lowest terms', r ? Model.text(r) : 'cannot divide by zero'], ['As a mixed number', r ? Model.mixed(r) : '—'], ['As a decimal', r ? Kit.fmt(r[0] / r[1]) : '—'],
      ['Which is bigger?', order ? (order > 0 ? v.n1 + '/' + v.d1 : v.n2 + '/' + v.d2) : 'they are equal']],
    result: same ? 'You can only add or subtract parts of the same size, so both fractions are rewritten over ' + common + '.' : v.op === 'multiply' ? 'Multiply the tops and multiply the bottoms, then simplify.' : 'Dividing by a fraction is the same as multiplying by it turned upside down.'};''', height=300,
    aria='Bars from 0 to 4 showing the two fractions and the answer.')

add('area-perimeter-volume', 'math.2.geometry', 'Area, Perimeter and Volume', 'Measuring shapes and solids',
    'Perimeter is the distance round a shape, area is the surface it covers, and volume is the space a solid fills.',
    [('shape', select('shape', 'Shape', [('rectangle', 'Rectangle'), ('triangle', 'Right-angled triangle'), ('circle', 'Circle'), ('cuboid', 'Cuboid')])),
     ('a', slider('a', 'Length a (or radius)', 1, 12, 6)), ('b', slider('b', 'Length b', 1, 12, 4)), ('c', slider('c', 'Height c (cuboid only)', 1, 12, 3))], ['Measure', 'Rule', 'Value'],
    '''  measure(shape, a, b, c) {
    if (shape === 'rectangle') return [['Perimeter', '2 × (a + b)', 2 * (a + b), 'units'], ['Area', 'a × b', a * b, 'square units']];
    if (shape === 'triangle') { const h = Math.hypot(a, b); return [['Longest side', '√(a² + b²)', h, 'units'], ['Perimeter', 'a + b + longest side', a + b + h, 'units'], ['Area', '½ × a × b', a * b / 2, 'square units']]; }
    if (shape === 'circle') return [['Diameter', '2 × a', 2 * a, 'units'], ['Circumference', '2 × π × a', 2 * Math.PI * a, 'units'], ['Area', 'π × a²', Math.PI * a * a, 'square units']];
    return [['Volume', 'a × b × c', a * b * c, 'cubic units'], ['Surface area', '2 × (ab + bc + ac)', 2 * (a * b + b * c + a * c), 'square units'], ['Total edge length', '4 × (a + b + c)', 4 * (a + b + c), 'units']];
  },''',
    '''  const p = Kit.plot(canvas, {x: [-4, 20.8], y: [-1.8, 15.8], grid: false}), blue = '#215783', rows = Model.measure(v.shape, v.a, v.b, v.c);
  if (v.shape === 'rectangle') { p.line(0, 0, v.a, 0, blue, 3); p.line(v.a, 0, v.a, v.b, blue, 3); p.line(v.a, v.b, 0, v.b, blue, 3); p.line(0, v.b, 0, 0, blue, 3); p.text('a = ' + v.a, v.a / 2, 0, '#172533', -16, 20); p.text('b = ' + v.b, v.a, v.b / 2); }
  if (v.shape === 'triangle') { p.line(0, 0, v.a, 0, blue, 3); p.line(0, 0, 0, v.b, blue, 3); p.line(v.a, 0, 0, v.b, '#963d18', 3); p.text('a = ' + v.a, v.a / 2, 0, '#172533', -16, 20); p.text('b = ' + v.b, 0, v.b / 2, '#172533', -52, 0); }
  if (v.shape === 'circle') { const k = 0.55, cx = 8, cy = 6.5; for (let i = 0; i < 120; i++) p.line(cx + k * v.a * Math.cos(i * Math.PI / 60), cy + k * v.a * Math.sin(i * Math.PI / 60), cx + k * v.a * Math.cos((i + 1) * Math.PI / 60), cy + k * v.a * Math.sin((i + 1) * Math.PI / 60), blue, 3); p.line(cx, cy, cx + k * v.a, cy, '#963d18', 3); p.text('radius a = ' + v.a, cx, cy, '#172533', 4, -8); }
  if (v.shape === 'cuboid') { const dx = v.b * 0.45, dy = v.b * 0.3, box = [[0, 0], [v.a, 0], [v.a, v.c], [0, v.c]]; box.forEach(([x, y], i) => { const [nx, ny] = box[(i + 1) % 4]; p.line(x, y, nx, ny, blue, 3); p.line(x + dx, y + dy, nx + dx, ny + dy, blue, i < 1 || i > 2 ? 1 : 3, i < 1 || i > 2 ? [5, 5] : []); p.line(x, y, x + dx, y + dy, blue, i === 0 ? 1 : 3, i === 0 ? [5, 5] : []); }); p.text('a = ' + v.a, v.a / 2, 0, '#172533', -16, 20); p.text('c = ' + v.c, 0, v.c / 2, '#172533', -52, 0); p.text('b = ' + v.b, v.a + dx / 2, dy / 2, '#172533', 8, 6); }
  return {sum: rows.map(r => r[0] + ' ' + Kit.fmt(r[2])).join(' · '),
    rows: rows.map(r => [r[0], r[1], Kit.fmt(r[2]) + ' ' + r[3]]),
    result: v.shape === 'cuboid' ? 'Volume counts unit cubes: ' + v.a + ' × ' + v.b + ' in each layer, and ' + v.c + ' layers.' : 'Length is measured in units, area in square units. Doubling every length doubles the perimeter but makes the area four times as large.'};''', height=520,
    aria='The chosen shape drawn with its lengths labelled.', caption='Measures')

add('percent-grid', 'math.2.percent', 'Percentages', 'Percent, fraction and decimal',
    'Percent means “out of a hundred”. The grid has 100 squares.',
    [('p', slider('p', 'Percent', 0, 100, 35)), ('whole', slider('whole', 'Of this amount', 10, 500, 80, 10))], ['Form', 'Value'],
    '''  gcd: (a, b) => b ? Model.gcd(b, a % b) : a,
  fraction(p) { const g = Model.gcd(p, 100) || 1; return [p / g, 100 / g]; },
  decimal: p => p / 100,
  of: (p, whole) => Math.round(p * whole) / 100,
  increase: (p, whole) => Math.round((100 + p) * whole) / 100,
  decrease: (p, whole) => Math.round((100 - p) * whole) / 100,''',
    '''  const g = Kit.plot(canvas, {x: [-0.5, 10.5], y: [-0.5, 10.5], grid: false}), [n, d] = Model.fraction(v.p);
  for (let i = 0; i < 100; i++) { const x = i % 10, y = 9 - Math.floor(i / 10); if (i < v.p) for (let k = 1; k < 10; k++) g.line(x + 0.06, y + k / 10, x + 0.94, y + k / 10, '#8fb6d6', 4); }
  for (let i = 0; i <= 10; i++) { g.line(i, 0, i, 10, '#172533', 1); g.line(0, i, 10, i, '#172533', 1); }
  return {sum: v.p + '% of ' + v.whole + ' = ' + Kit.fmt(Model.of(v.p, v.whole), 6),
    rows: [['Percent', v.p + '%'], ['Fraction in lowest terms', d === 1 ? String(n) : n + '/' + d], ['Decimal', String(Model.decimal(v.p))], [v.p + '% of ' + v.whole, Kit.fmt(Model.of(v.p, v.whole), 6)],
      [v.whole + ' increased by ' + v.p + '%', Kit.fmt(Model.increase(v.p, v.whole), 6)], [v.whole + ' decreased by ' + v.p + '%', Kit.fmt(Model.decrease(v.p, v.whole), 6)]],
    result: 'To find ' + v.p + '% of an amount, multiply it by ' + Model.decimal(v.p) + '. An increase of ' + v.p + '% followed by a decrease of ' + v.p + '% does not return to the start, because the second percent is taken of a different amount.'};''', height=520,
    aria='A ten by ten grid with one square shaded for each percent.')

add('ratio-sharing', 'math.2.ratio', 'Ratio and Proportion', 'Sharing in a ratio and scaling up',
    'A ratio compares parts. Share an amount in the ratio, or scale a recipe and keep the ratio the same.',
    [('a', slider('a', 'First part', 1, 10, 2)), ('b', slider('b', 'Second part', 1, 10, 3)), ('total', slider('total', 'Amount to share', 10, 200, 60, 5))], ['Scale', 'First', 'Second', 'Together'],
    '''  gcd: (a, b) => b ? Model.gcd(b, a % b) : a,
  simplify(a, b) { const g = Model.gcd(a, b); return [a / g, b / g]; },
  share(total, a, b) { const part = total / (a + b); return {part, first: part * a, second: part * b}; },
  scale: (a, b, k) => [a * k, b * k],
  // The second quantity that keeps the ratio when the first is x.
  proportion: (a, b, x) => x * b / a,''',
    '''  const s = Model.share(v.total, v.a, v.b), [sa, sb] = Model.simplify(v.a, v.b), p = Kit.plot(canvas, {x: [-0.2, v.a + v.b + 0.2], y: [0, 3], grid: false});
  for (let i = 0; i < v.a + v.b; i++) { for (let k = 0; k <= 24; k++) p.line(i + 0.04, 1 + k / 20, i + 0.96, 1 + k / 20, i < v.a ? '#8fb6d6' : '#e3b89c', 5); p.line(i, 1, i, 2.2, '#172533', 1.5); }
  p.line(v.a + v.b, 1, v.a + v.b, 2.2, '#172533', 1.5); p.line(0, 1, v.a + v.b, 1, '#172533', 1.5); p.line(0, 2.2, v.a + v.b, 2.2, '#172533', 1.5);
  p.text(Kit.fmt(s.first), v.a / 2, 2.2, '#215783', -10, -10); p.text(Kit.fmt(s.second), v.a + v.b / 2, 2.2, '#963d18', -10, -10);
  return {sum: v.total + ' shared ' + v.a + ' : ' + v.b + ' gives ' + Kit.fmt(s.first) + ' and ' + Kit.fmt(s.second),
    rows: [1, 2, 3, 5, 10].map(k => ['× ' + k, String(v.a * k), String(v.b * k), String((v.a + v.b) * k)]),
    result: 'The ratio ' + v.a + ' : ' + v.b + (sa !== v.a ? ' simplifies to ' + sa + ' : ' + sb : ' is already in its simplest form') + '. There are ' + (v.a + v.b) + ' equal parts, so one part of ' + v.total + ' is ' + Kit.fmt(s.part) + '.'};''', height=220,
    aria='A bar divided into equal parts, coloured to show the two shares.', caption='The same ratio at different scales')


def build():
    registry_path = WEB / 'activities/registry.json'
    registry = json.loads(registry_path.read_text())
    for act in ACTS:
        folder = WEB / 'math' / act['slug']
        folder.mkdir(parents=True, exist_ok=True)
        page = HTML
        for key, value in {'TITLE': act['title'], 'NODE': act['node'], 'BACK': act['back'], 'LEDE': act['lede'], 'HEIGHT': str(act['height']), 'ARIA': act['aria'],
                           'CAPTION': act['caption'], 'CONTROLS': '\n'.join(html for _, html in act['controls']),
                           'HEADS': ''.join('<th scope="col">%s</th>' % head for head in act['heads'])}.items():
            page = page.replace('@%s@' % key, value)
        (folder / 'index.html').write_text(page)
        script = JS.replace('@MODEL@', act['model']).replace('@RENDER@', act['render']).replace('@IDS@', json.dumps([name for name, _ in act['controls']]))
        (folder / 'lab.js').write_text(script)
        entry = {'href': '/app/math/%s/index.html' % act['slug'], 'label': act['title']}
        links = registry.setdefault(act['node'], [])
        if entry not in links:
            links.append(entry)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + '\n')
    return len(ACTS)


if __name__ == '__main__':
    print(build(), 'activities')

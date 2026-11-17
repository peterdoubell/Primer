"""Generate the secondary and university mathematics activities.

They use the page shell of tools/build_math_number_activities.py: controls, a drawing, a table and a result line.
The model of each is a small pure object, tested in tests/activity-models.test.cjs.

Run: python tools/build_math_higher_activities.py. It rewrites web/math/<slug>/ and adds registry entries.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_math_number_activities as base  # noqa: E402

base.ACTS.clear()
add, slider, select = base.add, base.slider, base.select
SQUARE = 700  # canvas height that gives equal scales on both axes for a square range

add('compose-functions', 'math.3.functions', 'Functions', 'Evaluating and composing functions',
    'A function turns each input into one output. Composing feeds the output of one function into another, and the order matters.',
    [('f', select('f', 'Function f', [('double', 'f(x) = 2x + 1'), ('square', 'f(x) = x²'), ('shift', 'f(x) = x − 3'), ('half', 'f(x) = x / 2'), ('abs', 'f(x) = |x|')])),
     ('g', select('g', 'Function g', [('square', 'g(x) = x²'), ('double', 'g(x) = 2x + 1'), ('shift', 'g(x) = x − 3'), ('half', 'g(x) = x / 2'), ('abs', 'g(x) = |x|')])),
     ('x', slider('x', 'Input x', -5, 5, 2, 0.5))], ['Expression', 'Value'],
    '''  FUNCTIONS: {double: x => 2 * x + 1, square: x => x * x, shift: x => x - 3, half: x => x / 2, abs: x => Math.abs(x)},
  apply: (name, x) => Model.FUNCTIONS[name](x),
  // (outer ∘ inner)(x) = outer(inner(x))
  compose: (outer, inner, x) => Model.apply(outer, Model.apply(inner, x)),
  // Do the two orders agree at every half step from -5 to 5?
  commute(f, g) { for (let x = -5; x <= 5; x += 0.5) if (Math.abs(Model.compose(f, g, x) - Model.compose(g, f, x)) > 1e-9) return false; return true; },''',
    '''  const p = Kit.plot(canvas, {x: [-6, 6], y: [-10, 30]}), fg = Model.compose(v.f, v.g, v.x), gf = Model.compose(v.g, v.f, v.x);
  p.curve(x => Model.apply(v.f, x), '#215783'); p.curve(x => Model.apply(v.g, x), '#3c7a4b'); p.curve(x => Model.compose(v.f, v.g, x), '#963d18');
  p.point(v.x, Model.apply(v.f, v.x), '#215783'); p.point(v.x, Model.apply(v.g, v.x), '#3c7a4b'); p.point(v.x, fg, '#963d18'); p.text('f(g(x))', v.x, fg);
  return {sum: 'f(g(' + v.x + ')) = ' + Kit.fmt(fg) + '   g(f(' + v.x + ')) = ' + Kit.fmt(gf),
    rows: [['f(x)', Kit.fmt(Model.apply(v.f, v.x))], ['g(x)', Kit.fmt(Model.apply(v.g, v.x))], ['f(g(x)): g first, then f', Kit.fmt(fg)], ['g(f(x)): f first, then g', Kit.fmt(gf)]],
    result: Model.commute(v.f, v.g) ? 'For this pair the two orders give the same result at every input tried. That is unusual.' : 'Composition is not commutative: f(g(x)) and g(f(x)) are different functions. Blue is f, green is g and red is f(g(x)).'};''', height=460,
    aria='Graphs of f, g and f composed with g, with the chosen input marked.')

add('solve-linear', 'math.3.linear', 'Linear Equations', 'Solving a linear equation',
    'Solve ax + b = cx + d. Each side is a line; the solution is where the lines cross.',
    [('a', slider('a', 'a', -6, 6, 2)), ('b', slider('b', 'b', -6, 6, -3)), ('c', slider('c', 'c', -6, 6, -1)), ('d', slider('d', 'd', -6, 6, 6))], ['Step', 'Equation'],
    '''  solve(a, b, c, d) {
    if (a === c) return {kind: b === d ? 'all' : 'none'};
    const x = (d - b) / (a - c); return {kind: 'one', x, y: a * x + b};
  },
  side: (m, k) => ((m === 0 ? '' : (m === 1 ? '' : m === -1 ? '−' : String(m).replace('-', '−')) + 'x') + (k === 0 ? (m === 0 ? '0' : '') : (m === 0 ? '' : k > 0 ? ' + ' : ' − ') + (m === 0 ? String(k).replace('-', '−') : Math.abs(k)))),''',
    '''  const r = Model.solve(v.a, v.b, v.c, v.d), p = Kit.plot(canvas, {x: [-10, 10], y: [-30, 30]});
  p.curve(x => v.a * x + v.b, '#215783'); p.curve(x => v.c * x + v.d, '#963d18'); if (r.kind === 'one') { p.point(r.x, r.y, '#172533', 7); p.text('x = ' + Kit.fmt(r.x), r.x, r.y); }
  const start = Model.side(v.a, v.b) + ' = ' + Model.side(v.c, v.d);
  if (r.kind !== 'one') return {sum: start, rows: [['Start', start], ['Subtract ' + Model.side(v.c, 0) + ' from both sides', Model.side(0, v.b) + ' = ' + Model.side(0, v.d)]],
    result: r.kind === 'all' ? 'Both sides are the same line, so every value of x is a solution.' : 'The lines are parallel and never meet, so there is no solution.'};
  return {sum: start + '  →  x = ' + Kit.fmt(r.x),
    rows: [['Start', start], ['Collect x on the left', Model.side(v.a - v.c, v.b) + ' = ' + Model.side(0, v.d)], ['Collect numbers on the right', Model.side(v.a - v.c, 0) + ' = ' + Model.side(0, v.d - v.b)], ['Divide by ' + String(v.a - v.c).replace('-', '−'), 'x = ' + Kit.fmt(r.x)], ['Check: both sides equal', Kit.fmt(r.y)]],
    result: 'Do the same thing to both sides at every step. The lines cross at x = ' + Kit.fmt(r.x) + ', where both sides equal ' + Kit.fmt(r.y) + '.'};''', height=460,
    aria='Two lines, one for each side of the equation, and their crossing point.', caption='Working')

add('polynomial-roots', 'math.3.polynomials', 'Polynomials', 'From roots to a polynomial',
    'Choose three roots and a leading coefficient. The factored form multiplies out to the expanded form, and the graph crosses the axis at each root.',
    [('a', slider('a', 'Leading coefficient', -3, 3, 1)), ('r1', slider('r1', 'Root 1', -4, 4, -2)), ('r2', slider('r2', 'Root 2', -4, 4, 1)), ('r3', slider('r3', 'Root 3', -4, 4, 3))], ['Property', 'Value'],
    '''  // Coefficients of a(x − r1)(x − r2)…, highest power first.
  expand(a, roots) { let c = [a]; for (const r of roots) { const n = [...c, 0]; for (let i = 0; i < c.length; i++) n[i + 1] -= r * c[i]; c = n; } return c; },
  value: (coefficients, x) => coefficients.reduce((sum, c) => sum * x + c, 0),
  text(coefficients) {
    const up = {0: '', 1: 'x', 2: 'x²', 3: 'x³'}, n = coefficients.length - 1; let out = '';
    coefficients.forEach((c, i) => { if (!c) return; const power = up[n - i], size = Math.abs(c), body = (size === 1 && power ? '' : size) + power; out += out ? (c < 0 ? ' − ' : ' + ') + body : (c < 0 ? '−' : '') + body; });
    return out || '0';
  },
  factored(a, roots) { return (a === 1 ? '' : a === -1 ? '−' : String(a).replace('-', '−')) + roots.map(r => r === 0 ? 'x' : '(x ' + (r < 0 ? '+ ' : '− ') + Math.abs(r) + ')').join(''); },''',
    '''  const roots = [v.r1, v.r2, v.r3], c = Model.expand(v.a, roots), p = Kit.plot(canvas, {x: [-5, 5], y: [-60, 60]});
  p.curve(x => Model.value(c, x), '#215783'); for (const r of roots) p.point(r, 0, '#963d18', 6); p.point(0, Model.value(c, 0), '#3c7a4b', 5);
  if (v.a === 0) return {sum: 'y = 0', rows: [['Leading coefficient', '0']], result: 'With a leading coefficient of 0 nothing is left: the polynomial is zero everywhere.'};
  const repeated = new Set(roots).size < 3;
  return {sum: 'y = ' + Model.text(c),
    rows: [['Factored form', Model.factored(v.a, roots)], ['Expanded form', Model.text(c)], ['Degree', '3'], ['Roots', [...new Set(roots)].sort((x, y) => x - y).join(', ').replace(/-/g, '−')], ['Crosses the y-axis at', String(c[3]).replace('-', '−')], ['Sum of the roots (−b ÷ a)', String(-c[1] / c[0]).replace('-', '−')]],
    result: 'As x grows large, y ' + (v.a > 0 ? 'rises' : 'falls') + ' on the right and ' + (v.a > 0 ? 'falls' : 'rises') + ' on the left, because the degree is odd.' + (repeated ? ' A repeated root makes the graph touch the axis there instead of passing straight through.' : '')};''', height=460,
    aria='Graph of the cubic with its roots marked on the x-axis.', caption='The polynomial')

add('quadratic-solver', 'math.3.quadratics', 'Quadratic Equations', 'Solving a quadratic three ways',
    'Set a, b and c in ax² + bx + c = 0. The discriminant tells how many real roots there are before you find them.',
    [('a', slider('a', 'a', -3, 3, 1, 0.5)), ('b', slider('b', 'b', -8, 8, -2)), ('c', slider('c', 'c', -8, 8, -3))], ['Quantity', 'Value'],
    '''  solve(a, b, c) {
    if (a === 0) return null;
    const D = b * b - 4 * a * c, h = -b / (2 * a), k = c - b * b / (4 * a);
    if (D > 0) { const s = Math.sqrt(D), roots = [(-b - s) / (2 * a), (-b + s) / (2 * a)].sort((x, y) => x - y); return {D, h, k, kind: 'two', roots}; }
    if (D === 0) return {D, h, k, kind: 'one', roots: [h]};
    return {D, h, k, kind: 'complex', re: h, im: Math.sqrt(-D) / Math.abs(2 * a)};
  },''',
    '''  const r = Model.solve(v.a, v.b, v.c), p = Kit.plot(canvas, {x: [-10, 10], y: [-30, 30]}), m = t => Kit.fmt(t).replace('-', '−');
  p.curve(x => v.a * x * x + v.b * x + v.c, '#215783');
  if (!r) return {sum: 'Not a quadratic', rows: [['a', '0']], result: 'With a = 0 the x² term vanishes and the equation is linear.'};
  p.point(r.h, r.k, '#3c7a4b', 6); p.text('vertex', r.h, r.k); if (r.roots) for (const x of r.roots) p.point(x, 0, '#963d18', 6); p.line(r.h, -30, r.h, 30, '#9aa6ae', 1, [5, 5]);
  const roots = r.kind === 'complex' ? m(r.re) + ' ± ' + Kit.fmt(r.im) + 'i' : r.roots.map(m).join(' and ');
  return {sum: 'x = ' + roots,
    rows: [['Discriminant b² − 4ac', m(r.D)], ['Number of real roots', r.kind === 'two' ? '2' : r.kind === 'one' ? '1 (repeated)' : '0'], ['Roots from the formula', roots], ['Vertex', '(' + m(r.h) + ', ' + m(r.k) + ')'],
      ['Completed square', m(v.a) + '(x ' + (r.h < 0 ? '+ ' : '− ') + Kit.fmt(Math.abs(r.h)) + ')² ' + (r.k < 0 ? '− ' : '+ ') + Kit.fmt(Math.abs(r.k))], ['Axis of symmetry', 'x = ' + m(r.h)]],
    result: r.kind === 'two' ? 'The discriminant is positive, so the parabola crosses the x-axis twice. The roots sit the same distance either side of the axis of symmetry.' : r.kind === 'one' ? 'The discriminant is zero, so the parabola just touches the x-axis at its vertex.' : 'The discriminant is negative, so the parabola never reaches the x-axis. The roots are complex numbers.'};''', height=460,
    aria='Graph of the parabola with its vertex, axis of symmetry and any real roots.')

add('slope-between-points', 'math.3.slope', 'Slope and Lines', 'The line through two points',
    'Slope is rise over run. Two points fix a line, its slope and its equation.',
    [('x1', slider('x1', 'First point x', -6, 6, -2)), ('y1', slider('y1', 'First point y', -6, 6, -1)), ('x2', slider('x2', 'Second point x', -6, 6, 4)), ('y2', slider('y2', 'Second point y', -6, 6, 3))], ['Quantity', 'Value'],
    '''  line(x1, y1, x2, y2) {
    if (x1 === x2 && y1 === y2) return {kind: 'point'};
    if (x1 === x2) return {kind: 'vertical', x: x1};
    const m = (y2 - y1) / (x2 - x1); return {kind: 'line', m, b: y1 - m * x1, rise: y2 - y1, run: x2 - x1, perpendicular: m === 0 ? null : -1 / m};
  },
  equation(m, b) { const t = n => Kit.fmt(Math.abs(n)); return 'y = ' + (m === 0 ? Kit.fmt(b).replace('-', '−') : (m < 0 ? '−' : '') + (Math.abs(m) === 1 ? '' : t(m)) + 'x' + (b === 0 ? '' : (b < 0 ? ' − ' : ' + ') + t(b))); },''',
    '''  const r = Model.line(v.x1, v.y1, v.x2, v.y2), p = Kit.plot(canvas, {x: [-8, 8], y: [-8, 8]}), m = t => Kit.fmt(t).replace('-', '−');
  if (r.kind === 'line') { p.curve(x => r.m * x + r.b, '#215783'); p.line(v.x1, v.y1, v.x2, v.y1, '#963d18', 2, [6, 5]); p.line(v.x2, v.y1, v.x2, v.y2, '#3c7a4b', 2, [6, 5]); }
  if (r.kind === 'vertical') p.line(r.x, -8, r.x, 8, '#215783', 3);
  p.point(v.x1, v.y1, '#172533', 6); p.point(v.x2, v.y2, '#172533', 6);
  if (r.kind === 'point') return {sum: 'One point only', rows: [['Points', 'the same point twice']], result: 'One point does not fix a line. Move one of the points.'};
  if (r.kind === 'vertical') return {sum: 'x = ' + m(r.x), rows: [['Run', '0'], ['Slope', 'undefined'], ['Equation', 'x = ' + m(r.x)]], result: 'The run is zero, so rise over run would divide by zero. A vertical line has no slope and its equation is x = ' + m(r.x) + '.'};
  return {sum: Model.equation(r.m, r.b),
    rows: [['Rise (change in y)', m(r.rise)], ['Run (change in x)', m(r.run)], ['Slope', m(r.m)], ['y-intercept', m(r.b)], ['Equation', Model.equation(r.m, r.b)], ['Slope of a parallel line', m(r.m)], ['Slope of a perpendicular line', r.perpendicular === null ? 'undefined (vertical)' : m(r.perpendicular)]],
    result: r.m === 0 ? 'The rise is zero, so the line is horizontal with slope 0.' : 'For every 1 across, the line goes ' + (r.m > 0 ? 'up ' : 'down ') + Kit.fmt(Math.abs(r.m)) + '. Perpendicular slopes multiply to −1.'};''', height=SQUARE,
    aria='A grid with the two points, the line through them, and the rise and run.')

add('vector-sum-dot', 'math.3.vectors', 'Vectors', 'Adding vectors and the dot product',
    'A vector has a size and a direction. Add them tip to tail. The dot product measures how far two vectors point the same way.',
    [('ux', slider('ux', 'u across', -5, 5, 3)), ('uy', slider('uy', 'u up', -5, 5, 1)), ('vx', slider('vx', 'v across', -5, 5, 1)), ('vy', slider('vy', 'v up', -5, 5, 4))], ['Quantity', 'Value'],
    '''  add: (u, w) => [u[0] + w[0], u[1] + w[1]],
  dot: (u, w) => u[0] * w[0] + u[1] * w[1],
  length: u => Math.hypot(u[0], u[1]),
  // Angle between the vectors in degrees; null if either is the zero vector.
  angle(u, w) { const d = Model.length(u) * Model.length(w); return d ? Math.acos(Math.max(-1, Math.min(1, Model.dot(u, w) / d))) * 180 / Math.PI : null; },
  // Signed length of the shadow of u on w.
  projection(u, w) { const l = Model.length(w); return l ? Model.dot(u, w) / l : null; },''',
    '''  const u = [v.ux, v.uy], w = [v.vx, v.vy], s = Model.add(u, w), angle = Model.angle(u, w), p = Kit.plot(canvas, {x: [-11, 11], y: [-11, 11]}), m = t => Kit.fmt(t).replace('-', '−');
  p.arrow(0, 0, u[0], u[1], '#215783'); p.arrow(0, 0, w[0], w[1], '#3c7a4b'); p.line(u[0], u[1], s[0], s[1], '#3c7a4b', 2, [6, 5]); p.arrow(0, 0, s[0], s[1], '#963d18');
  p.text('u', u[0], u[1]); p.text('v', w[0], w[1]); p.text('u + v', s[0], s[1]);
  const dot = Model.dot(u, w);
  return {sum: 'u + v = (' + m(s[0]) + ', ' + m(s[1]) + ')   u · v = ' + m(dot),
    rows: [['u + v', '(' + m(s[0]) + ', ' + m(s[1]) + ')'], ['Length of u', Kit.fmt(Model.length(u))], ['Length of v', Kit.fmt(Model.length(w))], ['Length of u + v', Kit.fmt(Model.length(s))], ['Dot product u · v', m(dot)],
      ['Angle between u and v', angle === null ? 'undefined for a zero vector' : Kit.fmt(angle) + '°'], ['Shadow of u along v', Model.projection(u, w) === null ? 'undefined' : m(Model.projection(u, w))]],
    result: angle === null ? 'The zero vector has no direction, so the angle is not defined.' : dot === 0 ? 'The dot product is 0, so the vectors are perpendicular.' : 'The dot product is ' + (dot > 0 ? 'positive: the vectors point broadly the same way.' : 'negative: the vectors point broadly opposite ways.') + ' The length of u + v is never more than the two lengths added.'};''', height=SQUARE,
    aria='Arrows for u, v and their sum, added tip to tail.')

add('epsilon-n', 'math.4.analysis', 'Real Analysis', 'Convergence: for every ε there is an N',
    'A sequence converges to L if, however small a tolerance ε you name, the terms eventually stay within ε of L. Choose ε and find the N that works.',
    [('seq', select('seq', 'Sequence', [('inv', 'aₙ = 1/n'), ('ratio', 'aₙ = (n + 1)/n'), ('alt', 'aₙ = (−1)ⁿ/n'), ('geo', 'aₙ = (1/2)ⁿ')])), ('eps', slider('eps', 'Tolerance ε', 0.01, 0.5, 0.1, 0.01))], ['Quantity', 'Value'],
    '''  SEQUENCES: {inv: {a: n => 1 / n, limit: 0}, ratio: {a: n => (n + 1) / n, limit: 1}, alt: {a: n => (n % 2 ? -1 : 1) / n, limit: 0}, geo: {a: n => 0.5 ** n, limit: 0}},
  term: (name, n) => Model.SEQUENCES[name].a(n),
  gap: (name, n) => Math.abs(Model.term(name, n) - Model.SEQUENCES[name].limit),
  // Smallest N with |aₙ − L| < ε for all n ≥ N. The gap shrinks steadily for each of these sequences.
  threshold(name, eps) { let n = 1; while (Model.gap(name, n) >= eps - 1e-12) n++; return n; },''',
    '''  const s = Model.SEQUENCES[v.seq], N = Model.threshold(v.seq, v.eps), p = Kit.plot(canvas, {x: [0, 41], y: [s.limit - 1.1, s.limit + 1.1], xlabel: 'n', ylabel: 'aₙ'});
  p.line(0, s.limit + v.eps, 41, s.limit + v.eps, '#3c7a4b', 1.5, [6, 5]); p.line(0, s.limit - v.eps, 41, s.limit - v.eps, '#3c7a4b', 1.5, [6, 5]); p.line(0, s.limit, 41, s.limit, '#172533', 1);
  if (N <= 40) p.line(N, s.limit - 1.1, N, s.limit + 1.1, '#963d18', 1.5, [3, 4]);
  for (let n = 1; n <= 40; n++) p.point(n, Model.term(v.seq, n), n >= N ? '#215783' : '#9aa6ae', 4);
  return {sum: 'ε = ' + v.eps + '  →  N = ' + N,
    rows: [['Limit L', String(s.limit)], ['Tolerance ε', String(v.eps)], ['Smallest N that works', String(N)], ['|a_N − L|', Kit.fmt(Model.gap(v.seq, N))], ['|a_(N−1) − L| (just too far)', N > 1 ? Kit.fmt(Model.gap(v.seq, N - 1)) : 'no earlier term']],
    result: 'From n = ' + N + ' onward every term lies inside the green band of width ε around ' + s.limit + '. Shrink ε and N grows, but there is always an N: that is what convergence means.'};''', height=460,
    aria='Terms of the sequence, the band of width epsilon around the limit, and the threshold N.')

add('set-operations', 'math.4.discrete', 'Discrete Mathematics', 'Sets: union, intersection and counting',
    'Two sets drawn from the numbers 1 to 12. Count their union without counting anything twice.',
    [('a', select('a', 'Set A', [('even', 'even numbers'), ('odd', 'odd numbers'), ('three', 'multiples of 3'), ('prime', 'primes'), ('big', 'numbers above 6'), ('square', 'square numbers')])),
     ('b', select('b', 'Set B', [('three', 'multiples of 3'), ('even', 'even numbers'), ('odd', 'odd numbers'), ('prime', 'primes'), ('big', 'numbers above 6'), ('square', 'square numbers')]))], ['Set', 'Members', 'Size'],
    '''  UNIVERSE: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  SETS: {even: n => n % 2 === 0, odd: n => n % 2 === 1, three: n => n % 3 === 0, prime: n => [2, 3, 5, 7, 11].includes(n), big: n => n > 6, square: n => [1, 4, 9].includes(n)},
  members: name => Model.UNIVERSE.filter(Model.SETS[name]),
  union: (a, b) => Model.UNIVERSE.filter(n => Model.SETS[a](n) || Model.SETS[b](n)),
  intersection: (a, b) => Model.UNIVERSE.filter(n => Model.SETS[a](n) && Model.SETS[b](n)),
  difference: (a, b) => Model.UNIVERSE.filter(n => Model.SETS[a](n) && !Model.SETS[b](n)),
  complement: a => Model.UNIVERSE.filter(n => !Model.SETS[a](n)),
  // Number of subsets of a set with k members.
  subsets: k => 2 ** k,''',
    '''  const p = Kit.plot(canvas, {x: [0, 13], y: [0, 2], grid: false}), A = Model.members(v.a), B = Model.members(v.b), both = Model.intersection(v.a, v.b), either = Model.union(v.a, v.b), list = s => s.length ? '{' + s.join(', ') + '}' : '∅ (empty)';
  for (const n of Model.UNIVERSE) { const inA = A.includes(n), inB = B.includes(n); p.point(n, 1, inA && inB ? '#6b3fa0' : inA ? '#215783' : inB ? '#c9631f' : '#c3ccd2', 15, !inA && !inB); p.text(String(n), n, 1, '#172533', n > 9 ? -9 : -5, 44); }
  return {sum: '|A ∪ B| = ' + A.length + ' + ' + B.length + ' − ' + both.length + ' = ' + either.length,
    rows: [['A', list(A), String(A.length)], ['B', list(B), String(B.length)], ['A ∩ B (in both)', list(both), String(both.length)], ['A ∪ B (in either)', list(either), String(either.length)], ['A \\\\ B (in A, not B)', list(Model.difference(v.a, v.b)), String(Model.difference(v.a, v.b).length)],
      ['Complement of A', list(Model.complement(v.a)), String(Model.complement(v.a).length)], ['Subsets of A', '2 to the power ' + A.length, String(Model.subsets(A.length))]],
    result: both.length ? 'Adding the sizes counts the ' + both.length + ' shared ' + (both.length === 1 ? 'member' : 'members') + ' twice, so subtract the intersection once. Purple is in both, blue only in A, orange only in B.' : 'The sets are disjoint, so the size of the union is just the two sizes added.'};''', height=200,
    aria='The numbers 1 to 12, coloured by which set they belong to.', caption='Sets')

add('matrix-transform', 'math.4.linalg', 'Linear Algebra', 'A matrix as a transformation of the plane',
    'A 2 × 2 matrix moves every point of the plane. Its columns say where the two unit vectors land, and its determinant says how area scales.',
    [('a', slider('a', 'Top left a', -3, 3, 2, 0.5)), ('b', slider('b', 'Top right b', -3, 3, 1, 0.5)), ('c', slider('c', 'Bottom left c', -3, 3, 1, 0.5)), ('d', slider('d', 'Bottom right d', -3, 3, 2, 0.5))], ['Quantity', 'Value'],
    '''  det: (a, b, c, d) => a * d - b * c,
  trace: (a, b, c, d) => a + d,
  apply: (a, b, c, d, x, y) => [a * x + b * y, c * x + d * y],
  eigen(a, b, c, d) {
    const t = a + d, disc = t * t - 4 * (a * d - b * c);
    return disc >= 0 ? {real: true, values: [(t + Math.sqrt(disc)) / 2, (t - Math.sqrt(disc)) / 2]} : {real: false, re: t / 2, im: Math.sqrt(-disc) / 2};
  },
  inverse(a, b, c, d) { const D = a * d - b * c; return D ? [d / D, -b / D, -c / D, a / D].map(x => x + 0) : null; },''',
    '''  const p = Kit.plot(canvas, {x: [-7, 7], y: [-7, 7]}), D = Model.det(v.a, v.b, v.c, v.d), e = Model.eigen(v.a, v.b, v.c, v.d), inv = Model.inverse(v.a, v.b, v.c, v.d), m = t => Kit.fmt(t).replace('-', '−');
  const square = [[0, 0], [1, 0], [1, 1], [0, 1]], image = square.map(([x, y]) => Model.apply(v.a, v.b, v.c, v.d, x, y));
  square.forEach((q, i) => { const n = square[(i + 1) % 4]; p.line(q[0], q[1], n[0], n[1], '#9aa6ae', 2); });
  image.forEach((q, i) => { const n = image[(i + 1) % 4]; p.line(q[0], q[1], n[0], n[1], '#215783', 3); });
  p.arrow(0, 0, v.a, v.c, '#963d18'); p.arrow(0, 0, v.b, v.d, '#3c7a4b'); p.text('column 1', v.a, v.c); p.text('column 2', v.b, v.d);
  return {sum: 'determinant = ' + m(D),
    rows: [['Where (1, 0) goes', '(' + m(v.a) + ', ' + m(v.c) + ')'], ['Where (0, 1) goes', '(' + m(v.b) + ', ' + m(v.d) + ')'], ['Determinant ad − bc', m(D)], ['Trace a + d', m(Model.trace(v.a, v.b, v.c, v.d))],
      ['Eigenvalues', e.real ? e.values.map(m).join(' and ') : m(e.re) + ' ± ' + Kit.fmt(e.im) + 'i'], ['Inverse', inv ? '[' + inv.slice(0, 2).map(m).join(', ') + ' ; ' + inv.slice(2).map(m).join(', ') + ']' : 'none']],
    result: D === 0 ? 'The determinant is 0: the unit square is flattened onto a line or a point, so the matrix cannot be undone.' : 'The unit square (grey) becomes a parallelogram of area ' + Kit.fmt(Math.abs(D)) + (D < 0 ? ', flipped over because the determinant is negative.' : '.') + (e.real ? ' The eigenvalues multiply to the determinant and add to the trace.' : ' Complex eigenvalues mean no direction is kept: the matrix turns everything.')};''', height=SQUARE,
    aria='The unit square and its image under the matrix, with the two column vectors.')

add('gradient-field', 'math.4.multivar', 'Multivariable Calculus', 'Partial derivatives and the gradient',
    'A function of two variables has a slope in every direction. The gradient points in the direction of steepest ascent.',
    [('surface', select('surface', 'Function', [('bowl', 'f(x, y) = x² + y²'), ('saddle', 'f(x, y) = x² − y²'), ('product', 'f(x, y) = xy')])), ('x', slider('x', 'x', -2, 2, 1, 0.25)), ('y', slider('y', 'y', -2, 2, 0.5, 0.25)), ('angle', slider('angle', 'Direction (degrees)', 0, 345, 45, 15))], ['Quantity', 'Value'],
    '''  SURFACES: {bowl: {f: (x, y) => x * x + y * y, fx: (x, y) => 2 * x, fy: (x, y) => 2 * y}, saddle: {f: (x, y) => x * x - y * y, fx: (x, y) => 2 * x, fy: (x, y) => -2 * y}, product: {f: (x, y) => x * y, fx: (x, y) => y, fy: (x, y) => x}},
  value: (name, x, y) => Model.SURFACES[name].f(x, y),
  gradient: (name, x, y) => [Model.SURFACES[name].fx(x, y), Model.SURFACES[name].fy(x, y)],
  // Rate of change of f in the direction at the given angle from the x-axis.
  directional(name, x, y, degrees) { const [gx, gy] = Model.gradient(name, x, y), t = degrees * Math.PI / 180; return gx * Math.cos(t) + gy * Math.sin(t); },
  steepest: (name, x, y) => Math.hypot(...Model.gradient(name, x, y)),''',
    '''  const p = Kit.plot(canvas, {x: [-2.6, 2.6], y: [-2.6, 2.6], xlabel: 'x', ylabel: 'y'}), [gx, gy] = Model.gradient(v.surface, v.x, v.y), t = v.angle * Math.PI / 180, m = n => Kit.fmt(n).replace('-', '−');
  const cell = 0.2, w = Math.abs(p.X(cell) - p.X(0)) + 1, h = Math.abs(p.Y(cell) - p.Y(0)) + 1;
  for (let x = -2.5; x < 2.5 - 1e-9; x += cell) for (let y = -2.5; y < 2.5 - 1e-9; y += cell) { const z = Math.max(-1, Math.min(1, Model.value(v.surface, x + cell / 2, y + cell / 2) / 8)); p.ctx.fillStyle = z >= 0 ? 'rgba(150,61,24,' + (0.08 + 0.6 * z) + ')' : 'rgba(33,87,131,' + (0.08 - 0.6 * z) + ')'; p.ctx.fillRect(p.X(x), p.Y(y + cell), w, h); }
  const scale = 0.35; p.arrow(v.x, v.y, v.x + gx * scale, v.y + gy * scale, '#172533'); p.arrow(v.x, v.y, v.x + Math.cos(t) * 0.9, v.y + Math.sin(t) * 0.9, '#3c7a4b', 2); p.point(v.x, v.y, '#172533', 5);
  return {sum: '∇f = (' + m(gx) + ', ' + m(gy) + ')',
    rows: [['f(x, y)', m(Model.value(v.surface, v.x, v.y))], ['∂f/∂x (slope going east)', m(gx)], ['∂f/∂y (slope going north)', m(gy)], ['Gradient', '(' + m(gx) + ', ' + m(gy) + ')'], ['Steepest slope', Kit.fmt(Model.steepest(v.surface, v.x, v.y))], ['Slope in the chosen direction', m(Model.directional(v.surface, v.x, v.y, v.angle))]],
    result: gx === 0 && gy === 0 ? 'The gradient is zero here: a critical point. For the bowl it is a minimum; for the other two it is a saddle.' : 'The black arrow is the gradient: the uphill direction. The slope in any other direction (green) is the gradient dotted with that direction, so it is never steeper. Red shading is high, blue is low.'};''', height=SQUARE,
    aria='A shaded map of the function with the gradient arrow and the chosen direction at the point.')

add('modular-clock', 'math.4.numtheory', 'Number Theory', 'Euclid’s algorithm and arithmetic on a clock',
    'Euclid’s algorithm finds the greatest common divisor by repeated remainders. On a clock with n hours, multiplying by a reaches every hour exactly when gcd(a, n) = 1.',
    [('a', slider('a', 'a', 1, 60, 14)), ('n', slider('n', 'Modulus n', 2, 60, 45))], ['Step', 'Working'],
    '''  // Each step writes a = q × b + r; the last non-zero remainder is the gcd.
  euclid(a, b) { const steps = []; while (b) { const q = Math.floor(a / b), r = a % b; steps.push({a, b, q, r}); a = b; b = r; } return {steps, gcd: a}; },
  gcd: (a, b) => Model.euclid(a, b).gcd,
  // The x with a × x ≡ 1 (mod n), or null when a and n share a factor.
  inverse(a, n) { for (let x = 1; x < n; x++) if (a * x % n === 1) return x; return null; },
  power(a, k, n) { let result = 1 % n, base = a % n; while (k > 0) { if (k % 2) result = result * base % n; base = base * base % n; k = Math.floor(k / 2); } return result; },
  // The residues reached by 0, a, 2a, … modulo n.
  multiples(a, n) { const seen = []; let x = 0; do { seen.push(x); x = (x + a) % n; } while (x !== 0); return seen; },
  isPrime(n) { if (n < 2) return false; for (let d = 2; d * d <= n; d++) if (n % d === 0) return false; return true; },''',
    '''  const e = Model.euclid(v.a, v.n), reach = Model.multiples(v.a, v.n), inv = Model.inverse(v.a, v.n), p = Kit.plot(canvas, {x: [-1.25, 1.25], y: [-1.25, 1.25], grid: false});
  const at = k => [Math.sin(2 * Math.PI * k / v.n), Math.cos(2 * Math.PI * k / v.n)];
  reach.forEach((k, i) => { const [x, y] = at(k), [nx, ny] = at(reach[(i + 1) % reach.length]); p.line(x, y, nx, ny, '#8fb6d6', 1.5); });
  for (let k = 0; k < v.n; k++) { const [x, y] = at(k); p.point(x, y, reach.includes(k) ? '#215783' : '#c3ccd2', v.n > 30 ? 4 : 6, !reach.includes(k)); }
  p.text('0', 0, 1, '#172533', -4, -12);
  const rows = e.steps.map((s, i) => ['Step ' + (i + 1), s.a + ' = ' + s.q + ' × ' + s.b + ' + ' + s.r]);
  rows.push(['Greatest common divisor', String(e.gcd)], ['Hours reached by multiples of ' + v.a, reach.length + ' of ' + v.n], ['Inverse of ' + v.a + ' modulo ' + v.n, inv === null ? 'none' : String(inv)]);
  if (Model.isPrime(v.n) && v.a % v.n) rows.push([v.a + ' to the power ' + (v.n - 1) + ', modulo ' + v.n, String(Model.power(v.a, v.n - 1, v.n))]);
  return {sum: 'gcd(' + v.a + ', ' + v.n + ') = ' + e.gcd, rows,
    result: e.gcd === 1 ? 'The gcd is 1, so stepping by ' + v.a + ' visits every hour and ' + v.a + ' has an inverse: ' + v.a + ' × ' + inv + ' leaves remainder 1.' + (Model.isPrime(v.n) ? ' Because ' + v.n + ' is prime, Fermat’s little theorem gives remainder 1 for the power shown.' : '') : 'The gcd is ' + e.gcd + ', so stepping by ' + v.a + ' only visits ' + reach.length + ' hours (' + v.n + ' ÷ ' + e.gcd + ') and ' + v.a + ' has no inverse modulo ' + v.n + '.'};''', height=SQUARE,
    aria='A clock face with n hours; the hours reached by stepping a at a time are filled in and joined.', caption='Euclid’s algorithm')

add('binomial-distribution', 'math.4.prob-theory', 'Probability Theory', 'The binomial distribution',
    'Repeat a trial n times, each succeeding with probability p. The bars give the chance of each number of successes.',
    [('n', slider('n', 'Trials n', 1, 30, 10)), ('p', slider('p', 'Chance of success p', 0, 1, 0.3, 0.05)), ('k', slider('k', 'Successes k', 0, 30, 3))], ['Quantity', 'Value'],
    '''  choose(n, k) { if (k < 0 || k > n) return 0; let c = 1; for (let i = 1; i <= Math.min(k, n - k); i++) c = c * (n - i + 1) / i; return Math.round(c); },
  pmf: (n, p, k) => Model.choose(n, k) * p ** k * (1 - p) ** (n - k),
  cdf(n, p, k) { let total = 0; for (let i = 0; i <= Math.min(k, n); i++) total += Model.pmf(n, p, i); return total; },
  mean: (n, p) => n * p,
  variance: (n, p) => n * p * (1 - p),''',
    '''  const k = Math.min(v.k, v.n), top = Math.max(...Array.from({length: v.n + 1}, (_, i) => Model.pmf(v.n, v.p, i))), p = Kit.plot(canvas, {x: [-1, 31], y: [0, top * 1.15], xlabel: 'successes', ylabel: 'probability'});
  for (let i = 0; i <= v.n; i++) p.line(i, 0, i, Model.pmf(v.n, v.p, i), i === k ? '#963d18' : i < k ? '#215783' : '#9aa6ae', 12);
  p.line(Model.mean(v.n, v.p), 0, Model.mean(v.n, v.p), top * 1.1, '#3c7a4b', 1.5, [5, 5]);
  return {sum: 'P(X = ' + k + ') = ' + Kit.fmt(Model.pmf(v.n, v.p, k)),
    rows: [['Ways to choose ' + k + ' of ' + v.n, String(Model.choose(v.n, k))], ['P(exactly ' + k + ')', Kit.fmt(Model.pmf(v.n, v.p, k))], ['P(at most ' + k + ')', Kit.fmt(Model.cdf(v.n, v.p, k))], ['P(more than ' + k + ')', Kit.fmt(Math.max(0, 1 - Model.cdf(v.n, v.p, k)))],
      ['Mean np', Kit.fmt(Model.mean(v.n, v.p))], ['Variance np(1 − p)', Kit.fmt(Model.variance(v.n, v.p))], ['Standard deviation', Kit.fmt(Math.sqrt(Model.variance(v.n, v.p)))]],
    result: 'The bars are tallest near the mean (green line) at np = ' + Kit.fmt(Model.mean(v.n, v.p)) + '. As n grows the shape approaches the bell curve, and the share of successes settles near p: the law of large numbers.'};''', height=460,
    aria='Bar chart of the probability of each number of successes.')

add('cyclic-subgroups', 'math.5.abstract', 'Abstract Algebra', 'Subgroups of the integers modulo n',
    'The integers modulo n form a group under addition. Each element generates a subgroup, and the size of every subgroup divides n.',
    [('n', slider('n', 'Modulus n', 2, 24, 12)), ('g', slider('g', 'Element g', 0, 23, 8))], ['Quantity', 'Value'],
    '''  gcd: (a, b) => b ? Model.gcd(b, a % b) : a,
  // Everything reachable by adding g to itself, in the order reached.
  generated(n, g) { const out = []; let x = 0; do { out.push(x); x = (x + g) % n; } while (x !== 0); return out; },
  order: (n, g) => n / Model.gcd(n, g % n),
  // Number of cosets of the subgroup generated by g.
  index: (n, g) => n / Model.order(n, g),
  generators: n => Array.from({length: n}, (_, i) => i).filter(i => Model.gcd(n, i) === 1),
  divisors: n => Array.from({length: n}, (_, i) => i + 1).filter(d => n % d === 0),''',
    '''  const g = v.g % v.n, H = Model.generated(v.n, g), p = Kit.plot(canvas, {x: [-1.3, 1.3], y: [-1.3, 1.3], grid: false}), at = k => [Math.sin(2 * Math.PI * k / v.n), Math.cos(2 * Math.PI * k / v.n)];
  H.forEach((k, i) => { const [x, y] = at(k), [nx, ny] = at(H[(i + 1) % H.length]); p.line(x, y, nx, ny, '#8fb6d6', 2); });
  for (let k = 0; k < v.n; k++) { const [x, y] = at(k); p.point(x, y, H.includes(k) ? '#215783' : '#c3ccd2', 8, !H.includes(k)); p.text(String(k), x * 1.13, y * 1.13, '#172533', -6, 5); }
  const order = Model.order(v.n, g);
  return {sum: '⟨' + g + '⟩ has ' + order + ' elements',
    rows: [['Element', g + (v.g !== g ? ' (' + v.g + ' reduced modulo ' + v.n + ')' : '')], ['Subgroup it generates', '{' + [...H].sort((x, y) => x - y).join(', ') + '}'], ['Order of the element', String(order)], ['Number of cosets (index)', String(Model.index(v.n, g))],
      ['Order × index', order + ' × ' + Model.index(v.n, g) + ' = ' + v.n], ['Generators of the whole group', Model.generators(v.n).join(', ')], ['Possible subgroup sizes', Model.divisors(v.n).join(', ')]],
    result: order === v.n ? g + ' generates the whole group, because gcd(' + g + ', ' + v.n + ') = 1.' : 'The subgroup has ' + order + ' elements and ' + order + ' divides ' + v.n + ', as Lagrange’s theorem requires. A cyclic group has exactly one subgroup for each divisor of n.'};''', height=SQUARE,
    aria='The elements of the group round a circle, with the generated subgroup filled in and joined.')

add('complex-mapping', 'math.5.complex-analysis', 'Complex Analysis', 'A complex function as a map of the plane',
    'A complex function sends each point z to a point w. Where the derivative is not zero, it stretches and turns every tiny shape the same way.',
    [('f', select('f', 'Function', [('square', 'w = z²'), ('inverse', 'w = 1/z'), ('exp', 'w = eᶻ')])), ('re', slider('re', 'Real part of z', -2, 2, 1, 0.25)), ('im', slider('im', 'Imaginary part of z', -2, 2, 0.5, 0.25))], ['Quantity', 'Value'],
    '''  apply(name, re, im) {
    if (name === 'square') return [re * re - im * im, 2 * re * im];
    if (name === 'exp') return [Math.exp(re) * Math.cos(im), Math.exp(re) * Math.sin(im)];
    const r2 = re * re + im * im; return r2 ? [re / r2, -im / r2] : null;
  },
  // f′(z): 2z, −1/z² and eᶻ.
  derivative(name, re, im) {
    if (name === 'square') return [2 * re, 2 * im];
    if (name === 'exp') return Model.apply('exp', re, im);
    const w = Model.apply('inverse', re, im); return w ? [-(w[0] * w[0] - w[1] * w[1]), -2 * w[0] * w[1]] : null;
  },
  modulus: z => Math.hypot(z[0], z[1]),
  argument: z => Math.atan2(z[1], z[0]) * 180 / Math.PI,
  text: z => (Kit.fmt(z[0]) + (z[1] < 0 ? ' − ' : ' + ') + Kit.fmt(Math.abs(z[1])) + 'i').replace(/^-/, '−'),''',
    '''  const z = [v.re, v.im], w = Model.apply(v.f, v.re, v.im), d = Model.derivative(v.f, v.re, v.im), p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5], xlabel: 'real', ylabel: 'imaginary'}), r = Model.modulus(z);
  for (let i = 0; i < 180; i++) { const t0 = i * Math.PI / 90, t1 = (i + 1) * Math.PI / 90, a = [r * Math.cos(t0), r * Math.sin(t0)], b = [r * Math.cos(t1), r * Math.sin(t1)]; p.line(a[0], a[1], b[0], b[1], '#8fb6d6', 1.5);
    const fa = Model.apply(v.f, a[0], a[1]), fb = Model.apply(v.f, b[0], b[1]); if (fa && fb && Model.modulus(fa) < 20 && Model.modulus(fb) < 20) p.line(fa[0], fa[1], fb[0], fb[1], '#e3b89c', 2); }
  p.point(z[0], z[1], '#215783', 6); p.text('z', z[0], z[1]); if (w) { p.point(w[0], w[1], '#963d18', 6); p.text('w', w[0], w[1]); }
  if (!w) return {sum: 'w is not defined', rows: [['z', '0']], result: '1/z has a pole at z = 0: the values grow without bound as z approaches 0.'};
  return {sum: 'w = ' + Model.text(w),
    rows: [['z', Model.text(z)], ['w = f(z)', Model.text(w)], ['Distance of w from 0', Kit.fmt(Model.modulus(w))], ['Angle of w', Kit.fmt(Model.argument(w)).replace('-', '−') + '°'], ['f′(z)', Model.text(d)], ['Local stretch |f′(z)|', Kit.fmt(Model.modulus(d))], ['Local turn', Model.modulus(d) ? Kit.fmt(Model.argument(d)).replace('-', '−') + '°' : 'undefined']],
    result: Model.modulus(d) === 0 ? 'The derivative is 0 here, so the map is not angle-preserving at this point: z² doubles angles at the origin.' : 'Near z the map multiplies small displacements by f′(z): it stretches them by ' + Kit.fmt(Model.modulus(d)) + ' and turns them through ' + Kit.fmt(Model.argument(d)).replace('-', '−') + '°. Angles between curves are kept. The pale blue circle through z maps to the orange curve.'};''', height=SQUARE,
    aria='The complex plane showing z, its image w, the circle through z and the image of that circle.')

add('curvature-circle', 'math.5.diffgeo', 'Differential Geometry', 'Curvature and the circle of best fit',
    'Curvature measures how fast a curve turns. At each point the osculating circle fits the curve best, and its radius is one over the curvature.',
    [('a', slider('a', 'Parabola y = ax²: a', -2, 2, 0.5, 0.25)), ('x', slider('x', 'Point x', -2, 2, 0, 0.25))], ['Quantity', 'Value'],
    '''  // Signed curvature of y = ax² at x: y″ / (1 + y′²)^(3/2).
  curvature: (a, x) => 2 * a / (1 + (2 * a * x) ** 2) ** 1.5,
  radius: (a, x) => { const k = Model.curvature(a, x); return k ? 1 / Math.abs(k) : Infinity; },
  // Centre of the osculating circle, or null on a straight line.
  centre(a, x) { if (!a) return null; const d = 2 * a * x, y = a * x * x, s = (1 + d * d) / (2 * a); return [x - d * s, y + s]; },
  tangent: (a, x) => 2 * a * x,''',
    '''  const y = v.a * v.x * v.x, k = Model.curvature(v.a, v.x), R = Model.radius(v.a, v.x), c = Model.centre(v.a, v.x), slope = Model.tangent(v.a, v.x), p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5]}), m = n => Kit.fmt(n).replace('-', '−');
  p.curve(t => v.a * t * t, '#215783'); p.curve(t => y + slope * (t - v.x), '#9aa6ae', -5, 5, 1.5);
  if (c && R < 60) { for (let i = 0; i < 180; i++) { const t0 = i * Math.PI / 90, t1 = (i + 1) * Math.PI / 90; p.line(c[0] + R * Math.cos(t0), c[1] + R * Math.sin(t0), c[0] + R * Math.cos(t1), c[1] + R * Math.sin(t1), '#963d18', 2); } p.line(v.x, y, c[0], c[1], '#963d18', 1, [5, 5]); p.point(c[0], c[1], '#963d18', 4); }
  p.point(v.x, y, '#172533', 6);
  return {sum: 'κ = ' + m(k) + (Number.isFinite(R) ? '   radius = ' + Kit.fmt(R) : ''),
    rows: [['Point', '(' + m(v.x) + ', ' + m(y) + ')'], ['Slope of the tangent', m(slope)], ['Curvature κ', m(k)], ['Radius of curvature 1/|κ|', Number.isFinite(R) ? Kit.fmt(R) : 'infinite'], ['Centre of the circle', c ? '(' + m(c[0]) + ', ' + m(c[1]) + ')' : 'none'], ['Curvature at the vertex', m(Model.curvature(v.a, 0))]],
    result: v.a === 0 ? 'A straight line has curvature 0 everywhere: it does not turn, and no circle fits it.' : 'The parabola turns fastest at its vertex, where κ = 2a = ' + m(2 * v.a) + ', and straightens further out. The red circle shares the curve’s position, tangent and curvature at the point.'};''', height=SQUARE,
    aria='The parabola with its tangent line and osculating circle at the chosen point.')

add('collatz-orbits', 'math.5.frontier', 'The Frontier', 'An open problem you can try: the Collatz conjecture',
    'Take a whole number. If it is even, halve it; if it is odd, triple it and add one. Repeat. Nobody has proved that every start reaches 1.',
    [('n', slider('n', 'Starting number', 1, 200, 27))], ['Quantity', 'Value'],
    '''  next: n => n % 2 ? 3 * n + 1 : n / 2,
  orbit(n) { const out = [n]; while (n !== 1) { n = Model.next(n); out.push(n); } return out; },
  steps: n => Model.orbit(n).length - 1,
  peak: n => Math.max(...Model.orbit(n)),
  // The start up to a limit that takes the most steps.
  longest(limit) { let best = 1; for (let n = 2; n <= limit; n++) if (Model.steps(n) > Model.steps(best)) best = n; return best; },''',
    '''  const orbit = Model.orbit(v.n), peak = Model.peak(v.n), p = Kit.plot(canvas, {x: [0, Math.max(orbit.length - 1, 1)], y: [0, peak * 1.1], xlabel: 'step', ylabel: 'value'});
  orbit.forEach((value, i) => { if (i) p.line(i - 1, orbit[i - 1], i, value, '#215783', 2); }); orbit.forEach((value, i) => p.point(i, value, value === peak ? '#963d18' : '#215783', value === peak ? 6 : 3));
  const longest = Model.longest(200);
  return {sum: v.n + ' reaches 1 in ' + (orbit.length - 1) + ' steps',
    rows: [['Steps to reach 1', String(orbit.length - 1)], ['Highest value reached', String(peak)], ['First terms', orbit.slice(0, 12).join(', ') + (orbit.length > 12 ? ', …' : '')], ['Odd steps (× 3 + 1)', String(orbit.filter(x => x % 2 && x !== 1).length)], ['Longest run for a start up to 200', longest + ' takes ' + Model.steps(longest) + ' steps']],
    result: 'Every starting number ever tried reaches 1, and computers have checked far beyond anything shown here. But checking is not proof: whether all whole numbers reach 1 is the Collatz conjecture, and it is still open.'};''', height=460,
    aria='Line graph of the values visited from the starting number until it reaches 1.')

add('fourier-square-wave', 'math.5.functional', 'Functional Analysis', 'Approximating a function by sine waves',
    'In a space of functions, sine waves act like perpendicular axes. Adding more of them brings the sum closer to a square wave when distance is measured by average squared error.',
    [('terms', slider('terms', 'Number of sine terms', 1, 25, 3))], ['Quantity', 'Value'],
    '''  // Square wave of height 1 and period 2π: (4/π) Σ sin((2j+1)x) / (2j+1).
  partial(terms, x) { let sum = 0; for (let j = 0; j < terms; j++) sum += Math.sin((2 * j + 1) * x) / (2 * j + 1); return 4 / Math.PI * sum; },
  square: x => Math.sin(x) >= 0 ? 1 : -1,
  // Share of the wave’s mean square captured by the first terms (Parseval).
  energy(terms) { let sum = 0; for (let j = 0; j < terms; j++) sum += 1 / (2 * j + 1) ** 2; return 8 / Math.PI ** 2 * sum; },
  // Root-mean-square distance between the wave and the partial sum.
  error: terms => Math.sqrt(Math.max(0, 1 - Model.energy(terms))),
  // Highest value of the partial sum, sampled finely across half a period.
  overshoot(terms) { let top = 0; for (let i = 1; i < 4000; i++) top = Math.max(top, Model.partial(terms, i * Math.PI / 4000)); return top; },''',
    '''  const p = Kit.plot(canvas, {x: [-3.5, 3.5], y: [-1.5, 1.5]});
  p.line(-Math.PI, -1, 0, -1, '#9aa6ae', 2); p.line(0, -1, 0, 1, '#9aa6ae', 2); p.line(0, 1, Math.PI, 1, '#9aa6ae', 2); p.curve(x => Model.partial(v.terms, x), '#215783');
  return {sum: v.terms + (v.terms === 1 ? ' term' : ' terms') + ': root-mean-square error ' + Kit.fmt(Model.error(v.terms), 3),
    rows: [['Sine terms used', String(v.terms)], ['Highest frequency', String(2 * v.terms - 1)], ['Share of the energy captured', Kit.fmt(100 * Model.energy(v.terms), 4) + '%'], ['Root-mean-square error', Kit.fmt(Model.error(v.terms), 3)], ['Highest point of the sum', Kit.fmt(Model.overshoot(v.terms), 4)]],
    result: 'The mean-square error falls toward 0 as terms are added: the sums converge to the square wave in that sense. But the peak beside each jump stays near 1.18, about 9% of the jump too high. Convergence on average is not convergence at every point (the Gibbs phenomenon).'};''', height=460,
    aria='A square wave and the sum of the chosen number of sine terms.')

add('truth-tables', 'math.5.logic', 'Logic and Set Theory', 'Truth tables and logical equivalence',
    'Two formulas are equivalent when they have the same truth value in every case. A truth table checks every case.',
    [('f', select('f', 'First formula', [('imp', 'P → Q'), ('and', 'P ∧ Q'), ('or', 'P ∨ Q'), ('iff', 'P ↔ Q'), ('nand', '¬(P ∧ Q)'), ('nor', '¬(P ∨ Q)'), ('taut', 'P ∨ ¬P')])),
     ('g', select('g', 'Second formula', [('ornot', '¬P ∨ Q'), ('contra', '¬Q → ¬P'), ('conv', 'Q → P'), ('demorgan', '¬P ∨ ¬Q'), ('demorgan2', '¬P ∧ ¬Q'), ('both', '(P → Q) ∧ (Q → P)'), ('absurd', 'P ∧ ¬P')]))], ['P', 'Q', 'First formula', 'Second formula'],
    '''  FORMULAS: {imp: (p, q) => !p || q, and: (p, q) => p && q, or: (p, q) => p || q, iff: (p, q) => p === q, nand: (p, q) => !(p && q), nor: (p, q) => !(p || q), taut: p => p || !p,
    ornot: (p, q) => !p || q, contra: (p, q) => !(!q) || !p, conv: (p, q) => !q || p, demorgan: (p, q) => !p || !q, demorgan2: (p, q) => !p && !q, both: (p, q) => (!p || q) && (!q || p), absurd: p => p && !p},
  CASES: [[true, true], [true, false], [false, true], [false, false]],
  table: name => Model.CASES.map(([p, q]) => Boolean(Model.FORMULAS[name](p, q))),
  equivalent: (f, g) => Model.table(f).every((value, i) => value === Model.table(g)[i]),
  tautology: name => Model.table(name).every(Boolean),
  contradiction: name => Model.table(name).every(value => !value),''',
    '''  const F = Model.table(v.f), G = Model.table(v.g), same = Model.equivalent(v.f, v.g), ctx = canvas.getContext('2d'), t = b => b ? 'T' : 'F', label = id => Kit.get(id).selectedOptions[0].textContent;
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.font = '18px system-ui, sans-serif';
  [['P', 60], ['Q', 150], [label('f'), 260], [label('g'), 480]].forEach(([text, x]) => { ctx.fillStyle = '#172533'; ctx.fillText(text, x, 34); });
  Model.CASES.forEach(([P, Q], i) => [[P, 60, 60], [Q, 150, 60], [F[i], 260, 190], [G[i], 480, 190]].forEach(([value, x, w]) => { ctx.fillStyle = value ? '#a9cdb1' : '#e9b3a8'; ctx.fillRect(x - 12, 50 + i * 44, w, 36); ctx.fillStyle = '#172533'; ctx.fillText(t(value), x, 75 + i * 44); }));
  ctx.strokeStyle = same ? '#3c7a4b' : '#b3261e'; ctx.lineWidth = 3; ctx.strokeRect(244, 46, 412, 4 * 44);
  const kind = name => Model.tautology(name) ? 'a tautology (always true)' : Model.contradiction(name) ? 'a contradiction (never true)' : 'sometimes true, sometimes false';
  return {sum: label('f') + (same ? '  ≡  ' : '  ≢  ') + label('g'),
    rows: Model.CASES.map(([P, Q], i) => [t(P), t(Q), t(F[i]), t(G[i])]),
    result: (same ? 'The two columns agree in all four cases, so the formulas are logically equivalent.' : 'The columns differ in at least one case, so the formulas are not equivalent.') + ' The first is ' + kind(v.f) + '; the second is ' + kind(v.g) + '.'};''', height=240,
    aria='A coloured truth table for the two formulas, green for true and red for false.', caption='Truth table')

add('cantor-set', 'math.5.measure', 'Measure Theory', 'The Cantor set: uncountable, yet of length zero',
    'Start with the interval from 0 to 1 and keep removing the open middle third of every piece. Measure what is left.',
    [('n', slider('n', 'Steps taken', 0, 7, 3))], ['Step', 'Pieces', 'Length of each', 'Total length'],
    '''  // The closed intervals left after n steps.
  intervals(n) { let out = [[0, 1]]; for (let i = 0; i < n; i++) out = out.flatMap(([a, b]) => [[a, a + (b - a) / 3], [b - (b - a) / 3, b]]); return out; },
  count: n => 2 ** n,
  length: n => (2 / 3) ** n,
  removed: n => 1 - (2 / 3) ** n,
  // Is x (a fraction p/q in lowest terms, given as a number) left after n steps?
  contains: (x, n) => Model.intervals(n).some(([a, b]) => x >= a - 1e-12 && x <= b + 1e-12),''',
    '''  const p = Kit.plot(canvas, {x: [-0.03, 1.03], y: [-0.6, v.n + 0.9], grid: false});
  for (let k = 0; k <= v.n; k++) { for (const [a, b] of Model.intervals(k)) p.line(a, v.n - k, b, v.n - k, '#215783', 12); p.text('step ' + k, 0, v.n - k, '#172533', -4, -12); }
  return {sum: Model.count(v.n) + ' pieces, total length ' + Kit.fmt(Model.length(v.n)),
    rows: Array.from({length: v.n + 1}, (_, k) => [String(k), String(Model.count(k)), '1/' + 3 ** k, 2 ** k + '/' + 3 ** k + ' ≈ ' + Kit.fmt(Model.length(k), 3)]),
    result: 'After ' + v.n + ' steps, ' + Kit.fmt(100 * Model.removed(v.n), 4) + '% of the length has been removed, and in the limit all of it: the Cantor set has measure 0. Yet endpoints such as 0, 1, 1/3 and 2/3 are never removed, and the set has as many points as the whole interval. Size by counting and size by measure are different ideas.'};''', height=360,
    aria='Rows of bars showing the pieces left after each step.', caption='What is left after each step')

add('newton-iteration', 'math.5.numerical', 'Numerical Analysis', 'Newton’s method and how fast it converges',
    'To find √a, guess x, then replace x by the average of x and a/x. Each step roughly doubles the number of correct digits.',
    [('a', slider('a', 'Find the square root of', 2, 50, 2)), ('x0', slider('x0', 'First guess', 1, 10, 1))], ['Step', 'Estimate', 'Error', 'Correct digits'],
    '''  step: (a, x) => (x + a / x) / 2,
  iterate(a, x0, steps) { const out = [x0]; for (let i = 0; i < steps; i++) out.push(Model.step(a, out[i])); return out; },
  error: (a, x) => Math.abs(x - Math.sqrt(a)),
  // Decimal digits that agree with the true root, capped by double precision.
  digits(a, x) { const e = Model.error(a, x) / Math.sqrt(a); return e < 1e-16 ? 16 : Math.max(0, Math.floor(-Math.log10(e))); },
  // Bisection on [lo, hi] for comparison: the bracket halves each step.
  bisect(a, lo, hi, steps) { for (let i = 0; i < steps; i++) { const mid = (lo + hi) / 2; if (mid * mid > a) hi = mid; else lo = mid; } return (lo + hi) / 2; },''',
    '''  const xs = Model.iterate(v.a, v.x0, 6), p = Kit.plot(canvas, {x: [-0.6, 6.6], y: [0, 17.5], xlabel: 'step', ylabel: 'correct digits'});
  xs.forEach((x, i) => { p.line(i, 0, i, Model.digits(v.a, x), '#215783', 26); p.point(i, Model.digits(v.a, Model.bisect(v.a, 0, Math.max(v.a, 1), i * 1)), '#963d18', 4); });
  return {sum: '√' + v.a + ' ≈ ' + Kit.fmt(xs[6], 16),
    rows: xs.map((x, i) => [String(i), Kit.fmt(x, 16), Model.error(v.a, x) < 1e-15 ? 'below 1e-15' : Kit.fmt(Model.error(v.a, x), 3), String(Model.digits(v.a, x))]),
    result: 'Once the estimate is close, the error is roughly squared at every step, so the correct digits double: quadratic convergence. Bisection (red dots) gains only about one digit every three or four steps. The machine stores about 16 digits, so no method can do better than that here.'};''', height=460,
    aria='Bars showing the number of correct digits after each Newton step, with bisection for comparison.', caption='Iterations')

add('heat-equation', 'math.5.pde', 'Partial Differential Equations', 'Heat flow along a rod',
    'A rod with both ends held at zero. Heat flows from hot to cold, and each sine-shaped mode of the temperature decays at its own rate.',
    [('start', select('start', 'Starting temperature', [('mix', 'sin(πx) + ½ sin(3πx)'), ('mode1', 'sin(πx)'), ('mode2', 'sin(2πx)'), ('mode3', 'sin(3πx)')])), ('t', slider('t', 'Time', 0, 5, 0.5, 0.1))], ['Mode', 'Starting size', 'Size now', 'Time to halve'],
    '''  ALPHA: 0.1,
  // [mode number, starting size] pairs.
  INITIAL: {mode1: [[1, 1]], mode2: [[2, 1]], mode3: [[3, 1]], mix: [[1, 1], [3, 0.5]]},
  decay: (k, t) => Math.exp(-Model.ALPHA * k * k * Math.PI ** 2 * t),
  halfLife: k => Math.log(2) / (Model.ALPHA * k * k * Math.PI ** 2),
  // Solution of u_t = α u_xx with u = 0 at both ends.
  u: (name, x, t) => Model.INITIAL[name].reduce((sum, [k, size]) => sum + size * Model.decay(k, t) * Math.sin(k * Math.PI * x), 0),''',
    '''  const p = Kit.plot(canvas, {x: [0, 1], y: [-1.6, 1.6], xlabel: 'position x', ylabel: 'temperature'});
  p.curve(x => Model.u(v.start, x, 0), '#9aa6ae', 0, 1, 2); p.curve(x => Model.u(v.start, x, v.t), '#963d18', 0, 1, 3);
  const middle = Model.u(v.start, 0.5, v.t);
  return {sum: 'Temperature at the middle: ' + Kit.fmt(Math.abs(middle) < 1e-9 ? 0 : middle, 3).replace('-', '−'),
    rows: Model.INITIAL[v.start].map(([k, size]) => ['sin(' + (k === 1 ? '' : k) + 'πx)', String(size), Kit.fmt(size * Model.decay(k, v.t), 3), Kit.fmt(Model.halfLife(k), 3)]),
    result: 'Mode k decays like e to the power −αk²π²t, so a mode with three times as many wiggles dies nine times as fast. Sharp detail vanishes first and the profile smooths toward the slowest mode. Grey is the start, red is now (α = ' + Model.ALPHA + ').'};''', height=460,
    aria='Temperature along the rod at the start and at the chosen time.', caption='Modes')

add('euler-characteristic', 'math.5.topology', 'Topology', 'Counting corners, edges and faces',
    'Topology studies what survives stretching. Corners minus edges plus faces is the same for every way of drawing a surface, and it tells surfaces apart.',
    [('solid', select('solid', 'Surface', [('cube', 'Cube'), ('tetrahedron', 'Tetrahedron'), ('octahedron', 'Octahedron'), ('dodecahedron', 'Dodecahedron'), ('icosahedron', 'Icosahedron'), ('prism', 'Triangular prism'), ('torus', 'Torus cut into a 3 × 3 grid'), ('doubletorus', 'Two-holed torus (one standard cutting)')]))], ['Surface', 'Corners V', 'Edges E', 'Faces F', 'V − E + F'],
    '''  SURFACES: {tetrahedron: [4, 6, 4], cube: [8, 12, 6], octahedron: [6, 12, 8], dodecahedron: [20, 30, 12], icosahedron: [12, 30, 20], prism: [6, 9, 5], torus: [9, 18, 9], doubletorus: [1, 4, 1]},
  NAMES: {tetrahedron: 'Tetrahedron', cube: 'Cube', octahedron: 'Octahedron', dodecahedron: 'Dodecahedron', icosahedron: 'Icosahedron', prism: 'Triangular prism', torus: 'Torus (3 × 3 grid)', doubletorus: 'Two-holed torus'},
  characteristic(name) { const [V, E, F] = Model.SURFACES[name]; return V - E + F; },
  // Number of holes of a closed orientable surface: χ = 2 − 2g.
  genus: name => (2 - Model.characteristic(name)) / 2,''',
    '''  const [V, E, F] = Model.SURFACES[v.solid], chi = Model.characteristic(v.solid), g = Model.genus(v.solid), p = Kit.plot(canvas, {x: [0, 4], y: [0, 34], grid: false});
  [['corners', V, '#215783'], ['edges', E, '#963d18'], ['faces', F, '#3c7a4b']].forEach(([name, count, colour], i) => { p.line(i + 1, 0, i + 1, count, colour, 60); p.text(name + ': ' + count, i + 1, count, '#172533', -34, -10); });
  p.line(0.3, 0, 3.7, 0, '#172533', 2);
  return {sum: 'V − E + F = ' + V + ' − ' + E + ' + ' + F + ' = ' + String(chi).replace('-', '−'),
    rows: Object.keys(Model.SURFACES).map(name => [Model.NAMES[name], ...Model.SURFACES[name].map(String), String(Model.characteristic(name)).replace('-', '−')]),
    result: g === 0 ? 'This surface can be inflated into a sphere, and every way of cutting a sphere into corners, edges and faces gives 2.' : 'This surface has ' + g + (g === 1 ? ' hole' : ' holes') + '. For a closed surface with g holes the count is always 2 − 2g, here ' + String(chi).replace('-', '−') + ', so it cannot be deformed into a sphere.'};''', height=300,
    aria='Bars for the numbers of corners, edges and faces.', caption='All the surfaces')

if __name__ == '__main__':
    print(base.build(), 'activities')

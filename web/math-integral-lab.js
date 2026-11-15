(function () {
'use strict';
const scenario = 'math.4.int-calc';
const definitions = Object.freeze({
  square: { label: '3x² · a power rule integral', formula: 'f(x) = 3x²', primitive: 'F(x) = x³', coefficients: [0, 0, 3], roots: [0] },
  linear: { label: '2x · an arbitrary constant', formula: 'f(x) = 2x', primitive: 'F(x) = x²', coefficients: [0, 2], roots: [0] },
  signed: { label: 'x² − 1 · signed change and total area', formula: 'f(x) = x² − 1', primitive: 'F(x) = x³/3 − x', coefficients: [-1, 0, 1], roots: [-1, 1] },
  velocity: { label: '6t · velocity in m/s', formula: 'v(t) = 6t m/s', primitive: 'F(t) = 3t² m', coefficients: [0, 6], roots: [0], variable: 't (s)', unit: 'm', nonnegative: true },
  inflow: { label: '4t + 1 · inflow in litres/minute', formula: 'r(t) = 4t + 1 L/min', primitive: 'F(t) = 2t² + t L', coefficients: [1, 4], roots: [-.25], variable: 't (min)', unit: 'L', nonnegative: true },
  increasing: { label: 'x² + 1 · positive, increasing on x > 0', formula: 'f(x) = x² + 1', primitive: 'F(x) = x³/3 + x', coefficients: [1, 0, 1], roots: [] },
  between: { label: 'x and x² · area between curves', formula: 'f(x) = x; g(x) = x²; h(x) = f(x) − g(x)', primitive: 'F(x) = x²/2 − x³/3 (an antiderivative of h)', coefficients: [0, 1, -1], roots: [0, 1] }
});
const initial = Object.freeze({ example: 'square', a: 0, b: 2, cursor: 1, constant: 0, count: 8, method: 'midpoint', singular: 'reciprocal', leftExponent: 2, rightExponent: 2, path: 'equal', power: .5 });
const presets = Object.freeze([
  ['power', 'Power rule: ∫₀² 3x² dx', { example: 'square', a: 0, b: 2, cursor: 1 }],
  ['constant', 'All antiderivatives differ by C', { example: 'linear', a: 0, b: 2, cursor: 1, constant: 2 }],
  ['signed', 'Signed change versus geometric area', { example: 'signed', a: -2, b: 2, cursor: 1 }],
  ['velocity', 'Velocity to distance: 0…4 seconds', { example: 'velocity', a: 0, b: 4, cursor: 2 }],
  ['between', 'The region between x and x²', { example: 'between', a: 0, b: 1, cursor: .5 }],
  ['inflow', 'Inflow to added volume: 0…3 minutes', { example: 'inflow', a: 0, b: 3, cursor: 1.5 }],
  ['increasing', 'Accumulation is rising and bending upward', { example: 'increasing', a: 0, b: 3, cursor: 1.5 }]
]);
const finite = (value, fallback, lo, hi) => typeof value === 'number' && Number.isFinite(value) && value >= lo && value <= hi ? value : fallback;
function normalize(raw = {}) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) raw = {};
  const example = Object.hasOwn(definitions, raw.example) ? raw.example : initial.example;
  const minimum = definitions[example].nonnegative ? 0 : -3;
  return { example, a: finite(raw.a, initial.a, minimum, 4), b: finite(raw.b, initial.b, minimum, 4), cursor: finite(raw.cursor, initial.cursor, minimum, 4), constant: finite(raw.constant, 0, -10, 10), count: Number.isInteger(raw.count) && raw.count >= 1 && raw.count <= 128 ? raw.count : 8, method: ['left', 'midpoint', 'right'].includes(raw.method) ? raw.method : 'midpoint', singular: ['reciprocal', 'power'].includes(raw.singular) ? raw.singular : 'reciprocal', leftExponent: finite(raw.leftExponent, 2, .5, 6), rightExponent: finite(raw.rightExponent, 2, .5, 6), path: ['equal', 'half', 'square', 'independent'].includes(raw.path) ? raw.path : 'equal', power: finite(raw.power, .5, .25, 2) };
}
const evaluate = (coefficients, x) => coefficients.reduceRight((sum, coefficient) => sum * x + coefficient, 0);
const primitive = (coefficients, x) => coefficients.reduce((sum, coefficient, degree) => sum + coefficient * x ** (degree + 1) / (degree + 1), 0);
const samples = (a, b, n = 160) => Array.from({ length: n + 1 }, (_, i) => a + (b - a) * i / n);
function definite(example, a, b) { return primitive(definitions[example].coefficients, b) - primitive(definitions[example].coefficients, a); }
function regions(example, a, b) {
  const definition = definitions[example], lo = Math.min(a, b), hi = Math.max(a, b);
  if (lo === hi) return [];
  const knots = [lo, ...definition.roots.filter(x => x > lo && x < hi), hi];
  return knots.slice(1).map((right, i) => {
    const left = knots[i], sign = Math.sign(evaluate(definition.coefficients, (left + right) / 2)), integral = definite(example, left, right);
    return { left, right, sign, integral, area: Math.abs(integral), points: samples(left, right, 48).map(x => [x, evaluate(definition.coefficients, x)]) };
  });
}
function quadrature(example, a, b, count, method) {
  // Bounds keep their orientation. 'Left' and 'right' refer to increasing x, even when a > b.
  const width = (b - a) / count, offset = method === 'midpoint' ? .5 : method === 'left' ? (width < 0 ? 1 : 0) : (width < 0 ? 0 : 1);
  const rectangles = Array.from({ length: count }, (_, i) => {
    const start = a + i * width, end = start + width, x = start + offset * width, height = evaluate(definitions[example].coefficients, x);
    return { start, end, x, height, width, contribution: width * height };
  });
  return { rectangles, sum: rectangles.reduce((sum, r) => sum + r.contribution, 0) };
}
function proper(raw = {}) {
  const state = normalize(raw), definition = definitions[state.example], { a, b, cursor, constant, count, method } = state, c = definition.coefficients;
  const exact = definite(state.example, a, b), split = regions(state.example, a, b), geometricArea = split.reduce((sum, region) => sum + region.area, 0), estimate = quadrature(state.example, a, b, count, method);
  const minimum = definition.nonnegative ? 0 : -3, low = Math.min(a, b, cursor), high = Math.max(a, b, cursor), margin = Math.max((high - low) * .1, .15);
  const domain = [Math.max(minimum, low - margin), Math.min(4, high + margin)], xs = samples(...domain, 224), accumulation = x => primitive(c, x) - primitive(c, a), slope = evaluate(c, cursor), current = accumulation(cursor), h = .2;
  const convergence = [1, 2, 4, 8, 16, 32, 64, 128].map(n => ({ n, ...Object.fromEntries(['left', 'midpoint', 'right'].map(type => [type, quadrature(state.example, a, b, n, type).sum])) }));
  return { state, formula: definition.formula, primitive: definition.primitive, domain, exact, geometricArea, average: a === b ? null : exact / (b - a), regions: split, ...estimate, error: estimate.sum - exact, convergence, splitAtProbe: { before: definite(state.example, a, cursor), after: definite(state.example, cursor, b) },
    integrand: xs.map(x => [x, evaluate(c, x)]), accumulation: xs.map(x => [x, accumulation(x)]), antiderivative: xs.map(x => [x, primitive(c, x) + constant]),
    cursor: { x: cursor, slope, accumulation: current, antiderivative: primitive(c, cursor) + constant, tangent: [Math.max(domain[0], cursor - h), Math.min(domain[1], cursor + h)].map(x => [x, current + (x - cursor) * slope]) },
    upperCurve: state.example === 'between' ? xs.map(x => [x, x]) : null, lowerCurve: state.example === 'between' ? xs.map(x => [x, x * x]) : null,
    ftc: 'All selected integrands are continuous. A(x) = ∫ₐˣ h(t) dt has derivative A′(x) = h(x). H(x) = F(x) + C has the same derivative, and H(b) − H(a) does not depend on C. Here h is the displayed integrand (f − g for the between-curves example).',
    note: 'The integral changes sign when the endpoints are reversed. Geometric area stays nonnegative and splits at every zero crossing. Left/right rectangles use the smaller/larger x endpoint of each subinterval; their signed widths follow a → b. Curves are sampled for display; numerical readouts use the stated polynomial antiderivative. Finite rectangle tables illustrate convergence; they do not prove convergence for arbitrary functions.' };
}
function improper(raw = {}) {
  const state = normalize(raw), { leftExponent: k, path, power: p } = state, leftEpsilon = 10 ** -k;
  const rightEpsilon = path === 'equal' ? leftEpsilon : path === 'half' ? leftEpsilon / 2 : path === 'square' ? leftEpsilon ** 2 : 10 ** -state.rightExponent;
  const reciprocal = (left, right) => ({ leftEpsilon: left, rightEpsilon: right, left: Math.log(left), right: -Math.log(right), combined: Math.log(left) - Math.log(right) });
  const endpoint = epsilon => p === 1 ? -Math.log(epsilon) : -Math.expm1((1 - p) * Math.log(epsilon)) / (1 - p);
  const rows = Array.from({ length: 6 }, (_, i) => {
    const exponent = i + 1, e = 10 ** -exponent, right = path === 'equal' ? e : path === 'half' ? e / 2 : path === 'square' ? e * e : 10 ** -state.rightExponent;
    return { exponent, ...reciprocal(e, right), powerIntegral: endpoint(e), powerRemainder: p < 1 ? e ** (1 - p) / (1 - p) : null };
  });
  return { state, ...reciprocal(leftEpsilon, rightEpsilon), powerIntegral: endpoint(leftEpsilon), powerLimit: p < 1 ? 1 / (1 - p) : null, powerRemainder: p < 1 ? leftEpsilon ** (1 - p) / (1 - p) : null, rows,
    reciprocalConverges: false, powerConverges: p < 1,
    verdict: state.singular === 'reciprocal' ? 'The ordinary improper integral of 1/x over [−1, 1] diverges. The left integral tends to −∞ and the right to +∞; both must converge separately. The symmetric Cauchy principal value is 0. It is a different limit.' : p < 1 ? 'The improper integral of x^(−p) over (0, 1] converges because p < 1. The omitted interval (0, ε) has area ε^(1−p)/(1−p), which tends to zero.' : 'The improper integral of x^(−p) over (0, 1] diverges because p ≥ 1. At p = 1 the truncated integral is −ln ε; for p > 1 it grows as a negative power of ε.',
    pathNote: path === 'equal' ? 'εR = εL: the finite truncated sums are zero along this symmetric path.' : path === 'half' ? 'εR = εL/2: both cutoffs approach zero, but every truncated sum is ln 2.' : path === 'square' ? 'εR = εL²: both cutoffs approach zero, but the truncated sum grows without bound.' : 'Independent cutoffs: the table varies εL while keeping the selected εR fixed. This is not a simultaneous limit of both cutoffs.' };
}
const fmt = value => value === null ? 'undefined' : Object.is(value, -0) || Math.abs(value) < 1e-12 ? '0' : Math.abs(value) >= 10000 || Math.abs(value) < .001 ? value.toExponential(4) : Number(value.toPrecision(7)).toString();
function render(item, hooks) {
  if (!['concept-lab', 'math-integral-lab'].includes(item?.renderer) || item.props?.scenario !== scenario) return null;
  const el = (tag, attrs = {}, ...children) => { const n = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); for (const child of children.flat(Infinity)) if (child != null) n.append(typeof child === 'object' ? child : document.createTextNode(String(child))); return n; };
  const svg = (tag, attrs = {}, ...children) => { const n = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); for (const child of children) n.append(typeof child === 'object' ? child : document.createTextNode(String(child))); return n; };
  let state = { ...initial }, station = 'proper', enlarged = false, model;
  const root = el('section', { class: 'card lesson-model math-integral-lab', 'data-renderer': 'math-integral-lab' });
  const tabs = el('select', { 'aria-label': 'Integral investigation', 'data-integral-station': '' }, el('option', { value: 'proper' }, 'Continuous integrals and accumulation'), el('option', { value: 'improper' }, 'Improper integrals: separate the limits'));
  const controls = el('div', { class: 'integral-controls' }), singularControls = el('div', { class: 'integral-controls' }), output = el('div', { class: 'integral-output' }), live = el('p', { role: 'status', 'aria-live': 'polite', class: 'integral-live' });
  const widgets = new Map();
  function select(parent, key, label, options) { const input = el('select', { 'aria-label': label, ['data-integral-' + key]: '' }); for (const [value, text] of options) input.append(el('option', { value }, text)); input.value = state[key]; parent.append(el('label', {}, label, input)); widgets.set(key, input); input.addEventListener('change', () => { state = normalize({ ...state, [key]: input.value }); if (station === 'proper') choice.value = 'custom'; update(); }); return input; }
  function number(parent, key, label, min, max, step) { const input = el('input', { type: 'number', min, max, step, value: state[key], 'aria-label': label, ['data-integral-' + key]: '' }); parent.append(el('label', {}, label, input)); widgets.set(key, input); const accept = () => { if (!input.validity.valid || input.value === '' || !Number.isFinite(input.valueAsNumber)) { input.setAttribute('aria-invalid', 'true'); live.textContent = 'Enter a value inside the labelled range. The accepted investigation remains displayed.'; return; } input.removeAttribute('aria-invalid'); state = normalize({ ...state, [key]: input.valueAsNumber }); if (station === 'proper') choice.value = 'custom'; update(); }; input.addEventListener('change', accept); input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); accept(); } if (e.key === 'Escape') { input.value = state[key]; input.removeAttribute('aria-invalid'); live.textContent = 'Restored the accepted value.'; } }); return input; }
  const choice = el('select', { 'aria-label': 'Integral example', 'data-integral-preset': '' }, el('option', { value: 'custom' }, 'Custom accepted controls'), ...presets.map(([id, title]) => el('option', { value: id }, title))); choice.value = 'power';
  choice.addEventListener('change', () => { const preset = presets.find(p => p[0] === choice.value); if (!preset) return; state = normalize({ ...initial, ...preset[2] }); update(); });
  select(controls, 'example', 'Integrand', Object.entries(definitions).map(([id, d]) => [id, d.label]));
  number(controls, 'a', 'Start a (−3…4; time examples 0…4)', -3, 4, .1); number(controls, 'b', 'End b (−3…4; time examples 0…4)', -3, 4, .1); number(controls, 'cursor', 'Probe x (−3…4; time examples 0…4)', -3, 4, .1); number(controls, 'constant', 'Antiderivative constant C (−10…10)', -10, 10, .5); number(controls, 'count', 'Rectangle count (1…128)', 1, 128, 1);
  select(controls, 'method', 'Rectangle sample', [['left', 'Left x endpoint'], ['midpoint', 'Midpoint'], ['right', 'Right x endpoint']]);
  select(singularControls, 'singular', 'Singular integrand', [['reciprocal', '1/x over [−1, 1]'], ['power', 'x^(−p) over (0, 1]']]);
  select(singularControls, 'path', 'Cutoff path', [['equal', 'Symmetric: εR = εL'], ['half', 'Offset: εR = εL/2'], ['square', 'Unequal rate: εR = εL²'], ['independent', 'Independent cutoffs']]);
  number(singularControls, 'leftExponent', 'Left cutoff exponent k: εL = 10^(−k)', .5, 6, .1); number(singularControls, 'rightExponent', 'Right cutoff exponent (independent path)', .5, 6, .1); number(singularControls, 'power', 'Power p (0.25…2)', .25, 2, .05);
  const zoom = el('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-integral-enlarge': '' }, 'Enlarge plots'); zoom.addEventListener('click', () => { enlarged = !enlarged; size(); });
  const reset = el('button', { type: 'button', class: 'btn ghost small', 'data-integral-reset': '' }, 'Reset investigation'); reset.addEventListener('click', () => { state = { ...initial }; choice.value = 'power'; update(); });
  root.append(el('h3', {}, 'Integrals: accumulation, area and limiting processes'), el('p', {}, 'Explore the same integrand as a signed area, a sum of rectangles, and the slope of its accumulation function. Then examine limits that cannot be cancelled.'), tabs, choice, controls, singularControls, el('div', { class: 'integral-actions' }, zoom, reset), output, live);
  const speech = () => Array.from(output.querySelectorAll(':scope > p, :scope > h4')).map(n => n.textContent).join(' '); root.getModelSpeech = speech; if (hooks?.speakButton) root.append(hooks.speakButton(speech));
  const colors = { blue: '#245f91', teal: '#24705e', coral: '#ab4936', gold: '#8a6512', grey: '#747267' };
  function chart(title, xLabel, yLabel, xd, values, name) {
    const lo = Math.min(0, ...values), hi = Math.max(0, ...values), pad = hi - lo > 1e-9 ? (hi - lo) * .12 : .5, yd = [lo - pad, hi + pad];
    const plot = svg('svg', { viewBox: '0 0 680 390', role: 'img', 'aria-label': title, 'data-integral-plot': name, 'data-domain': JSON.stringify({ x: xd, y: yd }), 'data-transform': JSON.stringify({ x0: 82, x1: 644, y0: 322, y1: 28 }) });
    const X = x => 82 + (x - xd[0]) * 562 / (xd[1] - xd[0]), Y = y => 322 - (y - yd[0]) * 294 / (yd[1] - yd[0]);
    for (let i = 0; i <= 4; i++) { const x = xd[0] + (xd[1] - xd[0]) * i / 4, y = yd[0] + (yd[1] - yd[0]) * i / 4; plot.append(svg('line', { x1: X(x), y1: 28, x2: X(x), y2: 322, stroke: '#d2cbbd' }), svg('line', { x1: 82, y1: Y(y), x2: 644, y2: Y(y), stroke: '#d2cbbd' }), svg('text', { x: X(x), y: 346, 'text-anchor': 'middle', 'font-size': 17 }, Number(x.toPrecision(4))), svg('text', { x: 73, y: Y(y) + 6, 'text-anchor': 'end', 'font-size': 16 }, Number(y.toPrecision(3)))); }
    if (xd[0] <= 0 && xd[1] >= 0) plot.append(svg('line', { x1: X(0), y1: 28, x2: X(0), y2: 322, stroke: colors.grey, 'stroke-width': 1.5 }));
    plot.append(svg('line', { x1: 82, y1: Y(0), x2: 644, y2: Y(0), stroke: colors.grey, 'stroke-width': 1.5 }), svg('text', { x: 360, y: 377, 'text-anchor': 'middle', 'font-size': 18 }, xLabel));
    const polyline = (points, color, role, attrs = {}) => { const line = svg('polyline', { points: points.map(([x, y]) => X(x) + ',' + Y(y)).join(' '), fill: 'none', stroke: color, 'stroke-width': 3, 'data-integral-series': role, ...attrs }); plot.append(line); return line; };
    const dot = (x, y, color, role) => plot.append(svg('circle', { cx: X(x), cy: Y(y), r: 5, fill: color, 'data-integral-point': role }));
    const wrap = el('div', { class: 'integral-viewport', tabindex: 0, role: 'region', 'aria-label': title + '; enlarge and scroll for detail' }, plot), figure = el('figure', {}, el('figcaption', {}, title), el('p', { class: 'integral-axis-caption' }, 'Vertical axis: ' + yLabel + '. Horizontal axis: ' + xLabel + '.'), wrap);
    return { figure, plot, X, Y, line: polyline, dot, yd };
  }
  function table(caption, heads, rows) { return el('div', { class: 'integral-table-scroll', tabindex: 0, role: 'region', 'aria-label': caption }, el('table', {}, el('caption', {}, caption), el('thead', {}, el('tr', {}, ...heads.map(h => el('th', { scope: 'col' }, h)))), el('tbody', {}, ...rows.map(row => el('tr', {}, ...row.map(v => el('td', {}, typeof v === 'number' ? fmt(v) : v))))))); }
  function drawProper(m) {
    const s = m.state, definition = definitions[s.example], unit = definition.unit ? ' ' + definition.unit : '', between = s.example === 'between';
    output.append(el('p', { class: 'integral-formula' }, m.formula + '. ' + m.primitive + '.'), el('p', { class: 'integral-readout' }, '∫ from ' + fmt(s.a) + ' to ' + fmt(s.b) + ' = ' + fmt(m.exact) + unit + '. Geometric area = ' + fmt(m.geometricArea) + unit + '. Average integrand = ' + fmt(m.average) + (m.average === null ? ' (the interval has zero width)' : '') + '.'), el('p', {}, 'At x = ' + fmt(s.cursor) + ', A(x) = ' + fmt(m.cursor.accumulation) + ' and A′(x) = h(x) = ' + fmt(m.cursor.slope) + '. H(x) = F(x) + ' + fmt(s.constant) + ' = ' + fmt(m.cursor.antiderivative) + '. Moving C shifts H but changes neither its slope nor the definite integral.'), el('p', {}, 'Split at the probe: ∫ from a to x = ' + fmt(m.splitAtProbe.before) + ', plus ∫ from x to b = ' + fmt(m.splitAtProbe.after) + ', equals ∫ from a to b = ' + fmt(m.exact) + '. This oriented identity also holds when the probe lies outside [a, b].'), el('p', {}, s.count + ' ' + s.method + ' rectangles give ' + fmt(m.sum) + '; signed approximation error = ' + fmt(m.error) + '. ' + (s.a > s.b ? 'Bounds run right to left; rectangle contributions reverse sign.' : s.a === s.b ? 'Equal bounds give an empty interval and integral zero.' : 'Bounds run left to right.')));
    const p = chart(between ? 'Two curves and their difference' : 'Integrand and signed rectangles', definition.variable || 'x', between ? 'f, g and h = f − g' : definition.formula, m.domain, [...m.integrand, ...(m.upperCurve || []), ...(m.lowerCurve || [])].map(p => p[1]), 'integrand');
    if (between) { for (const region of m.regions) { const xs = samples(region.left, region.right, 64), points = [...xs.map(x => [x, x]), ...xs.reverse().map(x => [x, x * x])]; p.plot.append(svg('polygon', { points: points.map(([x, y]) => p.X(x) + ',' + p.Y(y)).join(' '), fill: region.sign > 0 ? colors.teal : colors.coral, opacity: .22, 'data-integral-region': 'between', 'data-region-bounds': JSON.stringify([region.left, region.right]) })); } p.line(m.upperCurve, colors.blue, 'upper'); p.line(m.lowerCurve, colors.gold, 'lower'); }
    else for (const region of m.regions) p.plot.append(svg('polygon', { points: [[region.left, 0], ...region.points, [region.right, 0]].map(([x, y]) => p.X(x) + ',' + p.Y(y)).join(' '), fill: region.sign > 0 ? colors.teal : colors.coral, opacity: .18, 'data-integral-region': 'axis', 'data-region-bounds': JSON.stringify([region.left, region.right]) }));
    for (const r of m.rectangles) p.plot.append(svg('rect', { x: p.X(Math.min(r.start, r.end)), y: Math.min(p.Y(0), p.Y(r.height)), width: Math.abs(p.X(r.end) - p.X(r.start)), height: Math.abs(p.Y(0) - p.Y(r.height)), fill: r.height >= 0 ? colors.teal : colors.coral, 'fill-opacity': between ? .08 : .16, stroke: r.height >= 0 ? colors.teal : colors.coral, 'stroke-width': .8, 'data-integral-rectangle': '', 'data-rectangle': JSON.stringify(r) }));
    p.line(m.integrand, between ? colors.grey : colors.blue, 'integrand', between ? { 'stroke-dasharray': '6 4' } : {}); p.dot(s.cursor, m.cursor.slope, colors.coral, 'integrand-probe');
    for (const [value, name] of [[s.a, 'a'], [s.b, 'b']]) { p.plot.append(svg('line', { x1: p.X(value), y1: 28, x2: p.X(value), y2: 322, stroke: colors.grey, 'stroke-dasharray': '4 4', 'data-integral-bound': name })); }
    const a = chart('Accumulation and the antiderivative family', definition.variable || 'x', 'Accumulated value' + unit, m.domain, [...m.accumulation, ...m.antiderivative, ...m.cursor.tangent].map(p => p[1]), 'accumulation'); a.line(m.accumulation, colors.teal, 'accumulation'); a.line(m.antiderivative, colors.gold, 'antiderivative', { 'stroke-dasharray': '8 5' }); a.line(m.cursor.tangent, colors.coral, 'tangent', { 'stroke-width': 4 }); a.dot(s.cursor, m.cursor.accumulation, colors.coral, 'accumulation-probe'); a.dot(s.a, 0, colors.teal, 'anchor'); a.dot(s.b, m.exact, colors.blue, 'endpoint');
    output.append(el('div', { class: 'integral-plots' }, p.figure, a.figure), el('p', {}, between ? 'First graph: blue f(x) = x; gold g(x) = x²; dashed grey h = f − g. The region is split where the curves cross (x = 0 and x = 1). Rectangles approximate the signed integral of h.' : 'First graph: blue integrand. Teal regions lie above the axis; coral regions lie below. Each outlined rectangle uses the selected sample point.'), el('p', {}, 'Second graph: teal A(x) = F(x) − F(a); dashed gold H(x) = F(x) + C; coral tangent at the probe. The anchor is A(a) = 0; the blue endpoint is A(b). ' + m.ftc));
    const detail = el('details', {}, el('summary', {}, 'Compare rectangle refinements and inspect every signed region'), table('Refinement toward the analytic integral ' + fmt(m.exact), ['Rectangles', 'Left sum', 'Midpoint sum', 'Right sum'], m.convergence.map(r => [r.n, r.left, r.midpoint, r.right])), table('Regions in increasing x order', ['From', 'To', 'Signed integral', 'Geometric area'], m.regions.map(r => [r.left, r.right, r.integral, r.area]))); output.append(detail, el('p', { class: 'integral-note' }, m.note));
    if (s.example === 'velocity') output.append(el('p', {}, 'For t ≥ 0 the velocity is nonnegative. With chronological bounds a ≤ b, displacement and distance travelled agree. Reversed bounds show the oriented integral, not a negative physical distance.'));
    if (s.example === 'inflow') output.append(el('p', {}, 'This model uses t ≥ 0 minutes. With chronological bounds a ≤ b the integral is the volume added. Reversed bounds show the orientation rule, not an outward flow.'));
  }
  function drawImproper(m) {
    const reciprocal = m.state.singular === 'reciprocal';
    output.append(el('h4', {}, reciprocal ? 'A cancellation is not convergence' : 'The exponent decides endpoint convergence'), el('p', { class: 'integral-readout' }, m.verdict));
    if (reciprocal) {
      output.append(el('p', {}, 'εL = ' + fmt(m.leftEpsilon) + ', εR = ' + fmt(m.rightEpsilon) + '. From −1 to −εL: ∫ 1/x dx = ln εL = ' + fmt(m.left) + '; from εR to 1: ∫ 1/x dx = −ln εR = ' + fmt(m.right) + '. Finite truncated sum = ' + fmt(m.combined) + '.'), el('p', {}, m.pathNote));
      const p = chart('Each one-sided integral and their finite sum', 'k, where εL = 10^(−k)', 'Truncated integral', [1, 6], m.rows.flatMap(r => [r.left, r.right, r.combined]), 'limits'); p.line(m.rows.map(r => [r.exponent, r.left]), colors.coral, 'left-limit'); p.line(m.rows.map(r => [r.exponent, r.right]), colors.blue, 'right-limit'); p.line(m.rows.map(r => [r.exponent, r.combined]), colors.teal, 'combined-limit', { 'stroke-dasharray': '8 4' }); output.append(p.figure, el('p', {}, 'Coral: left integral. Blue: right integral. Dashed teal: finite sum. These exact logarithmic expressions establish the limiting behaviour; finite graph samples alone are not a proof. Change from symmetric to offset or unequal-rate cutoffs to see why cancellation does not define the ordinary improper integral.'), table('Separate cutoff values', ['k', 'εL', 'εR', 'Left', 'Right', 'Sum'], m.rows.map(r => [r.exponent, r.leftEpsilon, r.rightEpsilon, r.left, r.right, r.combined])));
    } else {
      output.append(el('p', {}, 'p = ' + fmt(m.state.power) + ', ε = ' + fmt(m.leftEpsilon) + '. ∫ε¹ x^(−p) dx = ' + fmt(m.powerIntegral) + '. ' + (m.powerConverges ? 'Limit = 1/(1−p) = ' + fmt(m.powerLimit) + '; omitted area = ' + fmt(m.powerRemainder) + '.' : 'There is no finite limit.')), el('p', {}, 'For p ≠ 1, the truncated integral is (1 − ε^(1−p))/(1−p). At p = 1 it is −ln ε. The case p = 1/2 has an unbounded integrand but a finite integral of 2.'));
      const limitLine = m.powerConverges ? [[1, m.powerLimit], [6, m.powerLimit]] : [], curve = m.rows.map(r => [r.exponent, r.powerIntegral]), p = chart('Accumulation as the endpoint cutoff shrinks', 'k, where ε = 10^(−k)', 'Truncated integral', [1, 6], [...curve, ...limitLine].map(p => p[1]), 'limits'); p.line(curve, colors.blue, 'power-limit'); for (const [x, y] of curve) p.dot(x, y, colors.blue, 'power-sequence'); if (limitLine.length) p.line(limitLine, colors.teal, 'finite-limit', { 'stroke-dasharray': '8 4' }); output.append(p.figure, el('p', {}, 'Blue dots: truncated integrals at integer k; joining segments are a visual guide. ' + (m.powerConverges ? 'Dashed teal: the finite limiting value. The explicit remainder measures the missing area.' : 'The values increase without a finite limit; the analytic expression establishes divergence.')), table('Endpoint cutoff sequence', ['k', 'ε', 'Truncated integral', 'Omitted area, if finite'], m.rows.map(r => [r.exponent, r.leftEpsilon, r.powerIntegral, r.powerRemainder === null ? 'diverges' : r.powerRemainder])));
    }
  }
  function size() { zoom.setAttribute('aria-pressed', String(enlarged)); zoom.textContent = enlarged ? 'Fit plots' : 'Enlarge plots'; for (const plot of root.querySelectorAll('[data-integral-plot]')) { plot.style.width = enlarged ? '900px' : '100%'; plot.style.minWidth = enlarged ? '900px' : ''; } }
  function update() {
    for (const [key, input] of widgets) { input.value = state[key]; input.removeAttribute('aria-invalid'); }
    const minimum = definitions[state.example].nonnegative ? 0 : -3; for (const key of ['a', 'b', 'cursor']) widgets.get(key).min = minimum;
    controls.hidden = station !== 'proper'; choice.hidden = station !== 'proper'; singularControls.hidden = station !== 'improper';
    for (const key of ['path', 'rightExponent']) widgets.get(key).closest('label').hidden = state.singular !== 'reciprocal'; widgets.get('rightExponent').closest('label').hidden = state.singular !== 'reciprocal' || state.path !== 'independent'; widgets.get('rightExponent').disabled = state.path !== 'independent'; widgets.get('power').closest('label').hidden = state.singular !== 'power';
    model = station === 'proper' ? proper(state) : improper(state); output.replaceChildren(); if (station === 'proper') drawProper(model); else drawImproper(model); root.setAttribute('data-integral-state', JSON.stringify({ station, ...state })); size(); live.textContent = station === 'proper' ? 'Integral ' + fmt(model.exact) + '. Rectangle sum ' + fmt(model.sum) + '.' : model.verdict;
  }
  tabs.addEventListener('change', () => { station = tabs.value; update(); });
  root.integral = { getState: () => ({ station, ...state }), getModel: () => JSON.parse(JSON.stringify(model)) };
  root.append(el('p', { class: 'integral-note' }, 'Definitions and theorem statements: ', el('a', { href: 'https://openstax.org/books/calculus-volume-1/pages/5-3-the-fundamental-theorem-of-calculus', target: '_blank', rel: 'noopener noreferrer' }, 'OpenStax: Fundamental Theorem'), '; ', el('a', { href: 'https://openstax.org/books/calculus-volume-2/pages/3-7-improper-integrals', target: '_blank', rel: 'noopener noreferrer' }, 'OpenStax: improper integrals'), '.'));
  update(); return root;
}
const api = Object.freeze({ scenario, definitions, initial, presets, normalize, evaluate, primitive, definite, regions, quadrature, proper, improper, render });
if (typeof window !== 'undefined') window.PrimerMathIntegralLab = api;
if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());

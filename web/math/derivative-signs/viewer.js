'use strict';

const get = id => document.getElementById(id);
const models = globalThis.PrimerDerivativeSigns;
const svgNamespace = 'http://www.w3.org/2000/svg';
const format = number => Number(number.toPrecision(6)).toString();
let cubicModel = models.cubic(1, 0);
let penModel = models.pen(6);

function mark(parent, tag, attributes = {}, text) {
  const element = document.createElementNS(svgNamespace, tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  if (text !== undefined) element.textContent = text;
  parent.append(element);
  return element;
}

function describe(svg, title, description) {
  svg.replaceChildren();
  mark(svg, 'title', { id: svg.id + '-title' }, title);
  mark(svg, 'desc', { id: svg.id + '-description' }, description);
}

function graph(svg, key, title, xDomain, yDomain, xTicks, yTicks, top, xLabel) {
  const left = 82, width = 478, height = 185;
  const X = x => left + width * (x - xDomain[0]) / (xDomain[1] - xDomain[0]);
  const Y = y => top + height * (yDomain[1] - y) / (yDomain[1] - yDomain[0]);
  mark(svg, 'text', { x: left, y: top - 23, class: 'title' }, title);
  for (const x of xTicks) {
    mark(svg, 'line', { x1: X(x), x2: X(x), y1: top, y2: top + height, class: 'grid' });
    mark(svg, 'text', { x: X(x), y: top + height + 22, 'text-anchor': 'middle' }, format(x));
  }
  for (const y of yTicks) {
    mark(svg, 'line', { x1: left, x2: left + width, y1: Y(y), y2: Y(y), class: 'grid' });
    mark(svg, 'text', { x: left - 12, y: Y(y) + 5, 'text-anchor': 'end' }, format(y));
  }
  mark(svg, 'line', { x1: left, x2: left + width, y1: Y(0), y2: Y(0), class: 'axis' });
  mark(svg, 'text', { x: left + width / 2, y: top + height + 47, 'text-anchor': 'middle' }, xLabel);
  const definitions = mark(svg, 'defs');
  const clip = mark(definitions, 'clipPath', { id: svg.id + '-' + key + '-clip' });
  mark(clip, 'rect', { x: left, y: top, width, height });
  const data = mark(svg, 'g', { 'clip-path': 'url(#' + clip.id + ')', 'data-plot': key });
  return { X, Y, data, top, height, domain: xDomain };
}

function polynomialCurve(plot, value, derivative, className) {
  const [start, end] = plot.domain, span = (end - start) / 3;
  const controls = [
    [start, value(start)],
    [start + span, value(start) + span * derivative(start)],
    [end - span, value(end) - span * derivative(end)],
    [end, value(end)],
  ];
  const [first, ...rest] = controls.map(([x, y]) => [plot.X(x), plot.Y(y)].join(','));
  // Endpoint values and derivatives give the exact cubic Bézier for these polynomials.
  mark(plot.data, 'path', { d: 'M' + first + ' C' + rest.join(' '), class: className, 'data-curve': className });
}

function probe(plot, x, y) {
  mark(plot.data, 'line', { x1: plot.X(x), x2: plot.X(x), y1: plot.top, y2: plot.top + plot.height, class: 'probe' });
  mark(plot.data, 'circle', { cx: plot.X(x), cy: plot.Y(y), r: 4.5, class: 'point', 'data-probe': '' });
}

function stationary(plot, x, y, label) {
  mark(plot.data, 'circle', { cx: plot.X(x), cy: plot.Y(y), r: 7, class: 'stationary', 'data-stationary': label });
  const labelY = plot.Y(y) - plot.top < 30 ? plot.Y(y) + 24 : plot.Y(y) - 11;
  mark(plot.data, 'text', { x: plot.X(x) + 12, y: labelY, 'data-stationary-label': label }, label);
}

function cubicExplanation(model) {
  if (model.a < 0) return 'The derivative is positive for every real x. The function increases throughout its domain.';
  if (model.a === 0) return 'At x = 0, the tangent is horizontal and the function keeps increasing. This is a stationary inflection. The value f″(0) = 0 alone is inconclusive about an extremum.';
  const [maximum, minimum] = model.stationary;
  return 'Point 1 is a local maximum at x = −√a ≈ ' + format(maximum.x) + ', f = ' + format(maximum.y) +
    '. Point 2 is a local minimum at x = √a ≈ ' + format(minimum.x) + ', f = ' + format(minimum.y) +
    '. The derivative changes sign at both points.';
}

function signTable(model) {
  const body = get('signs').tBodies[0];
  body.replaceChildren();
  const endpoints = model.a > 0 ? ['−∞', '−√a', '√a', '∞'] : model.a === 0 ? ['−∞', '0', '∞'] : ['−∞', '∞'];
  for (const [index, interval] of model.intervals.entries()) {
    const row = body.insertRow();
    const header = document.createElement('th');
    header.scope = 'row';
    header.textContent = '(' + endpoints[index] + ', ' + endpoints[index + 1] + ')';
    row.append(header);
    row.insertCell().textContent = interval.sign > 0 ? 'Positive' : 'Negative';
    row.insertCell().textContent = interval.sign > 0 ? 'Increasing' : 'Decreasing';
  }
}

function drawCubic() {
  cubicModel = models.cubic(get('parameter').valueAsNumber, get('probe').valueAsNumber);
  const { a, x, value, derivative, secondDerivative } = cubicModel;
  get('parameter-value').textContent = format(a);
  get('probe-value').textContent = format(x);
  const explanation = cubicExplanation(cubicModel);
  const readout = 'At x = ' + format(x) + ', f = ' + format(value) + ', f′ = ' + format(derivative) +
    ', and f″ = ' + format(secondDerivative) + '.';
  const chart = get('cubic-chart');
  describe(chart, 'Function and derivative for a = ' + format(a), readout + ' ' + explanation);
  const ticks = [-3, -2, -1, 0, 1, 2, 3];
  const upper = graph(chart, 'function', 'f(x) = x³ − 3ax', [-3, 3], [-40, 40], ticks, [-40, -20, 0, 20, 40], 50, 'x');
  const lower = graph(chart, 'derivative', 'f′(x) = 3(x² − a)', [-3, 3], [-15, 33], ticks, [-12, 0, 12, 24], 350, 'x');
  polynomialCurve(upper, t => t ** 3 - 3 * a * t, t => 3 * (t ** 2 - a), 'function');
  polynomialCurve(lower, t => 3 * (t ** 2 - a), t => 6 * t, 'derivative');
  mark(upper.data, 'line', {
    x1: upper.X(-3), x2: upper.X(3),
    y1: upper.Y(value + derivative * (-3 - x)), y2: upper.Y(value + derivative * (3 - x)),
    class: 'tangent',
  });
  probe(upper, x, value);
  probe(lower, x, derivative);
  for (const [index, point] of cubicModel.stationary.entries()) {
    stationary(upper, point.x, point.y, String(index + 1));
    stationary(lower, point.x, 0, String(index + 1));
  }
  signTable(cubicModel);
  get('cubic-readout').textContent = readout;
  get('stationary-note').textContent = explanation;
}

function drawPlan(model) {
  const plan = get('pen-plan');
  describe(plan, 'Rectangle with perimeter 40 metres',
    'Width ' + format(model.width) + ' metres, length ' + format(model.length) + ' metres and area ' +
    format(model.area) + ' square metres. Both plan axes use 18 display units per metre.');
  const X = x => 60 + x * 18, Y = y => 400 - y * 18;
  mark(plan, 'text', { x: 60, y: 22, class: 'title' }, 'Plan · equal scales on both axes');
  for (const coordinate of [0, 5, 10, 15, 20]) {
    mark(plan, 'line', { x1: X(coordinate), x2: X(coordinate), y1: Y(0), y2: Y(20), class: 'grid' });
    mark(plan, 'line', { x1: X(0), x2: X(20), y1: Y(coordinate), y2: Y(coordinate), class: 'grid' });
    mark(plan, 'text', { x: X(coordinate), y: 423, 'text-anchor': 'middle' }, coordinate);
    mark(plan, 'text', { x: 45, y: Y(coordinate) + 5, 'text-anchor': 'end' }, coordinate);
  }
  mark(plan, 'text', { x: 240, y: 452, 'text-anchor': 'middle' }, 'Width (m)');
  mark(plan, 'text', { transform: 'translate(18,220) rotate(-90)', 'text-anchor': 'middle' }, 'Length (m)');
  mark(plan, 'rect', {
    x: X(0), y: Y(model.length), width: model.width * 18, height: model.length * 18,
    class: 'plan', 'data-rectangle': '',
  });
  if (model.width === 0 || model.length === 0) {
    mark(plan, 'line', {
      x1: X(0), y1: Y(0), x2: X(model.width), y2: Y(model.length),
      class: 'plan', 'data-degenerate-plan': '',
    });
  }
}

function drawPen() {
  penModel = models.pen(get('width').valueAsNumber);
  const { width, length, area, derivative, areaShortfall } = penModel;
  get('width-value').textContent = format(width) + ' m';
  const collapsed = width === 0 || length === 0 ? ' The plan collapses to a line at this endpoint.' : '';
  const readout = 'Width ' + format(width) + ' m × length ' + format(length) + ' m. Perimeter 40 m. Area ' +
    format(area) + ' m². dA/dw = ' + format(derivative) + ' m² per metre. Deficit from the maximum ' +
    format(areaShortfall) + ' m².' + collapsed;
  get('pen-readout').textContent = readout;
  drawPlan(penModel);
  const chart = get('pen-chart'), ticks = [0, 5, 10, 15, 20];
  describe(chart, 'Area and derivative for the rectangular pen', readout + ' Area increases up to width 10 metres and decreases above 10 metres.');
  const upper = graph(chart, 'area', 'A(w) = w(20 − w) · area (m²)', [0, 20], [-5, 110], ticks, [0, 25, 50, 75, 100], 50, 'Width w (m)');
  const lower = graph(chart, 'area-derivative', 'dA/dw = 20 − 2w · m² per metre', [0, 20], [-22, 22], ticks, [-20, -10, 0, 10, 20], 350, 'Width w (m)');
  polynomialCurve(upper, w => w * (20 - w), w => 20 - 2 * w, 'function');
  mark(lower.data, 'line', { x1: lower.X(0), x2: lower.X(20), y1: lower.Y(20), y2: lower.Y(-20), class: 'derivative', 'data-linear-derivative': '' });
  probe(upper, width, area);
  probe(lower, width, derivative);
  stationary(upper, 10, 100, 'Maximum');
  stationary(lower, 10, 0, 'Zero');
}

function changeParameter(value) {
  get('parameter').value = value;
  get('feedback').textContent = '';
  get('prediction').reset();
  drawCubic();
}

get('parameter').addEventListener('input', () => changeParameter(get('parameter').value));
get('probe').addEventListener('input', drawCubic);
for (const button of document.querySelectorAll('[data-a]')) {
  button.addEventListener('click', () => changeParameter(button.dataset.a));
}
get('prediction').addEventListener('submit', event => {
  event.preventDefault();
  const prediction = new FormData(event.currentTarget).get('classification');
  get('feedback').textContent = (prediction === cubicModel.classification ? 'Correct. ' : 'Recheck the signs on either side of each derivative zero. ') +
    cubicExplanation(cubicModel);
});
get('width').addEventListener('input', drawPen);
get('show-maximum').addEventListener('click', () => {
  get('width').value = 10;
  drawPen();
});
get('pen-reset').addEventListener('click', () => {
  get('width').value = 6;
  drawPen();
});
get('station').addEventListener('change', () => {
  get('cubic-panel').hidden = get('station').value !== 'cubic';
  get('pen-panel').hidden = get('station').value !== 'pen';
});
get('cubic-chart').addEventListener('click', event => {
  const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(event.currentTarget.getScreenCTM().inverse());
  if (point.x < 82 || point.x > 560) return;
  const inGraph = (point.y >= 50 && point.y <= 235) || (point.y >= 350 && point.y <= 535);
  if (!inGraph) return;
  const x = -3 + 6 * (point.x - 82) / 478;
  get('probe').value = Math.round(x * 20) / 20;
  drawCubic();
});

drawCubic();
drawPen();

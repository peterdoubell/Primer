'use strict';

const linear = x => x + 2;
const sinc = x => x === 0 ? 1 : Math.sin(x) / x;
const left = x => x + 1;
const right = x => x * x;
const reciprocal = x => 1 / x;
const cases = {
  hole: {at: 2, box: [0, 4, 0, 7], left: linear, right: linear, value: null,
    formula: 'f(x) = (x² − 4)/(x − 2) for x ≠ 2.',
    result: 'Both sides approach 4. The function is undefined at 2.'},
  reassigned: {at: 2, box: [0, 4, 0, 7], left: linear, right: linear, value: 2,
    formula: 'f(x) = x + 2 for x ≠ 2. At x = 2, f(x) = 2.',
    result: 'Both sides approach 4. The assigned value f(2) = 2 leaves the limit unchanged.'},
  jump: {at: 2, box: [1, 3, 0, 10], left, right, value: null,
    formula: 'f(x) = x + 1 left of 2 and x² right of 2. At 2 it is undefined.',
    result: 'The left-hand limit is 3 and the right-hand limit is 4. The two-sided limit does not exist.'},
  sinc: {at: 0, box: [-2, 2, 0, 1.3], left: sinc, right: sinc, value: null,
    formula: 'f(x) = sin(x)/x for x ≠ 0, with x in radians.',
    result: 'Both sides approach 1. The original quotient is undefined at 0.'},
  infinity: {right: reciprocal, formula: 'f(x) = 1/x for x > 0.',
    result: 'As x increases without bound, 1/x approaches 0. For any positive target ε, x > 1/ε gives 1/x < ε.'},
};

const get = id => document.getElementById(id);
const choice = get('case');
const slider = get('step');
const canvas = get('graph');
const ctx = canvas.getContext('2d');
const distances = [0.5, 0.1, 0.01, 0.001, 0.0001];
const largeInputs = [2, 5, 10, 50, 100];
const format = number => Number(number.toPrecision(10)).toString();

function graph(model, samples, maximum) {
  const far = model.at === undefined;
  const [xmin, xmax, ymin, ymax] = far ? [0, maximum, 0, 1.2] : model.box;
  const x = value => 65 + (value - xmin) * 625 / (xmax - xmin);
  const y = value => 315 - (value - ymin) * 290 / (ymax - ymin);
  const line = (x0, y0, x1, y1) => {
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
  };
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = '17px system-ui';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const horizontal = xmin + (xmax - xmin) * i / 4;
    const vertical = ymin + (ymax - ymin) * i / 4;
    ctx.strokeStyle = '#d8dfe4';
    line(x(horizontal), y(ymin), x(horizontal), y(ymax));
    line(x(xmin), y(vertical), x(xmax), y(vertical));
    ctx.fillStyle = '#172533';
    ctx.fillText(format(horizontal), x(horizontal) - ctx.measureText(format(horizontal)).width / 2, 339);
    ctx.fillText(format(vertical), 9, y(vertical) + 6);
  }
  ctx.strokeStyle = '#172533';
  line(x(xmin), y(ymin), x(xmax), y(ymin));
  line(x(xmin), y(ymin), x(xmin), y(ymax));
  ctx.fillText('x', 708, 312);
  ctx.fillText('f(x)', 64, 17);
  function curve(start, end, fn, color) {
    ctx.beginPath();
    for (let i = 0; i <= 240; i++) {
      const input = start + (end - start) * i / 240;
      if (i === 0) ctx.moveTo(x(input), y(fn(input)));
      else ctx.lineTo(x(input), y(fn(input)));
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.stroke();
  }
  function point(input, value, color, open, radius) {
    ctx.beginPath();
    ctx.arc(x(input), y(value), radius, 0, 2 * Math.PI);
    ctx.fillStyle = open ? '#fff' : color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
  }
  if (far) {
    curve(1, xmax, model.right, '#215783');
  } else {
    curve(xmin, model.at, model.left, '#963d18');
    curve(model.at, xmax, model.right, '#215783');
  }
  for (const sample of samples) point(sample.input, sample.value, sample.color, false, 4.5);
  if (!far) {
    point(model.at, model.left(model.at), '#963d18', true, 7);
    if (model.left(model.at) !== model.right(model.at)) point(model.at, model.right(model.at), '#215783', true, 7);
    if (model.value !== null) point(model.at, model.value, '#172533', false, 7);
  }
}

function draw() {
  const model = cases[choice.value];
  const step = slider.valueAsNumber;
  const far = model.at === undefined;
  const distance = far ? largeInputs[step] : distances[step];
  const samples = far
    ? [{name: 'Towards infinity', input: distance, value: model.right(distance), color: '#215783'}]
    : [
      {name: 'From the left', input: model.at - distance, value: model.left(model.at - distance), color: '#963d18'},
      {name: 'From the right', input: model.at + distance, value: model.right(model.at + distance), color: '#215783'},
    ];
  get('formula').textContent = model.formula;
  get('distance').textContent = (far ? 'x = ' : 'Distance from target = ') + format(distance);
  slider.setAttribute('aria-valuetext', get('distance').textContent);
  get('rows').replaceChildren(...samples.map(sample => {
    const row = document.createElement('tr');
    const name = document.createElement('th');
    name.scope = 'row';
    name.textContent = sample.name;
    row.append(name);
    for (const value of [sample.input, sample.value]) row.insertCell().textContent = format(value);
    return row;
  }));
  const note = far
    ? 'The horizontal axis expands as x increases. The curve shows x ≥ 1.'
    : 'Orange approaches from the left and blue from the right. Open circles mark excluded values. The table distinguishes sample points that are too close to separate on the graph.';
  get('graph-note').textContent = note;
  get('result').textContent = model.result;
  canvas.setAttribute('aria-label', model.formula + ' ' + model.result);
  graph(model, samples, Math.max(4, 2 * distance));
}
choice.addEventListener('change', draw);
slider.addEventListener('input', draw);
draw();

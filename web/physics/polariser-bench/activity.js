const get = id => document.getElementById(id);
const degrees = Math.PI / 180;
const axes = ['#126980', '#745197', '#9a4c1d'];
const ink = '#1c3751';

function factor(angle) {
  const separation = Math.abs(angle) % 180;
  return separation === 90 ? 0 : Math.cos(angle * degrees) ** 2;
}

function transmission(final, middle) {
  return middle === null ? .5 * factor(final) : .5 * factor(middle) * factor(final - middle);
}

function plot(id) {
  const canvas = get(id);
  const width = Math.round(canvas.getBoundingClientRect().width);
  if (width && canvas.width !== width) canvas.width = width;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = '14px system-ui';
  return { canvas, ctx, width: canvas.width };
}

function path(ctx, coordinates, stroke, thickness = 1) {
  ctx.beginPath();
  coordinates.forEach(([x, y], index) => index ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
  ctx.strokeStyle = stroke;
  ctx.lineWidth = thickness;
  ctx.stroke();
}

function words(ctx, text, x, y, color = ink) {
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}

function faceAxes(final, middle) {
  const { canvas, ctx, width } = plot('filters');
  const filters = middle === null ? [['First', 0, axes[0]], ['Final', final, axes[2]]] :
    [['First', 0, axes[0]], ['Middle', middle, axes[1]], ['Final', final, axes[2]]];
  const distance = width / filters.length;
  const radius = Math.min(60, distance * .37);
  const y = 104;
  filters.forEach(([name, angle, colour], index) => {
    const x = distance * (index + .5);
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = '#e8f1f6';
    ctx.fill();
    ctx.strokeStyle = '#98aebc';
    ctx.lineWidth = 2;
    ctx.stroke();
    const dx = Math.cos(angle * degrees) * radius, dy = -Math.sin(angle * degrees) * radius;
    path(ctx, [[x - dx, y - dy], [x + dx, y + dy]], colour, 3);
    ctx.textAlign = 'center';
    words(ctx, name, x, y + radius + 25);
    words(ctx, angle + '°', x, y + radius + 45, colour);
    ctx.textAlign = 'start';
  });
  canvas.setAttribute('aria-label', filters.map(([name, angle]) => name + ' axis ' + angle + ' degrees').join('. '));
}

function drawCurve(final, middle) {
  const { canvas, ctx, width } = plot('curve');
  const left = 52, right = width - 22, top = 32, bottom = 221;
  const x = theta => left + (right - left) * theta / 180;
  const y = fraction => bottom - (bottom - top) * fraction / .5;
  const rate = theta => middle === null ? transmission(theta, null) : transmission(final, theta);
  const selected = middle === null ? final : middle;
  for (const tick of [0, .125, .25, .375, .5]) {
    path(ctx, [[left,y(tick)],[right,y(tick)]], '#dce5ed');
    words(ctx, 100 * tick + '%', 4, y(tick) + 5);
  }
  path(ctx, [[left,top],[left,bottom],[right,bottom]], ink);
  path(ctx, Array.from({length:181},(_, angle)=>[x(angle),y(rate(angle))]), '#315c9a', 2.5);
  path(ctx, [[x(selected),bottom],[x(selected),y(rate(selected))]], '#925019', 2);
  ctx.beginPath();
  ctx.arc(x(selected), y(rate(selected)), 4, 0, 2 * Math.PI);
  ctx.fillStyle = '#925019';
  ctx.fill();
  ctx.textAlign = 'center';
  for (const tick of [0,45,90,135,180]) words(ctx, tick+'°', x(tick),bottom+20);
  ctx.textAlign = 'start';
  words(ctx, (middle === null ? 'Final' : 'Middle') + ' axis angle', left, 262);
  canvas.setAttribute('aria-label', 'Final intensity versus ' + (middle === null ? 'final' : 'middle') +
    ' axis angle. Current transmission ' + (rate(selected) * 100).toFixed(2) + ' percent.');
  get('curve-explanation').textContent = middle === null ?
    'The curve turns the final axis while the first stays at 0°.' :
    'The curve turns the middle axis while the first and final axes stay fixed.';
}

function row(label, intensity, description) {
  const tr = document.createElement('tr');
  const name = document.createElement('th');
  name.scope = 'row';
  name.textContent = label;
  const value = document.createElement('td');
  value.textContent = (intensity * 100).toFixed(2) + '%';
  const factor = document.createElement('td');
  factor.textContent = description;
  tr.append(name, value, factor);
  return tr;
}

function render() {
  const final = get('final').valueAsNumber;
  const middle = get('include').checked ? get('middle').valueAsNumber : null;
  get('middle').disabled = middle === null;
  get('final-value').textContent = final + '°';
  get('middle-value').textContent = middle === null ? '—' : middle + '°';
  get('final').setAttribute('aria-valuetext', final + ' degrees');
  if (middle !== null) get('middle').setAttribute('aria-valuetext', middle + ' degrees');
  const lossAtFinal = factor(final - (middle ?? 0));
  const intensity = transmission(final, middle);
  const rows = [row('Input',1,'Unpolarised beam'),row('After first polariser',.5,'½')];
  if (middle !== null) rows.push(row('After middle polariser',.5 * factor(middle),'cos² ' + middle + '°'));
  rows.push(row('After final polariser',intensity,'cos² ' + Math.abs(final - (middle ?? 0)) +
    '° = ' + lossAtFinal.toFixed(4)));
  get('path').replaceChildren(...rows);
  faceAxes(final, middle);
  drawCurve(final, middle);
  const reference = middle === null ? '' :
    ' At the same outer angles, the two-filter transmission is ' + (transmission(final, null) * 100).toFixed(2) + '%.';
  get('result').textContent = 'Final intensity is ' + (intensity*100).toFixed(2) + '% of the unpolarised input.' + reference;
}

for (const id of ['final','middle','include']) get(id).addEventListener('input',render);
const resize=new ResizeObserver(render);
for(const id of ['filters','curve'])resize.observe(get(id));
render();

const get = id => document.getElementById(id);
const tau = 2 * Math.PI;
const blue = '#215c9c';
const orange = '#9a4710';
const ink = '#1b354c';
const muted = '#8199aa';
const maximumFrequency = 2.5;
const stiffness = tau * tau;

function response(frequency, ratio) {
  const angular = tau * frequency;
  const damping = 2 * ratio * tau;
  const amplitude = 1 / Math.hypot(stiffness - angular ** 2, damping * angular);
  const lag = Math.atan2(damping * angular, stiffness - angular ** 2);
  return { amplitude, lag, power: damping * (angular * amplitude) ** 2 / 2 };
}

function plot(id) {
  const canvas = get(id);
  const width = Math.round(canvas.getBoundingClientRect().width);
  if (width && canvas.width !== width) canvas.width = width;
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.font = '14px system-ui';
  return { canvas, context, width: canvas.width };
}

function line(ctx, points, colour, width = 1) {
  ctx.beginPath();
  points.forEach(([x, y], index) => index ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
  ctx.strokeStyle = colour;
  ctx.lineWidth = width;
  ctx.stroke();
}

function text(ctx, value, x, y, colour = ink) {
  ctx.fillStyle = colour;
  ctx.fillText(value, x, y);
}

function spring(displacement, force, maxAmplitude) {
  const { canvas, context, width } = plot('spring');
  const centre = width / 2;
  const scale = width * .30 / maxAmplitude;
  const x = centre + scale * displacement;
  const top = 64, middle = 91;
  line(context, [[18, 137], [width - 22, 137]], ink);
  line(context, [[18, 58], [18, 137]], ink, 3);
  context.setLineDash([4, 4]);
  line(context, [[centre, 48], [centre, 137]], muted);
  context.setLineDash([]);
  const coils = Array.from({length: 25}, (_, i) => [18 + (x - 40) * i / 24,
    middle + (i === 0 || i === 24 ? 0 : (i % 2 ? 10 : -10))]);
  line(context, coils, blue, 2);
  context.fillStyle = '#a5c4df';
  context.fillRect(x - 22, top, 44, 53);
  context.strokeStyle = ink;
  context.strokeRect(x - 22, top, 44, 53);
  const arrow = x + force * width * .13;
  if (Math.abs(arrow - x) > 3) {
    const direction = Math.sign(force);
    line(context, [[x, 155], [arrow, 155], [arrow - direction * 6, 151]], orange, 2);
    line(context, [[arrow, 155], [arrow - direction * 6, 159]], orange, 2);
  }
  text(context, 'Position x = ' + (displacement * 100).toFixed(2) + ' cm', 16, 188);
  text(context, 'Drive = ' + force.toFixed(2) + ' N', 16, 207, orange);
  canvas.setAttribute('aria-label', 'Mass at ' + (displacement * 100).toFixed(2) +
    ' centimetres from equilibrium with drive force ' + force.toFixed(2) + ' newtons');
}

function traces(lag, fraction) {
  const { canvas, context, width } = plot('traces');
  const left = 24, span = width - 42, middle = 112;
  const x = t => left + span * t;
  const y = value => middle - 64 * value;
  line(context, [[left, 39], [left, 176]], muted);
  line(context, [[left, middle], [x(1), middle]], muted);
  for (const [phase, colour] of [[0, orange], [lag, blue]]) {
    line(context, Array.from({length: 121}, (_, i) => {
      const t = i / 120;
      return [x(t), y(Math.cos(tau * t - phase))];
    }), colour, 2);
  }
  line(context, [[x(fraction), 39], [x(fraction), 176]], ink);
  text(context, 'Drive force', left, 23, orange);
  text(context, 'Displacement', Math.max(left + 86, width / 2), 23, blue);
  text(context, '0', left, 201);
  text(context, 'One period', x(1) - 72, 201);
  canvas.setAttribute('aria-label', 'Normalized drive and displacement. Displacement lags by ' +
    (lag * 180 / Math.PI).toFixed(1) + ' degrees');
}

function frequencyPlots(frequency, ratio, maxAmplitude) {
  const { canvas, context, width } = plot('response');
  const left = 55, right = width - 17;
  const x = f => left + (right - left) * f / maximumFrequency;
  const panels = [
    { title: 'Amplitude (cm)', top: 35, bottom: 125, maximum: maxAmplitude, value: row => row.amplitude,
      label: (maxAmplitude * 100).toFixed(1), colour: blue },
    { title: 'Phase lag (degrees)', top: 162, bottom: 252, maximum: Math.PI, value: row => row.lag,
      label: '180', colour: orange },
  ];
  for (const { title, top, bottom, maximum, label, value, colour } of panels) {
    const y = n => bottom - (bottom - top) * n / maximum;
    line(context, [[left, top], [left, bottom], [right, bottom]], ink);
    line(context, [[left, top], [right, top]], muted);
    line(context, Array.from({length: 201}, (_, i) => {
      const f = maximumFrequency * i / 200;
      return [x(f), y(value(response(f, ratio)))];
    }), colour, 2);
    const current = x(frequency);
    line(context, [[current, top], [current, bottom]], ink);
    context.fillStyle = colour;
    context.beginPath();
    context.arc(current, y(value(response(frequency, ratio))), 3.5, 0, tau);
    context.fill();
    text(context, title, left, top - 10);
    text(context, label, 11, top + 5);
    text(context, '0', left - 17, bottom + 5);
  }
  for (const f of [.5, 1, 1.5, 2, 2.5]) text(context, String(f), x(f) - 10, 271);
  text(context, 'Drive frequency (Hz)', left, 289);
  canvas.setAttribute('aria-label', 'Amplitude and phase response versus frequency at damping ratio ' + ratio.toFixed(2));
}

function render() {
  const frequency = get('frequency').valueAsNumber;
  const ratio = get('damping').valueAsNumber;
  const fraction = get('phase').valueAsNumber / 100;
  const point = response(frequency, ratio);
  const peakFrequency = ratio < Math.SQRT1_2 ? Math.sqrt(1 - 2 * ratio ** 2) : 0;
  const maxAmplitude = response(peakFrequency, ratio).amplitude;
  const time = fraction / frequency;
  spring(point.amplitude * Math.cos(tau * fraction - point.lag), Math.cos(tau * fraction), maxAmplitude);
  traces(point.lag, fraction);
  frequencyPlots(frequency, ratio, maxAmplitude);
  const controls = [
    ['frequency', frequency.toFixed(2) + ' Hz'],
    ['damping', ratio.toFixed(2)],
    ['phase', time.toFixed(3) + ' s'],
  ];
  for (const [id, value] of controls) {
    get(id + '-value').textContent = value;
    get(id).setAttribute('aria-valuetext', value);
  }
  const values = [
    ['Displacement amplitude', (point.amplitude * 100).toFixed(4) + ' cm'],
    ['Lag behind drive force', (point.lag * 180 / Math.PI).toFixed(3) + '°'],
    ['Average power from drive', (point.power * 1000).toFixed(4) + ' mW'],
  ];
  get('measurements').replaceChildren(...values.map(([name, value]) => {
    const row = document.createElement('tr');
    const heading = document.createElement('th');
    heading.scope = 'row';
    heading.textContent = name;
    const cell = document.createElement('td');
    cell.textContent = value;
    row.append(heading, cell);
    return row;
  }));
  get('peak').textContent = peakFrequency > 0
    ? 'The displacement amplitude peaks at ' + peakFrequency.toFixed(3) + ' Hz. The phase lag is 90° at the undamped natural frequency of 1 Hz.'
    : 'The amplitude decreases from its zero-frequency value. The phase lag is still 90° at 1 Hz.';
}
for (const id of ['frequency','damping','phase']) get(id).addEventListener('input', render);
const resize = new ResizeObserver(render);
for (const id of ['spring','traces','response']) resize.observe(get(id));
render();

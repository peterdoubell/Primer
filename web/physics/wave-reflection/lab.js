'use strict';

const amplitude = 4;
const wavelength = 3;
const frequency = 2;
const get = id => document.getElementById(id);
const mode = get('end');
const phase = get('phase');
const canvas = get('wave');
const context = canvas.getContext('2d');
const palettes = ['#a04517', '#245890', '#146745'];

function draw() {
  const fixed = mode.value === 'fixed';
  const time = phase.valueAsNumber / (frequency * 100);
  const radians = 2 * Math.PI * frequency * time;
  const incident = x => amplitude * Math.cos(2 * Math.PI * x / wavelength + radians);
  const reflected = x => (fixed ? -1 : 1) * amplitude * Math.cos(2 * Math.PI * x / wavelength - radians);
  const sum = x => incident(x) + reflected(x);
  const values = [incident(0), reflected(0), sum(0)];
  const unit = value => (Math.abs(value) < .0005 ? 0 : value).toFixed(3) + ' cm';
  const timeText = time.toFixed(3) + ' s';
  get('time').textContent = timeText;
  phase.setAttribute('aria-valuetext', timeText);
  for (const [i, id] of ['incident', 'reflected', 'sum'].entries()) get(id).textContent = unit(values[i]);

  const explanation = fixed
    ? 'At a fixed end the two displacements cancel at every instant. The boundary is a node.'
    : 'At a free end the two displacements add with the same sign. The boundary is an antinode, with a maximum displacement of 8 cm in either direction.';
  get('result').textContent = explanation;
  canvas.setAttribute('aria-label', 'Incident, reflected and summed displacements at ' + timeText + '. ' + explanation);
  const displayWidth = Math.round(canvas.getBoundingClientRect().width);
  if (displayWidth > 0 && displayWidth !== canvas.width) canvas.width = displayWidth;
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.font = '14px system-ui';

  for (const [row, [label, fn]] of [['Incident wave', incident], ['Reflected wave', reflected], ['String displacement', sum]].entries()) {
    const centre = 83 + 126 * row;
    const left = 55;
    const width = canvas.width - left - 22;
    const scale = 4.5;
    context.lineWidth = 1;
    context.strokeStyle = '#b9c4cb';
    context.beginPath();
    context.moveTo(left, centre - 8 * scale);
    context.lineTo(left, centre + 8 * scale);
    for (const tick of [-8, 8]) {
      const height = centre - tick * scale;
      context.moveTo(left - 5, height);
      context.lineTo(left, height);
    }
    context.moveTo(left, centre);
    context.lineTo(left + width, centre);
    context.stroke();
    context.fillStyle = '#192938';
    context.fillText(label, left, centre - 47);
    context.fillText('+8', 12, centre - 8 * scale + 5);
    context.fillText('−8', 12, centre + 8 * scale + 5);
    if (row === 2) {
      for (let x = 0; x <= 6; x += 1.5) context.fillText(String(x), left + width * x / 6 - 5, 390);
      const axisLabel = 'Distance from boundary (m)';
      context.fillText(axisLabel, (canvas.width - context.measureText(axisLabel).width) / 2, 414);
    }
    context.beginPath();
    for (let sample = 0; sample <= 600; sample++) {
      const px = left + width * sample / 600;
      const py = centre - scale * fn(sample / 100);
      if (sample === 0) context.moveTo(px, py);
      else context.lineTo(px, py);
    }
    context.strokeStyle = palettes[row];
    context.lineWidth = 2.5;
    context.stroke();
    context.beginPath();
    context.arc(left, centre - scale * values[row], 4, 0, 2 * Math.PI);
    context.fillStyle = palettes[row];
    context.fill();
  }
}
mode.addEventListener('change', draw);
phase.addEventListener('input', draw);
new ResizeObserver(draw).observe(canvas);
draw();

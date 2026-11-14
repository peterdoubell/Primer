'use strict';

const earthRadius = 6371; // km
const earthMu = 398600.44; // km³/s²
const get = id => document.getElementById(id);
const radius = get('radius');
const mass = get('mass');
const phase = get('phase');
const canvas = get('orbit');
const ctx = canvas.getContext('2d');
const format = (n, digits = 2) => n.toLocaleString('en-GB', {maximumFractionDigits: digits});

function calculate(multiple, kg) {
  const r = earthRadius * multiple;
  const acceleration = 1000 * earthMu / r ** 2;
  const speed = Math.sqrt(earthMu / r);
  return {altitude: r - earthRadius, acceleration, force: kg * acceleration,
    speed, periodHours: 2 * Math.PI * r / speed / 3600};
}

function diagram(multiple, angle) {
  const centre = [320, 230];
  const orbitRadius = Math.min(163, multiple * 57);
  const planetRadius = orbitRadius / multiple;
  const position = [centre[0] + orbitRadius * Math.cos(angle), centre[1] - orbitRadius * Math.sin(angle)];
  const circle = (point, r) => {
    ctx.beginPath();
    ctx.arc(...point, r, 0, 2 * Math.PI);
  };
  function line(x0, y0, x1, y1) {
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
  }
  function arrow(direction, color, label, offset) {
    const endpoint = [position[0] + direction[0] * 54, position[1] + direction[1] * 54];
    const theta = Math.atan2(direction[1], direction[0]);
    ctx.strokeStyle = ctx.fillStyle = color;
    ctx.lineWidth = 3;
    line(...position, ...endpoint);
    for (const turn of [-.48,.48]) line(...endpoint,
      endpoint[0] - 11 * Math.cos(theta + turn), endpoint[1] - 11 * Math.sin(theta + turn));
    const labelX = Math.min(canvas.width - ctx.measureText(label).width - 10, Math.max(10, endpoint[0] + offset[0]));
    const labelY = Math.min(canvas.height - 10, Math.max(23, endpoint[1] + offset[1]));
    ctx.fillText(label, labelX, labelY);
  }

  ctx.fillStyle = '#101f32';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.font = '20px system-ui';
  ctx.strokeStyle = '#7893ab';
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 8]);
  circle(centre, orbitRadius);
  ctx.stroke();
  ctx.setLineDash([]);
  circle(centre, planetRadius);
  const globe = ctx.createRadialGradient(centre[0] - planetRadius * .35, centre[1] - planetRadius * .35, 0,
    ...centre, planetRadius);
  globe.addColorStop(0, '#6cd3df');
  globe.addColorStop(1, '#184a7a');
  ctx.fillStyle = globe;
  ctx.fill();
  ctx.strokeStyle = '#eef5fa';
  ctx.lineWidth = 1;
  line(...centre, ...position);
  ctx.fillStyle = '#eef5fa';
  ctx.fillText('Earth', centre[0] - 24, centre[1] + planetRadius + 25);
  ctx.fillText('r', (centre[0] + position[0]) / 2, (centre[1] + position[1]) / 2 - 8);
  arrow([-Math.cos(angle), Math.sin(angle)], '#ffc276', 'Inward gravity', [12, 33]);
  arrow([Math.sin(angle), Math.cos(angle)], '#80e6ed', 'Velocity', [11, 7]);
  circle(position, 6);
  ctx.fillStyle = '#fff';
  ctx.fill();
}

function draw() {
  const multiple = radius.valueAsNumber;
  const kg = mass.valueAsNumber;
  get('distance').textContent = format(multiple) + ' Earth radii';
  get('mass-value').textContent = format(kg) + ' kg';
  radius.setAttribute('aria-valuetext', get('distance').textContent);
  mass.setAttribute('aria-valuetext', get('mass-value').textContent);
  const near = calculate(multiple, kg);
  const far = calculate(2 * multiple, kg);
  const quantities = [
    ['Altitude', 'altitude', 'km', 0],
    ['Gravity g = μ/r²', 'acceleration', 'm/s²', 3],
    ['Force F = mg', 'force', 'N', 2],
    ['Orbital speed', 'speed', 'km/s', 3],
    ['Orbital period', 'periodHours', 'h', 2],
  ];
  get('rows').replaceChildren(...quantities.map(([label, key, unit, precision]) => {
    const row = document.createElement('tr');
    const heading = document.createElement('th');
    heading.scope = 'row';
    heading.textContent = label;
    row.append(heading);
    for (const point of [near, far]) row.insertCell().textContent = format(point[key], precision) + ' ' + unit;
    return row;
  }));
  const status = 'At twice the distance, gravity and force are one quarter as large. Circular speed is about 71% as large and the period is about 2.83 times longer.';
  get('status').textContent = status;
  canvas.setAttribute('aria-label', 'A circular orbit at ' + format(multiple) +
    ' Earth radii. The gravity arrow points to Earth’s centre and the velocity arrow is tangent to the orbit.');
  const fraction = phase.valueAsNumber / 100;
  const elapsed = phase.value + '% · ' + format(fraction * near.periodHours, 2) + ' h';
  get('elapsed').textContent = elapsed;
  phase.setAttribute('aria-valuetext', elapsed);
  diagram(multiple, fraction * 2 * Math.PI);
}

for (const control of [radius, mass, phase]) control.addEventListener('input', draw);
draw();

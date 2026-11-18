import { angularRadius, causticHeight, radians, traceRay, visibleHalfArc, waterIndex } from './optics.mjs';

const element = id => document.getElementById(id);
const order = element('order');
const wavelength = element('wavelength');
const height = element('height');
const sun = element('sun');

const swatches = [
  [400, [174, 122, 246]],
  [445, [117, 145, 255]],
  [485, [85, 191, 250]],
  [520, [105, 217, 139]],
  [575, [249, 221, 106]],
  [610, [252, 155, 94]],
  [700, [239, 89, 103]],
];
const ink = '#dedfdf';
const muted = '#9baac0';
const grid = '#314357';
const gold = '#ffe0a0';
const degrees = angle => `${(angle / radians).toFixed(1)}°`;
const plainDegrees = angle => angle / radians;

function colour(nm) {
  const high = swatches.findIndex(([edge]) => edge >= nm);
  if (high <= 0) return `rgb(${swatches[0][1].join(',')})`;
  const [start, a] = swatches[high - 1];
  const [end, b] = swatches[high];
  const fraction = (nm - start) / (end - start);
  const channels = a.map((value, index) => Math.round(value + fraction * (b[index] - value)));
  return `rgb(${channels.join(',')})`;
}

function line(ctx, points, stroke, width = 2, dash = []) {
  if (!points.length) return;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = width;
  ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(...points[0]);
  for (const point of points.slice(1)) ctx.lineTo(...point);
  ctx.stroke();
  ctx.setLineDash([]);
}

function dot(ctx, [x, y], radius, fill, stroke) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, 2 * Math.PI);
  ctx.fill();
  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 3;
    ctx.stroke();
  }
}

function label(ctx, text, x, y, alignment = 'left', fill = ink) {
  ctx.font = '25px system-ui, sans-serif';
  ctx.textAlign = alignment;
  ctx.fillStyle = fill;
  ctx.fillText(text, x, y);
}

function reset(id) {
  const canvas = element(id);
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  return ctx;
}

function arrow(ctx, points, stroke) {
  line(ctx, points, stroke, 5);
  const [a, b] = points;
  const angle = Math.atan2(b[1] - a[1], b[0] - a[0]);
  line(ctx, [
    [b[0] - 17 * Math.cos(angle - .55), b[1] - 17 * Math.sin(angle - .55)],
    b,
    [b[0] - 17 * Math.cos(angle + .55), b[1] - 17 * Math.sin(angle + .55)],
  ], stroke, 5);
}

function drawDrop(ray, heightRatio, nm) {
  const ctx = reset('drop');
  const centre = [480, 300];
  const radius = 172;
  const pixel = ([x, y]) => [centre[0] + radius * x, centre[1] - radius * y];
  const water = ctx.createRadialGradient(420, 226, 35, 480, 300, radius);
  water.addColorStop(0, '#284964');
  water.addColorStop(1, '#152d46');
  dot(ctx, centre, radius, water, '#7ca7c3');
  line(ctx, [pixel([-1.1, 0]), pixel([1.1, 0])], '#7190a5', 2, [7, 9]);
  dot(ctx, centre, 4, '#aebdcf');

  const incidentStart = pixel([-2.51, heightRatio]);
  const rendered = ray.points.map(pixel);
  const [entry] = rendered;
  const outboundStart = ray.points.at(-1);
  const outboundEnd = [
    outboundStart[0] + 1.04 * ray.outgoing[0],
    outboundStart[1] + 1.04 * ray.outgoing[1],
  ];
  const rayColour = colour(nm);
  const incomingLabelY = heightRatio > 0.82 ? incidentStart[1] - 16 : incidentStart[1] - 30;
  label(ctx, 'Sunlight', incidentStart[0], incomingLabelY);
  arrow(ctx, [incidentStart, entry], rayColour);
  line(ctx, rendered, '#0b192a', 11);
  line(ctx, rendered, rayColour, 6);
  arrow(ctx, [pixel(outboundStart), pixel(outboundEnd)], rayColour);

  rendered.forEach((point, index) => {
    const atBoundary = index === 0 || index === ray.points.length - 1;
    dot(ctx, point, atBoundary ? 8 : 11, atBoundary ? '#edf5fe' : rayColour, '#111b29');
  });
}

function drawAngles(ratio, peak, index, reflections, nm) {
  const ctx = reset('angles');
  const left = 94, right = 786, top = 48, bottom = 501;
  const minimum = reflections === 1 ? 0 : 45;
  const maximum = reflections === 1 ? 50 : 180;
  const ticks = reflections === 1 ? [0, 10, 20, 30, 40, 50] : [45, 70, 95, 120, 145, 170];
  const x = value => left + (right - left) * value;
  const y = value => bottom - (bottom - top) * (value - minimum) / (maximum - minimum);

  for (const degree of ticks) {
    const height = y(degree);
    line(ctx, [[left, height], [right, height]], grid);
    label(ctx, `${degree}°`, left - 16, height + 8, 'right', muted);
  }
  line(ctx, [[left, top], [left, bottom], [right, bottom]], '#697c92', 3);
  for (const ratioTick of [0, .25, .5, .75, 1]) {
    line(ctx, [[x(ratioTick), bottom], [x(ratioTick), bottom + 10]], '#697c92', 3);
    label(ctx, ratioTick.toString(), x(ratioTick), bottom + 36, 'center', muted);
  }
  label(ctx, 'Distance from centre ÷ radius', (left + right) / 2, 580, 'center');
  label(ctx, 'Angle from the point opposite the Sun', left, 30);
  const samples = Array.from({ length: 257 }, (_, sample) => {
    // Quadratic spacing resolves the steep turn near grazing incidence.
    const position = 1 - (1 - sample / 256) ** 2;
    return [x(position), y(plainDegrees(angularRadius(position, index, reflections)))];
  });
  line(ctx, samples, colour(nm), 5);
  const peakX = x(peak);
  const peakY = y(plainDegrees(angularRadius(peak, index, reflections)));
  line(ctx, [[peakX, peakY], [peakX, bottom]], gold, 2, [7, 7]);
  line(ctx, [[peakX, peakY - 15], [peakX + 15, peakY], [peakX, peakY + 15],
    [peakX - 15, peakY], [peakX, peakY - 15]], gold, 3);
  dot(ctx, [x(ratio), y(plainDegrees(angularRadius(ratio, index, reflections)))], 7, '#ffffff', '#172537');
}

const skyArcs = [1, 2].map(reflections =>
  Array.from({ length: 301 }, (_, position) => {
    const nm = position + 400;
    const index = waterIndex(nm);
    return { nm, radius: angularRadius(causticHeight(index, reflections), index, reflections) };
  })
);

function drawSky(sunElevation, nm, reflections) {
  const ctx = reset('sky');
  const centre = [480, 540];
  const pixels = 7.45;
  const steps = 120;
  const project = (radius, azimuth) => [
    centre[0] + pixels * plainDegrees(radius) * Math.sin(azimuth),
    centre[1] - pixels * plainDegrees(radius) * Math.cos(azimuth),
  ];
  const arc = (radius, halfArc) => Array.from({ length: steps + 1 }, (_, step) =>
    project(radius, halfArc * (2 * step / steps - 1)));
  const ground = [];
  for (let sample = 0; sample <= steps; sample++) {
    const azimuth = Math.PI * (sample / steps - .5);
    const horizonRadius = sunElevation === 0 ? 62 * radians : Math.atan(Math.tan(sunElevation) / Math.cos(azimuth));
    if (horizonRadius <= 62 * radians) ground.push(project(horizonRadius, azimuth));
  }

  for (const radius of [20, 40, 60]) {
    line(ctx, arc(radius * radians, Math.PI / 2), grid, 2, [5, 7]);
    label(ctx, `${radius}°`, centre[0] + 18, centre[1] - radius * pixels + 24, 'left', muted);
  }
  line(ctx, [[27, centre[1]], [933, centre[1]]], grid, 2);
  line(ctx, [[centre[0], 63], centre], grid, 2, [5, 7]);
  if (sunElevation === 0) {
    line(ctx, [[25, centre[1]], [935, centre[1]]], '#93aac0', 3);
  } else {
    line(ctx, ground, '#93aac0', 3);
  }

  for (const family of skyArcs) {
    for (const sample of family) {
      const halfArc = visibleHalfArc(sample.radius, sunElevation);
      if (halfArc > 0) line(ctx, arc(sample.radius, halfArc), colour(sample.nm), 1.7);
    }
  }

  const chosen = skyArcs[reflections - 1][nm - 400];
  if (chosen.radius > sunElevation) {
    const atApex = project(chosen.radius, 0);
    dot(ctx, atApex, 8, colour(nm), '#ffffff');
  }
  dot(ctx, centre, 6, gold, '#172537');
  label(ctx, 'Direction opposite the Sun', centre[0], 596, 'center', muted);
  label(ctx, 'Sky above the horizon', 30, 44);
}

let previousSky;

function refresh() {
  const nm = Number(wavelength.value);
  const reflections = Number(order.value);
  const ratio = Number(height.value);
  const solarElevation = Number(sun.value) * radians;
  const index = waterIndex(nm);
  const peak = causticHeight(index, reflections);
  const concentratedAngle = angularRadius(peak, index, reflections);
  const ray = traceRay(ratio, index, reflections);
  const angle = angularRadius(ratio, index, reflections);
  const visibility = concentratedAngle - solarElevation;
  const bounceText = reflections === 1 ? 'one bounce' : 'two bounces';

  element('wavelength-value').textContent = `${nm} nm`;
  element('height-value').textContent = `${(ratio * 100).toFixed(1)}% of radius`;
  element('sun-value').textContent = `${sun.value}°`;
  element('drop-description').textContent = `The arrow follows sunlight bending into water and leaving after ${bounceText}.`;
  element('sky-description').textContent = visibility > 0
    ? `The dot marks this colour at the top of the selected bow, ${degrees(visibility)} above the horizon.`
    : 'The selected colour sits at or below the horizon. Lower the Sun to bring it into view.';

  element('result').textContent = `Your ray leaves ${degrees(angle)} from the point opposite the Sun. This colour gathers at ${degrees(concentratedAngle)}. ${(100 * ray.power).toFixed(2)}% of the incident ray follows this path.`;
  element('drop').setAttribute('aria-label', `A ray at ${(ratio * 100).toFixed(1)} percent of the drop radius bends at entry, makes ${bounceText}, and bends out again.`);
  element('angles').setAttribute('aria-label', `Plot of exit angle against entry position. The ray leaves at ${degrees(angle)} and the curve flattens at ${degrees(concentratedAngle)}.`);
  element('sky').setAttribute('aria-label', `Angular view of both rainbows above a level horizon. The Sun is ${sun.value} degrees high. ${element('sky-description').textContent}`);

  drawDrop(ray, ratio, nm);
  drawAngles(ratio, peak, index, reflections, nm);
  const skyState = [solarElevation, nm, reflections].join(',');
  if (skyState !== previousSky) {
    drawSky(solarElevation, nm, reflections);
    previousSky = skyState;
  }
}

for (const control of [order, wavelength, height, sun]) {
  control.addEventListener('input', refresh);
}
element('aim').addEventListener('click', () => {
  height.value = causticHeight(waterIndex(Number(wavelength.value)), Number(order.value)).toFixed(3);
  refresh();
});
refresh();

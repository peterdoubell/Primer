import { simulate, steadyRate } from './model.mjs';

const get = id => document.getElementById(id);
const format = (value, digits = 2) => Number(value).toLocaleString('en', { maximumFractionDigits: digits });
const ms = time => format(time * 1000, 4) + ' ms';
let seed = 104729, run, selected = 0, worker = null, repeatBatch = 0;

function state() {
  return { rate: get('rate').valueAsNumber, deadTime: get('dead-time').valueAsNumber * 1e-6,
    duration: Number(get('duration').value), seed };
}

function row(cells) {
  const tr = document.createElement('tr');
  cells.forEach((value, index) => {
    const cell = document.createElement(index ? 'td' : 'th');
    if (!index) cell.scope = 'row';
    cell.textContent = value;
    tr.append(cell);
  });
  return tr;
}

function plot(canvas, height) {
  canvas.height = canvas.clientWidth < 600 ? Math.round(height * 1.55) : height;
  const ctx = canvas.getContext('2d'), width = canvas.width;
  const font = Math.max(16, 13 * width / Math.max(250, canvas.clientWidth));
  ctx.clearRect(0, 0, width, canvas.height);
  ctx.fillStyle = '#fffdf7'; ctx.fillRect(0, 0, width, canvas.height);
  ctx.font = font + 'px system-ui'; ctx.fillStyle = '#203237'; ctx.lineWidth = 1.5;
  return { ctx, width, height: canvas.height, font };
}

function line(ctx, points, color, width = 2) {
  ctx.strokeStyle = color; ctx.lineWidth = width; ctx.beginPath();
  points.forEach(([x, y], index) => { if (index) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
  ctx.stroke();
}

function timing() {
  if (!run) return;
  const canvas = get('timeline'), { ctx, width, height, font } = plot(canvas, 300);
  const windowTime = Math.min(Number(get('window').value), run.state.duration);
  get('pan').step = String(Math.min(.01, windowTime / Math.max(windowTime, run.state.duration - windowTime) / 50));
  const start = get('pan').valueAsNumber * Math.max(0, run.state.duration - windowTime), end = start + windowTime;
  const left = Math.max(85, font * 4.8), right = width - 20;
  const top = font * 2.1, incomingY = top + (height - top - font * 3) * .25;
  const outputY = top + (height - top - font * 3) * .75, bottom = height - font * 1.9;
  const x = time => left + (time - start) * (right - left) / windowTime;
  get('pan-value').textContent = ms(start) + ' – ' + ms(end);
  ctx.save(); ctx.beginPath(); ctx.rect(left, top, right - left, bottom - top); ctx.clip();
  for (let index = 0; index < run.times.length; index += 1) {
    const time = run.times[index];
    if (time > end) break;
    if (run.accepted[index] && time + run.state.deadTime > start && run.state.deadTime) {
      ctx.fillStyle = '#ddd8c58c';
      ctx.fillRect(x(time), top, x(Math.min(time + run.state.deadTime, end)) - x(time), bottom - top);
    }
    if (time < start) continue;
    const px = x(time), accepted = run.accepted[index];
    if (index === selected) {
      line(ctx, [[px, top], [px, bottom]], '#b27b2d', 3);
      ctx.fillStyle = '#b27b2d'; ctx.beginPath(); ctx.arc(px, top + 5, 5, 0, 2 * Math.PI); ctx.fill();
    }
    line(ctx, [[px, incomingY], [px, incomingY - font * 1.1]], '#587d83', 1.7);
    if (accepted) line(ctx, [[px, outputY], [px, outputY - font * 1.35]], '#17677c', 3);
    else {
      const y = incomingY - font * 1.35, d = font * .15;
      line(ctx, [[px - d, y - d], [px + d, y + d]], '#aa522b', 2);
      line(ctx, [[px - d, y + d], [px + d, y - d]], '#aa522b', 2);
    }
  }
  ctx.restore();
  line(ctx, [[left, incomingY], [right, incomingY]], '#a0b2b1');
  line(ctx, [[left, outputY], [right, outputY]], '#a0b2b1');
  ctx.fillStyle = '#203237'; ctx.textAlign = 'left';
  ctx.fillText('Input', 8, incomingY); ctx.fillText('Counted', 8, outputY);
  for (let tick = 0; tick <= 4; tick += 1) {
    const time = start + tick * windowTime / 4, px = x(time);
    line(ctx, [[px, bottom], [px, bottom + 6]], '#607c81');
    ctx.textAlign = tick === 0 ? 'left' : tick === 4 ? 'right' : 'center';
    ctx.fillStyle = '#203237'; ctx.fillText(format(time * 1000, 3), px, bottom + font * 1.2);
  }
  ctx.textAlign = 'left'; ctx.fillText('ms after gate opens', left, font);
  const visible = [];
  run.times.forEach((time, index) => { if (time >= start && time < end) visible.push(index); });
  get('timeline-caption').textContent = `Window ${ms(start)} to ${ms(end)} of a ${ms(run.state.duration)} gate. Recovery bands have width ${format(run.state.deadTime * 1e6)} µs. Pulse heights are schematic. Gate seed ${seed}.`;
  get('event-rows').replaceChildren(...visible.slice(0, 80).map(index => row([
    index + 1, ms(run.times[index]), run.accepted[index] ? 'Recorded' : 'Lost during recovery',
  ])));
  get('table-note').textContent = visible.length > 80 ? `Showing the first 80 of ${visible.length} visible interactions. Narrow or move the time window to inspect the rest.` : `${visible.length} interactions in this time window.`;
}

function inspect(recenter = false) {
  const input = get('event');
  input.max = Math.max(0, run.times.length - 1);
  input.value = selected;
  get('event-value').textContent = run.times.length ? `${selected + 1} / ${format(run.times.length, 0)}` : 'No interactions';
  get('event').disabled = !run.times.length;
  get('previous').disabled = !run.times.length || selected === 0;
  get('next').disabled = !run.times.length || selected === run.times.length - 1;
  if (!run.times.length) {
    get('event-description').textContent = 'No interactions arrived in this gate. Count another gate or increase the input rate or gate duration.';
    get('interaction-dot').setAttribute('opacity', '0');
    timing(); return;
  }
  const time = run.times[selected], accepted = run.accepted[selected];
  let previousAccepted = selected;
  while (previousAccepted >= 0 && !run.accepted[previousAccepted]) previousAccepted -= 1;
  const until = run.times[previousAccepted] + run.state.deadTime;
  get('event-description').textContent = accepted
    ? `Interaction ${selected + 1} at ${ms(time)} is recorded. ${run.state.deadTime ? 'Recovery ends at ' + ms(until) + '.' : 'Recovery time is zero; the counter stays ready.'}`
    : `Interaction ${selected + 1} at ${ms(time)} is lost. Interaction ${previousAccepted + 1} already closed the gate until ${ms(until)}. This lost interaction does not extend that interval.`;
  get('interaction-dot').setAttribute('opacity', '1');
  get('interaction-dot').setAttribute('fill', accepted ? '#7fdae0' : '#eda882');
  get('recovery-symbol').setAttribute('stroke', accepted ? '#7fdae0' : '#eda882');
  if (recenter) {
    const windowTime = Math.min(Number(get('window').value), run.state.duration);
    const span = run.state.duration - windowTime;
    get('pan').value = span ? Math.max(0, Math.min(1, (time - windowTime / 2) / span)) : 0;
  }
  timing();
}

function clearComparison() {
  worker?.terminate(); worker = null;
  get('repeat').disabled = false;
  get('histogram-figure').hidden = true;
  get('statistics').replaceChildren(); get('dispersion').textContent = '';
  get('repeat-status').textContent = 'Count fresh gates to compare these settings.';
}

function update() {
  clearComparison();
  run = simulate(state()); selected = 0; get('pan').value = 0;
  get('rate-value').textContent = format(run.state.rate, 0) + ' s⁻¹';
  get('dead-time-value').textContent = format(run.state.deadTime * 1e6, 0) + ' µs';
  for (const [id, value] of [['incoming-count', run.times.length], ['recorded-count', run.count], ['lost-count', run.lost], ['counter-display', run.count]]) get(id).textContent = format(value, 0);
  get('live-time').textContent = ms(run.liveSeconds);
  get('gate-result').textContent = `Recorded rate: ${format(run.recordedRate)} s⁻¹. Count ÷ live time: ${format(run.liveRate)} s⁻¹. The steady output-rate prediction is ${format(steadyRate(run.state.rate, run.state.deadTime))} s⁻¹; a single finite gate fluctuates around its own finite-gate expectation.`;
  document.body.dataset.seed = seed;
  inspect();
}

let statisticsResult = null;
function histogram(simulated, predicted) {
  const { ctx, width, height, font } = plot(get('histogram'), 380);
  const all = [...simulated.counts, ...predicted.distribution.filter(row => row.probability > 1e-6).map(row => row.count)];
  let low = Math.min(...all), high = Math.max(...all);
  if (low === high) { low = Math.max(0, low - 1); high += 1; }
  const binSize = Math.max(1, Math.ceil((high - low + 1) / 45));
  const size = Math.ceil((high - low + 1) / binSize);
  const observed = new Array(size).fill(0), expected = new Array(size).fill(0);
  simulated.counts.forEach(count => { observed[Math.floor((count - low) / binSize)] += 1 / simulated.repetitions; });
  predicted.distribution.forEach(row => {
    const bin = Math.floor((row.count - low) / binSize);
    if (bin >= 0 && bin < size) expected[bin] += row.probability;
  });
  const top = font, bottom = height - font * 3, left = font * 4.5, right = width - 20;
  const maximum = Math.max(...observed, ...expected, .01) * 1.18;
  const x = index => left + (index + .5) / size * (right - left);
  const y = value => bottom - value / maximum * (bottom - top);
  for (let tick = 0; tick <= 3; tick += 1) {
    const value = maximum * tick / 3;
    line(ctx, [[left, y(value)], [right, y(value)]], '#d5dcda', 1);
    ctx.fillStyle = '#455f65'; ctx.textAlign = 'right'; ctx.fillText(format(value * 100, 1) + '%', left - 9, y(value) + font * .35);
  }
  observed.forEach((value, index) => {
    ctx.fillStyle = '#17677c'; const span = (right - left) / size;
    ctx.fillRect(x(index) - span * .4, y(value), span * .8, bottom - y(value));
  });
  line(ctx, expected.map((value, index) => [x(index), y(value)]), '#aa522b', 3);
  const ticks = [...new Set(Array.from({ length: 5 }, (_, tick) => Math.round((size - 1) * tick / 4)))];
  ticks.forEach((index, tick) => {
    const value = low + index * binSize;
    ctx.fillStyle = '#203237'; ctx.textAlign = tick === 0 ? 'left' : tick === ticks.length - 1 ? 'right' : 'center';
    ctx.fillText(format(value, 0), x(index), bottom + font * 1.25);
  });
  ctx.textAlign = 'center'; ctx.fillText('Recorded counts per gate', (left + right) / 2, height - font * .35);
  get('histogram-caption').textContent = `Relative frequency per ${binSize === 1 ? 'integer count' : binSize + '-count bin'}. The orange line sums the same bins of the finite-gate renewal distribution. Each simulated gate lasts ${ms(run.state.duration)}.`;
}

function repeat() {
  worker?.terminate();
  worker = new Worker(new URL('./statistics-worker.js', import.meta.url), { type: 'module' });
  const currentWorker = worker;
  const batchState = { ...run.state, seed: (run.state.seed + Math.imul(repeatBatch++, 0x85ebca6b)) >>> 0 };
  get('repeat-status').dataset.seed = batchState.seed;
  get('repeat').disabled = true; get('repeat-status').textContent = 'Counting 256 fresh gates and calculating the renewal prediction…';
  currentWorker.onmessage = event => {
    if (currentWorker !== worker) return;
    currentWorker.terminate(); worker = null; get('repeat').disabled = false;
    if (event.data.error) { get('repeat-status').textContent = event.data.error; return; }
    const { simulated, predicted } = event.data;
    statisticsResult = { simulated, predicted };
    get('histogram-figure').hidden = false;
    histogram(simulated, predicted);
    get('statistics').replaceChildren(
      row(['Mean count', format(simulated.mean, 3), format(predicted.mean, 3)]),
      row(['Standard deviation', format(simulated.standardDeviation, 3), format(predicted.standardDeviation, 3)]),
      row(['Variance ÷ mean', simulated.mean ? format(simulated.variance / simulated.mean, 4) : '—', predicted.fano === null ? '—' : format(predicted.fano, 4)]),
    );
    get('repeat-status').textContent = '256 fresh simulated gates completed. Orange is the model prediction, not a fit to those counts.';
    get('dispersion').textContent = run.state.rate === 0 ? 'With no incoming interactions, every gate records zero.'
      : run.state.deadTime === 0 ? 'With recovery removed, the count distribution is Poisson: the predicted variance equals its mean. A finite set of simulated gates fluctuates around that prediction.'
      : `Recovery spaces the recorded pulses apart. Here the predicted variance is ${format(predicted.fano, 3)} times the mean, so using the Poisson rule “variance = mean” would describe a different counting process.`;
  };
  currentWorker.onerror = () => {
    if (currentWorker !== worker) return;
    currentWorker.terminate(); worker = null; get('repeat').disabled = false;
    get('repeat-status').textContent = 'The comparison could not be calculated. Count fresh gates to retry.';
  };
  currentWorker.postMessage({ state: batchState });
}

for (const id of ['rate', 'dead-time']) get(id).addEventListener('input', update);
get('duration').addEventListener('change', update);
get('new-run').addEventListener('click', () => { seed = (seed + 1) >>> 0; update(); });
get('ideal').addEventListener('click', () => { get('dead-time').value = 0; update(); });
get('restore').addEventListener('click', () => { get('dead-time').value = 200; update(); });
get('event').addEventListener('input', () => { selected = get('event').valueAsNumber; inspect(true); });
get('previous').addEventListener('click', () => { selected = Math.max(0, selected - 1); inspect(true); });
get('next').addEventListener('click', () => { selected = Math.min(run.times.length - 1, selected + 1); inspect(true); });
get('window').addEventListener('change', timing); get('pan').addEventListener('input', timing);
get('repeat').addEventListener('click', repeat);
new ResizeObserver(() => { timing(); if (statisticsResult && !get('histogram-figure').hidden) histogram(statisticsResult.simulated, statisticsResult.predicted); }).observe(get('timeline'));
update(); repeat();

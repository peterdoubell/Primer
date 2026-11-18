import { archiveTemperature, blackbody, frequencyGHz, readChannels, residual } from './spectrum.mjs';

const get = id => document.getElementById(id);
const temperatureInput = get('temperature');
const channelInput = get('channel');
const spectrumCanvas = get('spectrum');
const residualCanvas = get('residuals');
const channelTable = get('channels');
const modelColour = '#b5faee';
const sourceColour = '#ffcf86';
let channels = [];

function axes(canvas, xMax, yMin, yMax, unit, highlighted) {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const scale = window.devicePixelRatio;
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  const left = 53;
  const right = width - 15;
  const top = 29;
  const bottom = height - 43;
  const x = value => left + (right - left) * value / xMax;
  const y = value => bottom - (bottom - top) * (value - yMin) / (yMax - yMin);
  ctx.fillStyle = '#122132';
  ctx.fillRect(0, 0, width, height);
  ctx.font = '12px system-ui';
  ctx.strokeStyle = '#385468';
  ctx.fillStyle = '#d0e4f1';
  ctx.textAlign = 'right';

  for (let tick = 0; tick <= 4; tick += 1) {
    const value = yMin + tick * (yMax - yMin) / 4;
    ctx.beginPath();
    ctx.moveTo(left, y(value));
    ctx.lineTo(right, y(value));
    ctx.stroke();
    ctx.fillText(Math.round(value).toString(), left - 6, y(value) + 4);
  }
  ctx.textAlign = 'center';
  for (let value = 0; value < xMax; value += width < 400 ? 200 : 100) {
    ctx.fillText(value.toString(), x(value), bottom + 16);
  }
  ctx.fillText('Frequency (GHz)', (left + right) / 2, height - 9);
  ctx.textAlign = 'left';
  ctx.fillText(unit, 6, 14);
  ctx.strokeStyle = '#7597aa';
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(x(highlighted), top);
  ctx.lineTo(x(highlighted), bottom);
  ctx.stroke();
  ctx.setLineDash([]);
  return { ctx, x, y };
}

function paintSpectrum(data, temperature, selected) {
  const yMax = 100 * Math.ceil(Math.max(...data.map(row => Math.max(row.observed, row.model))) / 100);
  const { ctx, x, y } = axes(spectrumCanvas, 675, 0, yMax, 'MJy/sr', selected.frequency);
  ctx.beginPath();
  ctx.moveTo(x(0), y(0));
  for (let frequency = 2.5; frequency <= 675; frequency += 2.5) {
    ctx.lineTo(x(frequency), y(blackbody(frequency, temperature)));
  }
  ctx.strokeStyle = modelColour;
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = sourceColour;
  for (const row of data) {
    ctx.beginPath();
    ctx.arc(x(row.frequency), y(row.observed), row === selected ? 4.8 : 2.5, 0, 2 * Math.PI);
    ctx.fill();
  }
}

function paintResidual(data, selected) {
  const extent = Math.max(500, ...data.map(row => Math.abs(row.residual) + row.sigma));
  const yMax = 250 * Math.ceil(extent / 250);
  const { ctx, x, y } = axes(residualCanvas, 675, -yMax, yMax, 'kJy/sr', selected.frequency);
  ctx.strokeStyle = sourceColour;
  ctx.fillStyle = sourceColour;
  for (const row of data) {
    const frequency = x(row.frequency);
    const high = y(row.residual + row.sigma);
    const low = y(row.residual - row.sigma);
    ctx.beginPath();
    ctx.moveTo(frequency, high);
    ctx.lineTo(frequency, low);
    ctx.moveTo(frequency - 3, high);
    ctx.lineTo(frequency + 3, high);
    ctx.moveTo(frequency - 3, low);
    ctx.lineTo(frequency + 3, low);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(frequency, y(row.residual), row === selected ? 4.5 : 2.2, 0, 2 * Math.PI);
    ctx.fill();
  }
}

function render() {
  if (!channels.length) return;
  const temperature = temperatureInput.valueAsNumber;
  const data = channels.map(channel => ({
    frequency: frequencyGHz(channel[0]),
    observed: channel[1],
    sigma: channel[3],
    model: blackbody(frequencyGHz(channel[0]), temperature),
    residual: residual(channel, temperature),
  }));
  const index = channelInput.valueAsNumber;
  const selected = data[index];
  paintSpectrum(data, temperature, selected);
  paintResidual(data, selected);
  get('temperature-value').textContent = temperature.toFixed(3) + ' K';
  get('channel-value').textContent = selected.frequency.toFixed(2) + ' GHz';
  get('observed').textContent = selected.observed.toFixed(3) + ' MJy/sr';
  get('model').textContent = selected.model.toFixed(3) + ' MJy/sr';
  get('difference').textContent = selected.residual.toFixed(1) + ' kJy/sr';
  get('uncertainty').textContent = selected.sigma + ' kJy/sr';
  for (const [rowIndex, row] of [...channelTable.rows].entries()) {
    row.toggleAttribute('data-selected', rowIndex === index);
  }
}

async function start() {
  try {
    const source = await fetch('firas-monopole.txt.gz');
    if (!source.ok) throw Error('Source file unavailable.');
    const stream = source.body.pipeThrough(new DecompressionStream('gzip'));
    const bytes = await new Response(stream).arrayBuffer();
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
      byte => byte.toString(16).padStart(2, '0')).join('');
    if (digest !== 'df793c3dca09ebfa7dbc5aa0ec1951daa8884431bc30eff28a710d7516cf50fa') {
      throw Error('Source checksum differs.');
    }
    channels = readChannels(new TextDecoder().decode(bytes));
    if (channels.length !== 43) throw Error('Source channel inventory differs.');
    for (const [wavenumber, intensity, difference, uncertainty, galaxy] of channels) {
      const row = channelTable.insertRow();
      for (const value of [frequencyGHz(wavenumber).toFixed(2), intensity.toFixed(3), difference, uncertainty, galaxy]) {
        row.insertCell().textContent = value;
      }
    }
    channelInput.max = channels.length - 1;
    channelInput.value = 7;
    temperatureInput.disabled = channelInput.disabled = get('reset').disabled = false;
    get('status').textContent = '43 published FIRAS channels';
    render();
    const observer = new ResizeObserver(render);
    observer.observe(spectrumCanvas);
    observer.observe(residualCanvas);
  } catch {
    get('status').textContent = 'The published channels could not be verified. Reload the page to try again.';
  }
}
temperatureInput.addEventListener('input', render);
channelInput.addEventListener('input', render);
get('reset').addEventListener('click', () => {
  temperatureInput.value = archiveTemperature;
  render();
});
start();

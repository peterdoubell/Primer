'use strict';

const {side, sites, spin, energy, magnetization, equilibrium} = PrimerIsing;
const element = id => document.getElementById(id);
const slider = element('temperature');
const canvas = element('histogram');
const context = canvas.getContext('2d');
const buttons = [];
let state = 0;
let distribution;

for (let site = 0; site < sites; site++) {
  const button = document.createElement('button');
  button.type = 'button';
  button.setAttribute('aria-label', `Spin at row ${Math.floor(site / side) + 1}, column ${site % side + 1}`);
  button.addEventListener('click', () => {
    state ^= 1 << site;
    showConfiguration();
  });
  element('spins').append(button);
  buttons.push(button);
}

function showConfiguration() {
  buttons.forEach((button, site) => {
    const up = spin(state, site) === 1;
    button.textContent = up ? '↑' : '↓';
    button.setAttribute('aria-pressed', String(up));
  });
  element('configuration-values').textContent = `Energy per spin ${energy(state) / sites} J · Magnetisation per spin ${magnetization(state) / sites}`;
}

function updateDistribution() {
  const temperature = Number(slider.value);
  distribution = equilibrium(temperature);
  element('temperature-value').textContent = temperature.toFixed(2);
  const {histogram, meanEnergy, meanAbsoluteMagnetization} = distribution;
  element('averages').textContent = `Mean energy per spin ${meanEnergy.toFixed(3)} J · Mean magnetisation magnitude ${meanAbsoluteMagnetization.toFixed(3)}`;
  context.clearRect(0, 0, canvas.width, canvas.height);
  const left = 66, top = 26, width = 548, height = 244;
  context.font = '18px system-ui';
  context.fillStyle = '#e4eff5';
  for (const p of [0, 0.125, 0.25, 0.375, 0.5]) {
    const y = top + height * (1 - p * 2);
    context.fillText(String(p), 8, y + 5);
    context.fillStyle = '#374952';
    context.fillRect(left, y, width, 1);
    context.fillStyle = '#e4eff5';
  }
  const band = width / histogram.length;
  const table = document.createDocumentFragment();
  histogram.forEach((probability, index) => {
    const m = (2 * index - sites) / sites;
    context.fillStyle = m < 0 ? '#a2d2f1' : m > 0 ? '#f6ba81' : '#e0e8eb';
    const bar = probability * 2 * height;
    context.fillRect(left + index * band + 2, top + height - bar, band - 4, bar);
    const row = document.createElement('tr');
    for (const value of [m.toFixed(3), probability.toExponential(4)]) {
      const cell = document.createElement('td');cell.textContent = value;row.append(cell);
    }
    table.append(row);
  });
  element('probabilities').replaceChildren(table);
  context.fillStyle = '#e4eff5';
  context.fillText('−1', left + 5, 296);
  context.fillText('0', left + width / 2 - 5, 296);
  context.fillText('+1', left + width - 27, 296);
  context.fillText('Magnetisation per spin', left + width / 2 - 100, 322);
}

slider.addEventListener('input', updateDistribution);
for (const button of document.querySelectorAll('[data-temperature]')) {
  button.addEventListener('click', () => {
    slider.value = button.dataset.temperature;
    updateDistribution();
  });
}
element('sample').addEventListener('click', () => {
  state = distribution.sample(Math.random());
  showConfiguration();
});
showConfiguration();
updateDistribution();

'use strict';

(() => {
  const side = 4;
  const sites = side * side;
  const states = 1 << sites;
  const energies = new Int8Array(states);
  const magnetizations = new Int8Array(states);
  const spin = (state, site) => state & (1 << site) ? 1 : -1;
  const neighbors = Array.from({length: sites}, (_, site) => {
    const x = site % side, y = Math.floor(site / side);
    return [y * side + (x + 1) % side, ((y + 1) % side) * side + x];
  });
  for (let state = 0; state < states; state++) {
    for (let site = 0; site < sites; site++) {
      const value = spin(state, site);
      magnetizations[state] += value;
      for (const neighbor of neighbors[site]) energies[state] -= value * spin(state, neighbor);
    }
  }

  function equilibrium(temperature) {
    if (!Number.isFinite(temperature) || temperature < 0.5 || temperature > 8) {
      throw new RangeError('Temperature must be between 0.5 and 8');
    }
    const weights = new Float64Array(states);
    const histogram = new Float64Array(sites + 1);
    let total = 0, energy = 0, absoluteMagnetization = 0;
    for (let state = 0; state < states; state++) {
      // Shift the energy by its minimum so every exponential is at most one.
      const weight = Math.exp(-(energies[state] + 2 * sites) / temperature);
      total += weight;
      weights[state] = total;
      histogram[(magnetizations[state] + sites) / 2] += weight;
      energy += energies[state] * weight;
      absoluteMagnetization += Math.abs(magnetizations[state]) * weight;
    }
    function sample(draw) {
      if (!Number.isFinite(draw) || draw < 0 || draw >= 1) throw new RangeError('Draw must be in [0, 1)');
      const target = draw * total;
      let left = 0, right = states - 1;
      while (left < right) {
        const middle = Math.floor((left + right) / 2);
        if (weights[middle] > target) right = middle;
        else left = middle + 1;
      }
      return left;
    }
    return {histogram: histogram.map(value => value / total), meanEnergy: energy / total / sites,
      meanAbsoluteMagnetization: absoluteMagnetization / total / sites, sample};
  }
  const api = {side, sites, states, spin, energy: state => energies[state], magnetization: state => magnetizations[state], equilibrium};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else globalThis.PrimerIsing = api;
})();

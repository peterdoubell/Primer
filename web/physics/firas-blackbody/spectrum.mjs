export const archiveTemperature = 2.725;
const planck = 6.62607015e-34;
const boltzmann = 1.380649e-23;
const lightSpeed = 299792458;

export function frequencyGHz(wavenumberCm) {
  return wavenumberCm * 100 * lightSpeed / 1e9;
}

export function blackbody(frequency, temperature) {
  if (frequency === 0) return 0;
  const hz = frequency * 1e9;
  return (2 * planck * hz ** 3 / lightSpeed ** 2)
    / Math.expm1(planck * hz / (boltzmann * temperature)) / 1e-20;
}

export function residual(channel, temperature) {
  const frequency = frequencyGHz(channel[0]);
  return channel[2] + 1000 * (blackbody(frequency, archiveTemperature) - blackbody(frequency, temperature));
}

export function readChannels(text) {
  return text.split('\n').map(line => line.trim())
    .filter(line => line && !line.startsWith('#'))
    .map(line => {
      const row = line.split(/\s+/).map(Number);
      if (row.length !== 5 || !row.every(Number.isFinite) || row[0] <= 0 || row[3] <= 0) {
        throw Error('Unexpected FIRAS channel.');
      }
      return row;
    });
}

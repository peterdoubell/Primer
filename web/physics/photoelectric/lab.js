'use strict';
const Model = {
  HC: 1239.841984,                        // h c in eV·nm
  // Approximate work functions in eV; measured values depend on the surface.
  METALS: {caesium: 2.1, potassium: 2.3, sodium: 2.28, zinc: 4.3, copper: 4.7},
  photonEnergy: wavelength => Model.HC / wavelength,
  frequency: wavelength => 299792458 / (wavelength * 1e-9),
  threshold: work => Model.HC / work,
  // Maximum kinetic energy of an ejected electron in eV; 0 when no electrons leave.
  kinetic: (wavelength, work) => Math.max(0, Model.photonEnergy(wavelength) - work),
  emits: (wavelength, work) => Model.photonEnergy(wavelength) > work,
};
function start() {
  const canvas = Kit.get('graph');
  function draw() {
    const wavelength = Kit.num('wavelength'), metal = Kit.get('metal').value, work = Model.METALS[metal], intensity = Kit.num('intensity');
    Kit.say('wavelength', wavelength, wavelength + ' nm'); Kit.say('intensity', intensity, intensity + '%');
    const energy = Model.photonEnergy(wavelength), ke = Model.kinetic(wavelength, work), emits = Model.emits(wavelength, work);
    const p = Kit.plot(canvas, {x: [0, 13], y: [0, 9], xlabel: 'photon energy (eV)', ylabel: 'max electron energy (eV)'});
    p.line(0, 0, work, 0, '#963d18', 4); p.line(work, 0, 13, 13 - work, '#963d18', 4);
    p.line(energy, 0, energy, ke, '#215783', 2, [5, 4]); p.point(energy, ke, '#215783'); p.text(Kit.fmt(ke, 3) + ' eV', energy, ke);
    p.text('threshold ' + Kit.fmt(work) + ' eV', work, 0, '#963d18', -40, -12);
    Kit.rows(Kit.get('rows'), [['Photon energy hc/λ', Kit.fmt(energy) + ' eV'], ['Work function of ' + metal + ' (approximate)', Kit.fmt(work) + ' eV'],
      ['Longest wavelength that ejects electrons', Kit.fmt(Model.threshold(work)) + ' nm'], ['Maximum electron energy', emits ? Kit.fmt(ke) + ' eV' : 'no electrons'],
      ['Stopping voltage', emits ? Kit.fmt(ke) + ' V' : '—'], ['Electrons per second (relative)', emits ? intensity + '%' : '0']]);
    Kit.get('result').textContent = emits
      ? 'Electrons are ejected. Each photon gives its whole energy to one electron: ' + Kit.fmt(work) + ' eV frees it and ' + Kit.fmt(ke, 3) + ' eV is left as motion. Brighter light ejects more electrons but does not make them faster.'
      : 'No electrons are ejected. Each photon carries ' + Kit.fmt(energy, 3) + ' eV, less than the ' + Kit.fmt(work) + ' eV needed, and making the light brighter does not help.';
    canvas.setAttribute('aria-label', 'Maximum electron energy against photon energy for ' + metal + '. ' + Kit.get('result').textContent);
  }
  Kit.bind(['wavelength', 'metal', 'intensity'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

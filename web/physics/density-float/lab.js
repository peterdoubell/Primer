'use strict';
const Model = {
  // Densities in g/cm³ at room temperature (typical values).
  SOLIDS: {cork: 0.24, pine: 0.5, ice: 0.92, 'plastic (HDPE)': 0.95, 'rubber': 1.2, glass: 2.5, aluminium: 2.7, iron: 7.87, gold: 19.3},
  LIQUIDS: {'cooking oil': 0.92, 'fresh water': 1.0, 'sea water': 1.025, honey: 1.42, mercury: 13.5},
  // Fraction of a floating object's volume below the surface; 1 when it sinks.
  submerged: (solid, liquid) => Math.min(1, solid / liquid),
  floats: (solid, liquid) => solid < liquid,
};
function start() {
  const canvas = Kit.get('graph'), ctx = canvas.getContext('2d');
  function draw() {
    const solid = Kit.get('solid').value, liquid = Kit.get('liquid').value, ds = Model.SOLIDS[solid], dl = Model.LIQUIDS[liquid];
    const frac = Model.submerged(ds, dl), floats = Model.floats(ds, dl), size = 110, surface = 130, bottom = 340;
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#cfe3f1'; ctx.fillRect(160, surface, 400, bottom - surface); ctx.strokeStyle = '#172533'; ctx.lineWidth = 3; ctx.strokeRect(160, 60, 400, bottom - 60);
    const top = floats ? surface - size * (1 - frac) : bottom - size;
    ctx.fillStyle = '#c9a26b'; ctx.fillRect(305, top, size, size); ctx.strokeRect(305, top, size, size);
    ctx.fillStyle = '#172533'; ctx.font = '16px system-ui, sans-serif'; ctx.fillText(solid, 315, top + size / 2 + 5); ctx.fillText(liquid, 172, bottom - 12);
    Kit.rows(Kit.get('rows'), [['Density of ' + solid, ds + ' g/cm³'], ['Density of ' + liquid, dl + ' g/cm³'], ['Result', floats ? 'floats' : 'sinks'],
      ['Part of the block below the surface', floats ? Kit.fmt(frac * 100, 3) + '%' : '100%'], ['A 1000 cm³ block weighs', Kit.fmt(ds, 4) + ' kg; it pushes aside up to ' + Kit.fmt(dl, 4) + ' kg of liquid']]);
    Kit.get('result').textContent = floats
      ? 'The ' + solid + ' floats because it is less dense than ' + liquid + '. It sinks in until the liquid it pushes aside weighs as much as the whole block: ' + Kit.fmt(frac * 100, 3) + '% under the surface.'
      : 'The ' + solid + ' sinks because it is denser than ' + liquid + '. Even fully under, the liquid it pushes aside weighs less than the block. Size and shape of a solid block do not change this; density does.';
    canvas.setAttribute('aria-label', 'A block of ' + solid + ' in a tank of ' + liquid + '. It ' + (floats ? 'floats' : 'sinks') + '.');
  }
  Kit.bind(['solid', 'liquid'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();

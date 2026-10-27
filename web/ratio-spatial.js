(function (host) {
  'use strict';
  const initial = { mode: 'mixture', a: 2, b: 3, batches: 3, factor: 0.5, gap: 0.1 };
  const controls = [
    { key: 'mode', label: '3D investigation', options: [{ value: 'mixture', label: 'Equal recipe batches' }, { value: 'similarity', label: 'Similar shapes and linear scale' }] },
    { key: 'a', label: 'Parts A per batch', min: 0, max: 8, step: 1 },
    { key: 'b', label: 'Parts B per batch', min: 0, max: 8, step: 1 },
    { key: 'batches', label: 'Number of batches', min: 0, max: 4, step: 1 },
    { key: 'factor', label: 'Linear scale factor', min: 0.25, max: 2, step: 0.25 },
    { key: 'gap', label: 'Inspection gap between ingredients', min: 0, max: 0.3, step: 0.1 },
  ];
  for (const control of controls) if (control.key !== 'mode') control.visibleWhen = { mode: [control.key === 'factor' ? 'similarity' : 'mixture'] };
  function normalize(raw) {
    const state = { mode: raw.mode === 'similarity' ? 'similarity' : 'mixture' };
    for (const control of controls.filter(c => !c.options)) {
      const value = raw[control.key], n = (typeof value === 'number' || typeof value === 'string' && value.trim()) ? Number(value) : NaN;
      const accepted = Number.isFinite(n) ? n : initial[control.key];
      state[control.key] = Number((control.min + Math.round((Math.max(control.min, Math.min(control.max, accepted)) - control.min) / control.step) * control.step).toFixed(8));
    }
    return state;
  }
  function outline(g, center, dimensions) {
    const corners = [[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(v => v.map((x, i) => center[i] + x * dimensions[i] / 2));
    for (const [a, b] of [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]) g.line([corners[a], corners[b]], '#83949a', { ratio_reference: true });
  }
  function build(s, g) {
    const boxes = [], unit = [0.2, 0.5, 0.5], unitVolume = 0.05;
    if (s.mode === 'mixture') {
      outline(g, [-1.5, 0, -1.8], unit); g.label([-1.5, 0.6, -1.8], 'Fixed volume: one part');
      for (let i = 0; i < s.batches; i++) {
        for (const [key, start, color] of [['a', -1.6, g.colors.blue], ['b', -1.6 + s.a * 0.2 + s.gap, g.colors.coral]]) {
          if (!s[key]) continue;
          const dimensions = [s[key] * unit[0], unit[1], unit[2]], center = [start + dimensions[0] / 2, 0, -0.8 + i * 0.8];
          g.box(center, dimensions, color, { ratio_ingredient: key, ratio_batch: i, ratio_parts: s[key] });
          boxes.push({ ingredient: key, batch: i, parts: s[key], center, dimensions, representedVolume: s[key] });
        }
        g.label([-2, 0.05, -0.8 + i * 0.8], 'Batch ' + (i + 1));
      }
      const A = s.a * s.batches, B = s.b * s.batches, defined = s.a + s.b > 0;
      return {
        readout: 'Each batch has ' + s.a + ' parts A and ' + s.b + ' parts B. ' + s.batches + ' batches contain A = ' + A + ', B = ' + B + ', total = ' + (A + B) + ' volume parts. ' + (!defined ? '0 : 0 does not define a ratio.' : !s.batches ? 'Zero batches contain zero of both ingredients; their 0 : 0 totals do not define a new ratio.' : 'Every batch and the positive combined batch count preserve A : B = ' + s.a + ' : ' + s.b + '.'),
        note: 'The fixed gray outline is one volume part, with dimensions 0.2 × 0.5 × 0.5 in world coordinates. Each ingredient bar has the same width-to-amount scale and the same cross-section, so its volume is exactly its stated number of parts times 0.05 world-volume units. Camera changes and inspection gaps do not change amounts. Separate rows identify batches; empty batches and absent ingredients add no material. Colors identify A and B, rather than predicting the color of a physical mixture. This companion has its own controls, independent of the workbench.',
        legend: [{ label: 'A volume parts', color: g.colors.blue }, { label: 'B volume parts', color: g.colors.coral }, { label: 'Gray outline: one part', color: '#83949a' }],
        ratioGeometry: { mode: s.mode, boxes, unitDimensions: unit, worldVolumePerPart: unitVolume, totalA: A, totalB: B, total: A + B, ratioDefined: defined, combinedRatioDefined: defined && s.batches > 0 },
      };
    }
    const original = [1.2, 0.5, 0.8], scaled = original.map(x => x * s.factor);
    for (const [kind, center, dimensions, color] of [['original', [-2,0,0], original, g.colors.blue], ['scaled', [2,0,0], scaled, g.colors.coral]]) {
      g.box(center, dimensions, color, { ratio_shape: kind }); boxes.push({ kind, center, dimensions });
      g.label([center[0], dimensions[1] / 2 + 0.5, 0], kind === 'original' ? 'Original lengths: 1.2, 0.5, 0.8' : 'Scaled lengths: ' + scaled.map(x => Number(x.toFixed(6))).join(', '));
    }
    const volume = original.reduce((a, b) => a * b, 1), lengthFactor = s.factor, areaFactor = s.factor ** 2, volumeFactor = s.factor ** 3;
    return {
      readout: 'Every linear dimension is multiplied by ' + lengthFactor + '. Corresponding face areas multiply by ' + areaFactor + ', and volume multiplies by ' + volumeFactor + '. Original volume = ' + Number(volume.toFixed(8)) + '; scaled volume = ' + Number((volume * volumeFactor).toFixed(8)) + ' in the same world-volume units.',
      note: 'These two rectangular prisms share the same world-coordinate scale. The scale factor changes all three lengths, so it changes surface areas by its square and volume by its cube. Translating the shapes apart aids inspection and is not part of the scale transformation. Use the exact dimension readout when perspective hides an edge. The recipe controls and inspection gap are inactive in this investigation; the workbench provides arbitrary model denominators and metre-to-centimetre conversion.',
      legend: [{ label: 'Original shape', color: g.colors.blue }, { label: 'Similar scaled shape', color: g.colors.coral }],
      ratioGeometry: { mode: s.mode, boxes, lengthFactor, areaFactor, volumeFactor, originalVolume: volume, scaledVolume: volume * volumeFactor },
    };
  }
  const family = Object.freeze({ title: 'Ratio volumes and similar shapes', initial, controls, normalize, build, camera: { yaw: -28, pitch: 21 } });
  if (host) host.PrimerRatioSpatialFamily = family;
  if (typeof module !== 'undefined' && module.exports) module.exports = family;
})(typeof window === 'undefined' ? null : window);

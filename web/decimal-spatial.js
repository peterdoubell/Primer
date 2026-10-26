/* One world-space unit cube defines every decimal place in this companion. */
(function (host) {
  'use strict';
  const initial = { whole: 1, tenths: 2, hundredths: 0, thousandths: 0, separation: 0.02 };
  const controls = [
    { key: 'whole', label: 'Whole units', min: 0, max: 3, step: 1 },
    { key: 'tenths', label: 'Tenths', min: 0, max: 10, step: 1 },
    { key: 'hundredths', label: 'Hundredths', min: 0, max: 10, step: 1 },
    { key: 'thousandths', label: 'Thousandths', min: 0, max: 10, step: 1 },
    { key: 'separation', label: 'Inspection gap', min: 0, max: 0.04, step: 0.02, unit: ' unit edges' },
  ];
  function normalize(raw) {
    const state = {};
    for (const c of controls) {
      const value = raw[c.key], number = (typeof value === 'number' || typeof value === 'string' && value.trim()) ? Number(value) : NaN;
      const accepted = Number.isFinite(number) ? number : initial[c.key];
      state[c.key] = Number((c.min + Math.round((Math.max(c.min, Math.min(c.max, accepted)) - c.min) / c.step) * c.step).toFixed(8));
    }
    return state;
  }
  function wireCube(g, center) {
    const corners = [[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(v => v.map((x, i) => center[i] + x / 2));
    for (const [a, b] of [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]) g.line([corners[a], corners[b]], '#83949a', { width: 1, decimal_reference: true });
  }
  function build(s, g) {
    wireCube(g, [-1.4, 0, -0.8]);
    const groups = [
      { key: 'whole', power: 0, size: [1,1,1], color: g.colors.blue, center: i => [-1.3 + i * (1 + s.separation), 0, 1.5] },
      { key: 'tenths', power: -1, size: [1,0.1,1], color: g.colors.teal, center: i => [0.1, -0.45 + i * (0.1 + s.separation), -0.8] },
      { key: 'hundredths', power: -2, size: [0.1,0.1,1], color: g.colors.gold, center: i => [1.3 + i * (0.1 + s.separation), -0.45, -0.8] },
      { key: 'thousandths', power: -3, size: [0.1,0.1,0.1], color: g.colors.coral, center: i => [2.9, -0.45, -1.25 + i * (0.1 + s.separation)] },
    ];
    for (const group of groups) for (let i = 0; i < s[group.key]; i++) g.box(group.center(i), group.size, group.color, { decimal_place: group.power, decimal_piece: i });
    g.label([-1.4,0.8,-0.8], 'Fixed whole: volume 1');
    if(s.tenths)g.label([0.1,0.95,-0.8], s.tenths + (s.tenths===1?' tenth':' tenths'));
    if(s.hundredths)g.label([1.85,0.55,-0.8], s.hundredths + (s.hundredths===1?' hundredth':' hundredths'));
    if(s.thousandths)g.label([2.3,0.05,-0.8], s.thousandths + (s.thousandths===1?' thousandth':' thousandths'));
    if(s.whole)g.label([-0.1,0.8,1.5], s.whole + (s.whole===1?' whole unit':' whole units'));
    const milliunits = 1000 * s.whole + 100 * s.tenths + 10 * s.hundredths + s.thousandths;
    const decimal = Math.floor(milliunits / 1000) + '.' + String(milliunits % 1000).padStart(3, '0');
    return {
      readout: s.whole + ' × 1 + ' + s.tenths + ' × 0.1 + ' + s.hundredths + ' × 0.01 + ' + s.thousandths + ' × 0.001 = ' + decimal + ' fixed-whole units. Ten thousandths regroup as one hundredth; ten hundredths as one tenth; ten tenths as one whole.',
      note: 'Every colored block has its stated physical volume relative to the same unit cube: whole 1 × 1 × 1, tenth 1 × 0.1 × 1, hundredth 0.1 × 0.1 × 1, thousandth 0.1 × 0.1 × 0.1. Gray edges mark the fixed reference cube, not another amount to add. Gaps and the separated place columns aid inspection and do not change any block’s dimensions or the represented amount. Counts of ten demonstrate regrouping. This independently controlled three-decimal-place companion illustrates place values; it does not copy another activity’s arithmetic state or infer a measurement’s uncertainty.',
      legend: groups.map(group => ({ label: group.key, color: group.color })).concat([{ label: 'Gray edges: fixed reference whole', color: '#83949a' }]),
      baseTen: { milliunits, decimal, referenceCenter: [-1.4,0,-0.8], groups: groups.map(group => ({ power: group.power, count: s[group.key], dimensions: group.size })) },
    };
  }
  const family = Object.freeze({ title: 'Base-ten volumes', initial, controls, normalize, build, camera: { yaw: -28, pitch: 21 } });
  if (host) host.PrimerDecimalSpatialFamily = family;
  if (typeof module !== 'undefined' && module.exports) module.exports = family;
})(typeof window === 'undefined' ? null : window);

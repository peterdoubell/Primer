/* The same planar construction feeds the flat chart and rotatable chart. */
(function (host) {
  'use strict';
  const core = () => host ? host.PrimerCoordinatePlaneCore : require('./coordinate-plane-core.js');
  const arithmetic = () => host ? host.PrimerAlgebraFunctionsCore : require('./algebra-functions-core.js');
  function scene(raw) {
    const model = core().model(raw), a = arithmetic(), number = a.number;
    const points = model.graph.points.map(p => ({ ...p, x: number(p.x), y: number(p.y), xText: a.text(p.x), yText: a.text(p.y) }));
    const max = Math.max(.5, ...points.flatMap(p => [Math.abs(p.x), Math.abs(p.y)]));
    const power = 10 ** Math.floor(Math.log10(max / 4));
    const step = [1, 2, 5, 10].map(n => n * power).find(n => n >= max / 4);
    const extent = Number((Math.ceil(max / step + 0.5) * step).toPrecision(12)), gain = 3 / extent;
    const ticks = [];
    for (let i = -Math.floor(extent / step + 1e-12); i <= Math.floor(extent / step + 1e-12); i++) ticks.push(Number((i * step).toPrecision(12)));
    const segments = model.graph.segments.map(s => ({ ...s, from: s.from.map(number), to: s.to.map(number) }));
    const markers = [];
    for (const p of points) {
      let group = markers.find(g => g.x === p.x && g.y === p.y);
      if (!group) { group = { x: p.x, y: p.y, ids: [], labels: [] }; markers.push(group); }
      group.ids.push(p.id); group.labels.push(p.label);
    }
    return { model, points, segments, markers, extent, step, ticks, gain,
      note: 'All geometry lies in the x–y plane at z = 0. Both axes have equal units. The chart fits all named points and the origin; its unit spacing may change when inputs change. Fractions in the table are exact; drawing positions use floating-point approximations. Marker sizes identify points and do not represent a measured length. Coincident points share a marker and retain every name. Rotating the chart changes its apparent angles, not its coordinates or distances.' };
  }
  function build(raw, g) {
    const s = scene(raw), world = p => [p[0] * s.gain, p[1] * s.gain, 0], e = s.extent;
    for (const t of s.ticks) {
      g.line([world([t, -e]), world([t, e])], t === 0 ? g.colors.ink : '#cbd7d2', { coordinate_kind: 'grid-x', value: t, width: t === 0 ? 1.5 : 0.5 });
      g.line([world([-e, t]), world([e, t])], t === 0 ? g.colors.ink : '#cbd7d2', { coordinate_kind: 'grid-y', value: t, width: t === 0 ? 1.5 : 0.5 });
    }
    g.label(world([e, 0]), 'x: +' + e); g.label(world([0, e]), 'y: +' + e);
    for (const line of s.segments) g.line([world(line.from), world(line.to)], line.id === 'straight-distance' ? g.colors.coral : g.colors.teal, { coordinate_kind: 'construction', segmentId: line.id, width: 2 });
    if (s.model.state.mode === 'reflect') {
      const kind = s.model.state.reflection;
      if (kind !== 'origin') g.line((kind === 'x-axis' ? [[-e, 0], [e, 0]] : kind === 'y-axis' ? [[0, -e], [0, e]] : [[-e, -e], [e, e]]).map(world), g.colors.plum, { coordinate_kind: 'reflection-line', width: 2 });
    }
    for (const p of s.markers) {
      const position = world([p.x, p.y]);
      g.sphere(position, .045, g.colors.gold, { coordinate_kind: 'marker', pointIds: p.ids });
      g.label([position[0], position[1] + .15, 0], p.ids.join('/'));
    }
    return { readout: s.model.readout, note: s.model.note + ' ' + s.note + ' Grid spacing = ' + s.step + ' coordinate units; one coordinate unit = ' + s.gain + ' world units.',
      legend: [{ label: 'Coordinate construction', color: g.colors.teal }, { label: 'Straight-line distance', color: g.colors.coral }], coordinatePlaneGeometry: s };
  }
  const family = { title: 'A coordinate plane in space', requires: 'PrimerCoordinatePlaneCore', linkedStateKey: 'math.2.coordinates', camera: { yaw: -15, pitch: 12 },
    initialFactory: () => core().defaults(), controls: [], controlsFactory: () => [], normalize: raw => core().accept(raw), build };
  const api = Object.freeze({ scene, build, family });
  if (host) host.PrimerCoordinatePlaneSpatial = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? null : window);
